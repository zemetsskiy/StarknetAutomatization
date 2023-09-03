import asyncio
from random import randint, uniform
from typing import Optional

import requests
from starknet_py.net.client_models import Call
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.models.chains import StarknetChainId
from starknet_py.contract import Contract
from starknet_py.net.signer.stark_curve_signer import KeyPair

from config.logger import logger
from config.settings import RPC, RANDOM_INCREASE_FEE
from utils.Models import ContractInfo, TokenAmount


class Client:
    def __init__(self, private_key, address):
        self.private_key = private_key
        self.address = address

        self.account = Account(
            client=FullNodeClient(RPC),
            address=address,
            key_pair=KeyPair.from_private_key(
                eval(self.private_key)
            ),
            chain=StarknetChainId.MAINNET,
        )

    async def get_balance(self, token_address=0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7,
                          decimals=18):
        balance = await self.account.get_balance(token_address=token_address)
        return TokenAmount(amount=balance, wei=True, decimals=decimals)

    @staticmethod
    async def EstimateFee(tx):
        response = await tx.estimate_fee()
        overall_fee = response.overall_fee
        gas_price = response.gas_price / 10 ** 9

        # TODO LOW GAS WAITING LOGIC

        return overall_fee

    async def approve(self, token_address, spender, amount_to_approve):
        info = ContractInfo.GetData(token_address)
        abi = info.get('abi')
        token_name = info.get('name')

        logger.debug(f"[{self.account.address}]: Approving {token_name}...")

        contract = Contract(address=token_address, abi=abi, provider=self.account)
        prepared_tx = contract.functions['approve'].prepare(spender=spender, amount=amount_to_approve)

        fee = await Client.EstimateFee(prepared_tx)

        tx = await prepared_tx.invoke(max_fee=int(fee * (1 + randint(RANDOM_INCREASE_FEE[0], RANDOM_INCREASE_FEE[1]) / 100)))

        for _ in range(100):
            try:
                receipt = await self.account.client.get_transaction_receipt(tx.hash)
                block = receipt.block_number
                if block:
                    return True
            except:
                pass
            finally:
                await asyncio.sleep(3)

    async def get_allowance(self, token_address, spender) -> Optional[TokenAmount]:
        data = ContractInfo.GetData(token_address)
        abi = data.get('abi')
        decimals = data.get('decimals')
        contract = Contract(address=token_address, abi=abi,
                            provider=self.account)
        allowance_check = await contract.functions['allowance'].prepare(owner=self.address,
                                                                        spender=spender).call()
        if token_address == 0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3:
            amount = allowance_check.res
        else:
            amount = allowance_check.remaining
        return TokenAmount(amount=amount, decimals=decimals, wei=True)

    async def call(self, interacted_contract_address, calldata, selector_name):
        try:
            logger.debug(f"[{self.address}] Sending tx...")
            call = Call(to_addr=interacted_contract_address, selector=get_selector_from_name(selector_name),
                        calldata=calldata)
            max_fee = TokenAmount(amount=float(uniform(0.0007534534534, 0.001)))
            resp = await self.account.execute(calls=[call], max_fee=int(
                max_fee.Wei * (1 + randint(RANDOM_INCREASE_FEE[0], RANDOM_INCREASE_FEE[1]) / 100)))
            for _ in range(100):
                try:
                    receipt = await self.account.client.get_transaction_receipt(resp.transaction_hash)
                    block = receipt.block_number
                    if block:
                        return True
                except:
                    pass
                finally:
                    await asyncio.sleep(3)
        except Exception as exc:
            logger.error(f"Couldn't send tx: {exc}")

    async def approve_interface(self, token_address, spender, decimals, amount: Optional[TokenAmount] = None):
        name = ContractInfo.GetData(token_address).get('name')
        balance = await self.get_balance(token_address=token_address, decimals=decimals)
        if balance.Wei <= 0:
            logger.error(f"[{self.address}] Zero balance for {name}")
            return False

        if not amount or amount.Wei > balance.Wei:
            amount = balance
        approved_amount = await self.get_allowance(token_address=token_address, spender=spender)

        if approved_amount.Wei >= amount.Wei:
            logger.info(f"[{self.address}] Already approved {approved_amount.Ether} {name}")
            return True

        approved_tx = await self.approve(token_address=token_address, amount_to_approve=amount.Wei, spender=spender)

        if approved_tx:
            logger.info(f"[{self.address}] Approved {amount.Ether} {name}")
            #random_sleep = randint(180, 250)
            random_sleep = randint(10, 20)
            logger.info(f"[{self.address}] Sleeping for {random_sleep} sec before sending tx...")
            await asyncio.sleep(random_sleep)
            return True
        return False

    async def send_transaction(self, interacted_contract, function_name=None, **kwargs) -> bool:
        try:
            logger.info(f"[{self.address}] Sending tx...")

            prepared_tx = interacted_contract.functions[function_name].prepare(**kwargs)
            fee = await self.EstimateFee(prepared_tx)
            tx = await prepared_tx.invoke(
                max_fee=int(fee * (1 + randint(RANDOM_INCREASE_FEE[0], RANDOM_INCREASE_FEE[1]) / 100)))
            for _ in range(100):
                try:
                    receipt = await self.account.client.get_transaction_receipt(tx.hash)
                    block = receipt.block_number
                    if block:
                        return True
                except Exception:
                    pass
                finally:
                    await asyncio.sleep(3)
        except Exception as err:
            logger.error(f"Error while sending tx: {err}")

    @staticmethod
    def get_eth_price():
        logger.info(f'Getting ETH price')
        response = requests.get(f'https://api.binance.com/api/v3/depth?limit=1&symbol=ETHUSDT')
        if response.status_code != 200:
            logger.warning(f'code: {response.status_code} | json: {response.json()}')
            return
        result_dict = response.json()
        if 'asks' not in result_dict:
            logger.warning(f'code: {response.status_code} | json: {response.json()}')
            return
        return float(result_dict['asks'][0][0])
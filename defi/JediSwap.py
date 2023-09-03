import asyncio
import random
from time import time

from utils.Client import Client
from utils.GetData import GetDataForSwap, GetDataForLP
from utils.Models import TokenAmount, ContractInfo
from config.logger import logger
from config.settings import SLIPPAGE, DELAY_BETWEEN_ACTIONS
from starknet_py.contract import Contract


class JediSwap:

    ETH_ADDRESS = ContractInfo.ETH.get('address')
    ETH_ABI = ContractInfo.ETH.get('abi')

    USDT_ADDRESS = ContractInfo.USDT.get('address')
    USDT_ABI = ContractInfo.USDT.get('abi')

    USDC_ADDRESS = ContractInfo.USDC.get('address')
    USDC_ABI = ContractInfo.USDC.get('abi')

    DAI_ADDRESS = ContractInfo.DAI.get('address')
    DAI_ABI = ContractInfo.DAI.get('abi')

    JEDISWAP_CONTRACT = ContractInfo.JEDISWAP.get('address')
    JEDISWAP_ABI = ContractInfo.JEDISWAP.get('abi')

    JEDISWAP_ETHUSDC_CONTRACT = ContractInfo.JEDISWAP_ETHUSDC.get('address')
    JEDISWAP_ETHUSDC_CONTRACT_ABI = ContractInfo.JEDISWAP_ETHUSDC.get('abi')

    JEDISWAP_ETHUSDT_CONTRACT = ContractInfo.JEDISWAP_ETHUSDT.get('address')
    JEDISWAP_ETHUSDT_CONTRACT_ABI = ContractInfo.JEDISWAP_ETHUSDT.get('abi')

    def __init__(self, client: Client):
        self.client = client
        self.contract = Contract(address=JediSwap.JEDISWAP_CONTRACT, abi=JediSwap.JEDISWAP_ABI, provider=self.client.account)

    async def swap(self, swap_to_eth=False):
        try:
            global min_amount
            min_amount = 0

            data_for_swap = await GetDataForSwap(client=self.client, swap_to_eth=swap_to_eth)
            if data_for_swap == {}:
                return False
            amount, to_token_address, to_token_name, from_token_address, from_token_name, from_token_decimals = data_for_swap.values()


            logger.info(f"[{self.client.address}] Swapping {amount.Ether} {from_token_name} to {to_token_name}...[JediSwap]")
            is_approved = await self.client.approve_interface(token_address=from_token_address,
                                                              spender=JediSwap.JEDISWAP_CONTRACT,
                                                              decimals=from_token_decimals, amount=amount)
            if is_approved:
                eth_price = Client.get_eth_price()
                if to_token_name == 'USDT' or to_token_name == 'USDC':
                    if from_token_name == 'ETH':
                        min_to_amount = TokenAmount(amount=eth_price * float(amount.Ether) * (1 - SLIPPAGE / 100),
                                                    decimals=6)
                        print(min_to_amount)
                        min_amount = min_to_amount
                        print(min_amount)
                    elif from_token_name == 'DAI':
                        min_to_amount = TokenAmount(amount=float(amount.Ether) * (1 - SLIPPAGE / 100),
                                                    decimals=6)
                elif to_token_name == 'ETH':
                    min_to_amount = TokenAmount(amount=float(amount.Ether) / eth_price * (1 - SLIPPAGE / 100),
                                                decimals=18)
                elif to_token_name == 'DAI':
                    if from_token_name == 'USDT' or from_token_name == 'USDC':
                        min_to_amount = TokenAmount(amount=float(amount.Ether) * (1 - SLIPPAGE / 100), decimals=18)
                    elif from_token_name == 'ETH':
                        min_to_amount = TokenAmount(amount=eth_price * float(amount.Ether) * (1 - SLIPPAGE / 100),
                                                    decimals=18)
                print(min_amount)
                tx_hash = await self.client.send_transaction(interacted_contract=self.contract,
                                                             function_name='swap_exact_tokens_for_tokens',
                                                             amountIn=amount.Wei,
                                                             amountOutMin=min_amount.Wei,
                                                             path=[from_token_address,
                                                                   to_token_address],
                                                             to=self.client.address,
                                                             deadline=int(time() + 3600))
                if tx_hash:
                    logger.info(
                        f"[{self.client.address}] Successfully swapped {amount.Ether} {from_token_name} to {min_amount.Ether} {to_token_name} | [JediSwap]")
                    return True
        except Exception as exc:
            logger.error(f"[{self.client.address}] Couldn't swap | [JediSwap] | {exc}")

    async def add_liquidity(self) -> bool:
        try:
            get_data_for_adding_liquidity = await GetDataForLP(client=self.client, dex_name='jediswap')

            pooled_token_address, pooled_token_name, amount_one, amount_two, amount_in_usdt, token_one_address, token_two_address, token_one_name, token_two_name, token_one_decimals, token_two_decimals = get_data_for_adding_liquidity.values()

            logger.debug(f"[{self.client.address}] Adding liquidity to {pooled_token_name} pool {amount_one.Ether} {token_one_name}...[JediSwap]")

            is_approved_one = await self.client.approve_interface(token_address=token_one_address,
                                                              spender=JediSwap.JEDISWAP_CONTRACT,
                                                              decimals=token_one_decimals, amount=amount_one)

            is_approved_two = await self.client.approve_interface(token_address=token_two_address,
                                                              spender=JediSwap.JEDISWAP_CONTRACT,
                                                              decimals=token_two_decimals, amount=amount_two)
            if is_approved_one and is_approved_two:
                tx_hash = await self.client.send_transaction(interacted_contract=self.contract,
                                                             function_name='add_liquidity',
                                                             tokenA=token_one_address,
                                                             tokenB=token_two_address,
                                                             amountADesired=amount_one.Wei,
                                                             amountBDesired=amount_two.Wei,
                                                             amountAMin=int(amount_one.Wei * (1 - SLIPPAGE/ 100)),
                                                             amountBMin=int(amount_two.Wei * (1 - SLIPPAGE/ 100)),
                                                             to=self.client.address,
                                                             deadline=int(time() + 3600))
                if tx_hash:
                    logger.success(
                        f"[{self.client.address}] Successfully added ${amount_in_usdt} to {pooled_token_name} pool | [JediSwap]")
                    random_sleep = random.randint(DELAY_BETWEEN_ACTIONS[0], DELAY_BETWEEN_ACTIONS[1])
                    logger.info(f"[{self.client.address}] Sleeping for {random_sleep} sec before removing liquidity | [JediSwap]")
                    await asyncio.sleep(random_sleep)
                    await self.remove_liquidity(pooled_token_contract=pooled_token_address,
                                                amountA=int(amount_one.Wei * (1 - SLIPPAGE/ 100)),
                                                amountB=int(amount_two.Wei * (1 - SLIPPAGE/ 100)))
                    return True
        except Exception as exc:
            logger.error(f"[{self.client.address}] Couldn't add $ to pool | [JediSwap] | {exc}")

    async def remove_liquidity(self, pooled_token_contract, amountA = None, amountB = None) -> bool:
        global tokenA, tokenB
        try:
            logger.debug(
                f"[{self.client.address}] Removing liquidity | [JediSwap]")
            amount: TokenAmount = await self.client.get_balance(token_address=pooled_token_contract, decimals=18)
            if pooled_token_contract == 0x04d0390b777b424e43839cd1e744799f3de6c176c7e32c1812a41dbd9c19db6a:
                tokenA = JediSwap.ETH_ADDRESS
                tokenB = JediSwap.USDC_ADDRESS
            elif pooled_token_contract == 0x045e7131d776dddc137e30bdd490b431c7144677e97bf9369f629ed8d3fb7dd6:
                tokenA = JediSwap.ETH_ADDRESS
                tokenB = JediSwap.USDT_ADDRESS
            elif pooled_token_contract == 0x05801bdad32f343035fb242e98d1e9371ae85bc1543962fedea16c59b35bd19b:
                tokenA = JediSwap.USDC_ADDRESS
                tokenB = JediSwap.USDT_ADDRESS
            is_approved = await self.client.approve_interface(token_address=pooled_token_contract,
                                                              spender=JediSwap.JEDISWAP_CONTRACT,
                                                              decimals=18, amount=amount)
            if is_approved:
                tx_hash = await self.client.send_transaction(interacted_contract=self.contract,
                                                             function_name='remove_liquidity',
                                                             tokenA=tokenA,
                                                             tokenB=tokenB,
                                                             liquidity=amount.Wei,
                                                             amountAMin=amountA,
                                                             amountBMin=amountB,
                                                             to=self.client.address,
                                                             deadline=int(time() + 3600))
                if tx_hash:
                    logger.success(
                        f"[{self.client.address}] Successfully removed liquidity | [JediSwap]")
                    return True
        except Exception as exc:
            logger.error(f"[{self.client.address}] Couldn't remove liquidity | [JediSwap] {exc}")
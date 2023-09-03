import asyncio
import random
from time import time

from utils.Client import Client
from utils.GetData import GetDataForSwap, GetDataForLP
from utils.Info import TokenAmount, ContractInfo
from config.logger import logger
from config.settings import SLIPPAGE, DELAY_BETWEEN_ACTIONS
from starknet_py.contract import Contract


class TenkSwap:

    ETH_ADDRESS = ContractInfo.ETH.get('address')
    ETH_ABI = ContractInfo.ETH.get('abi')

    USDT_ADDRESS = ContractInfo.USDT.get('address')
    USDT_ABI = ContractInfo.USDT.get('abi')

    USDC_ADDRESS = ContractInfo.USDC.get('address')
    USDC_ABI = ContractInfo.USDC.get('abi')

    DAI_ADDRESS = ContractInfo.DAI.get('address')
    DAI_ABI = ContractInfo.DAI.get('abi')

    TENKSWAP_CONTRACT_ADDRESS = ContractInfo.TENKSWAP.get('address')
    TENKSWAP_ABI = ContractInfo.TENKSWAP.get('abi')

    def __init__(self, client: Client):
        self.client = client
        self.contract = Contract(address=TenkSwap.TENKSWAP_CONTRACT_ADDRESS, abi=TenkSwap.TENKSWAP_ABI, provider=self.client.account)

    async def swap(self, swap_to_eth=False):
        try:
            global min_amount
            min_amount = 0

            data_for_swap = await GetDataForSwap(client=self.client, swap_to_eth=swap_to_eth)
            if data_for_swap == {}:
                return False
            amount, to_token_address, to_token_name, from_token_address, from_token_name, from_token_decimals = data_for_swap.values()

            logger.info(f"[{self.client.address}] Swapping {amount.Ether} {from_token_name} to {to_token_name}...[10kSwap]")
            is_approved = await self.client.approve_interface(token_address=from_token_address,
                                                              spender=TenkSwap.TENKSWAP_CONTRACT_ADDRESS,
                                                              decimals=from_token_decimals, amount=amount)
            if is_approved:
                eth_price = Client.get_eth_price()
                if to_token_name == 'USDT' or to_token_name == 'USDC':
                    if from_token_name == 'ETH':
                        min_to_amount = TokenAmount(amount=eth_price * float(amount.Ether) * (1 - SLIPPAGE / 100), decimals=6)
                        min_amount = min_to_amount
                    elif from_token_name == 'DAI':
                        min_to_amount = TokenAmount(amount=float(amount.Ether) * (1 - SLIPPAGE / 100), decimals=6)
                        min_amount = min_to_amount

                elif to_token_name == 'ETH':
                    min_to_amount = TokenAmount(amount=float(amount.Ether) / eth_price * (1 - SLIPPAGE / 100), decimals=18)
                    min_amount = min_to_amount

                elif to_token_name == 'DAI':
                    if from_token_name == 'USDT' or from_token_name == 'USDC':
                        min_to_amount = TokenAmount(amount=float(amount.Ether) * (1 - SLIPPAGE / 100), decimals=18)
                        min_amount = min_to_amount

                    elif from_token_name == 'ETH':
                        min_to_amount = TokenAmount(amount=eth_price * float(amount.Ether) * (1 - SLIPPAGE / 100), decimals=18)
                        min_amount = min_to_amount

                tx_hash = await self.client.send_transaction(interacted_contract=self.contract,
                                                             function_name='swapExactTokensForTokens',
                                                             amountIn=amount.Wei,
                                                             amountOutMin=min_amount.Wei,
                                                             path=[from_token_address, to_token_address],
                                                             to=self.client.address,
                                                             deadline=int(time() + 3600))

                if tx_hash:
                    logger.info(f"[{self.client.address}] Successfully swapped {amount.Ether} {from_token_name} to {min_amount.Ether} {to_token_name} | [10kSwap]")
                    return True
        except Exception as err:
            logger.error(f"[{self.client.address}] Error while swapping | [10kSwap] | {err}")
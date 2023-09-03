import asyncio
import random
from time import time

from utils.Client import Client
from utils.Info import TokenAmount, ContractInfo
from config.logger import logger
from starknet_py.contract import Contract


class Minter:
    def __init__(self, client: Client):
        self.client = client

    async def mintStarkVerse(self):
        try:
            contract_address = ContractInfo.STARKVERSE.get('address')
            abi = ContractInfo.STARKVERSE.get('abi')
            contract = Contract(address=contract_address, abi=abi, provider=self.client.account)

            logger.info(f"[{self.client.address_to_log}] Minting nft | [StarkVerse NFT] |")

            tx_hash = await self.client.send_transaction(interacted_contract=contract,
                                                         function_name='publicMint',
                                                         to=self.client.address
                                                         )
            if tx_hash:
                logger.info(
                    f"[{self.client.address_to_log}] Successfully minted | [StarkVerse NFT] |")
                return True

        except Exception as err:
            logger.error(f"[{self.client.address_to_log}] Error while minting | [StarkVerse NFT] | {err}")




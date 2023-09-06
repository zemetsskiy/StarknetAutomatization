import asyncio
import random
from random import uniform, randint

import aiohttp

from utils.Client import Client
from utils.Info import ContractInfo, TokenAmount
from config.logger import logger
from starknet_py.contract import Contract
from starknet_py.net.client_models import Call
from starknet_py.hash.selector import get_selector_from_name
from config.settings import RANDOM_INCREASE_FEE


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

    async def mintStarknetIdNFT(self):
        try:
            contract_address = ContractInfo.STARKNETIDNFT.get('address')
            abi = ContractInfo.STARKNETIDNFT.get('abi')
            contract = Contract(address=contract_address, abi=abi, provider=self.client.account)

            logger.info(f"[{self.client.address_to_log}] Minting nft | [Starknet.id Identity NFT] |")

            id = random.randint(0, 2**128 - 1)

            max_fee = TokenAmount(amount=float(uniform(0.0007534534534, 0.001)))

            prepared_call = contract.functions["mint"].prepare(id, max_fee=int(max_fee.Wei * (1 + randint(RANDOM_INCREASE_FEE[0], RANDOM_INCREASE_FEE[1]) / 100)))
            await prepared_call.invoke()

            logger.info(f"[{self.client.address_to_log}] Successfully minted | [Starknet.id Identity NFT] |")

            return True
        except Exception as err:
            logger.error(f"[{self.client.address_to_log}] Error while minting | [Starknet.id Identity NFT] | {err}")

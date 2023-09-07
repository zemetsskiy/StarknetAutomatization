import ccxt

from config.logger import logger
from binance.client import Client


class Binance:
    @staticmethod
    def withdraw_token(api_key, api_secret, address, amount):
        try:
            client = Client(api_key, api_secret)
            response = client.withdraw(coin="ETH", address=address, amount=amount, network="ETH")
            if response:
                logger.info(f"{amount}ETH were successfully withdrawed to {address}")
        except Exception as err:
            logger.error(f"Error while withdrawing cash from Binance: {err}")
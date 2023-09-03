import asyncio

from defi.JediSwap import JediSwap
from utils.Client import Client

if __name__ == "__main__":
    address = int(address, 16)
    client = Client(address=address, private_key=private)
    JediSwap_client = JediSwap(client=client)
    asyncio.run(JediSwap_client.swap())
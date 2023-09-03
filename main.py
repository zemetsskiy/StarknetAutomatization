import asyncio

from defi.JediSwap import JediSwap
from utils.Client import Client

if __name__ == "__main__":
    address = "0x06456688D339347FaCE91fA70A150D5e183731B5d3bA32A7F02FF8d1Bf966DCd"
    address = int(address, 16)
    private = "0x022a5194cb7ed83a330d445150751e10dddc027a45cd8ae3be979c78d0811df4"
    client = Client(address=address, private_key=private)
    JediSwap_client = JediSwap(client=client)
    asyncio.run(JediSwap_client.swap())
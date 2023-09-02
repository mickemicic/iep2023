from web3 import HTTPProvider, Web3
import os

url = os.environ["BLOCKCHAIN"]
web3 = Web3(HTTPProvider(f"http://{url}:8545"))

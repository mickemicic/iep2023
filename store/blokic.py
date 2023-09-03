from web3 import HTTPProvider, Web3
import os

url = os.environ["BLOCKCHAIN"]
web3 = Web3(HTTPProvider(f"http://{url}:8545"))


def readFile(path):
    with open(path, "r") as file:
        return file.read()


bytecode = readFile("./sol_bytecode.bin")
abi = readFile("./sol_abi.abi")

setContract = web3.eth.contract(
    bytecode=bytecode,
    abi=abi
)

owner = web3.eth.accounts[0]

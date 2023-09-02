import json

from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
from web3 import Web3, HTTPProvider

from models import database, Order
from roleDecorator import roleCheck
from configuration import Configuration

from blokic import web3

# from store.models import database, Order
# from store.roleDecorator import roleCheck
# from store.configuration import Configuration

import io
import csv

from web3.exceptions import ContractLogicError

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


def readFile(path):
    with open(path, "r") as file:
        return file.read()


# web3 = Web3(HTTPProvider("http://127.0.0.1:8545"))
bytecode = readFile("./sol_bytecode.bin")
abi = readFile("./sol_abi.abi")


@application.route("/orders_to_deliver", methods=["GET"])
@jwt_required()
@roleCheck("courier")
def ordersToDeliver():
    orders = Order.query.filter(Order.status == "PENDING").all()
    ordArr = []

    for o in orders:
        order = {
            "id": o.id,
            "email": o.buyer
        }
        ordArr.append(order)

    return jsonify({"orders": ordArr}), 200


@application.route("/pick_up_order", methods=["POST"])
@jwt_required()
@roleCheck("courier")
def pickUpOrder():
    if "id" not in request.json:
        return {"message": "Missing order id."}, 400

    try:
        if int(request.json["id"]) <= 0:
            return {"message": "Invalid order id."}, 400
    except ValueError:
        return {"message": "Invalid order id."}, 400

    orderId = request.json["id"]

    reqOrder = Order.query.filter(Order.id == orderId).first()

    if reqOrder is None:
        return jsonify({"message": "Invalid order id."}), 400

    if reqOrder.status != "CREATED":
        return jsonify({"message": "Invalid order id."}), 400

    if "address" not in request.json or request.json["address"] == "":
        return {"message": "Missing address."}, 400

    if not web3.is_address(request.json["address"]):
        return {"message": "Invalid address."}, 400

    address = request.json["address"]

    contract_address = reqOrder.address
    contract = web3.eth.contract(
        abi=abi,
        bytecode=bytecode,
        address=contract_address
    )

    paid = contract.functions.getDeposit().call()
    if int(reqOrder.price) != paid:
        return jsonify({"message": "Transfer not complete."}), 400

    owner = web3.eth.accounts[0]

    try:
        contract.functions.assignCourier(address).transact({
            "from": owner
        })

    except ContractLogicError as e:
        mes = e.message[e.message.find("revert ") + 7:]
        return {"message": mes}, 400

    reqOrder.status = "PENDING"
    database.session.commit()

    return application.response_class(status=200)


@application.route("/", methods=["GET"])
@jwt_required()
@roleCheck("courier")
def index():
    return "KURIR RADI!"


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5003)

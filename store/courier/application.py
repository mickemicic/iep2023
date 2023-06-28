import json

from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
from web3 import Web3, HTTPProvider

from models import database, Order
from roleDecorator import roleCheck
from configuration import Configuration

# from store.models import database, Order
# from store.roleDecorator import roleCheck
# from store.configuration import Configuration

import io
import csv

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


def readFile(path):
    with open(path, "r") as file:
        return file.read()


web3 = Web3(HTTPProvider("http://127.0.0.1:8545"))
bytecode = readFile("../sol_bytecode.bin")
abi = readFile("../sol_abi.abi")


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
    try:
        orderId = request.json.get("id")
    except AttributeError:
        return jsonify({"message": "Missing order id."}), 400

    if orderId is None:
        return jsonify({"message": "Missing order id."}), 400

    try:
        int(orderId)
    except ValueError:
        return jsonify({"message": "Invalid order id."}), 400

    if orderId <= 0 or int(orderId) != orderId:
        return jsonify({"message": "Invalid order id."}), 400

    reqOrder = Order.query.filter(Order.id == orderId).first()

    if reqOrder is None:
        return jsonify({"message": "Invalid order id."}), 400

    if reqOrder.status != "PENDING":
        return jsonify({"message": "Invalid order id."}), 400

    address = request.json.get("address")
    if address is None or len(address) == 0:
        return jsonify({"message": "Missing address."}), 400

    addressExists = 0
    for i in web3.eth.accounts:
        if i == address:
            addressExists = 1
            print("PRONADJENA")

    if addressExists == 0:
        return jsonify({"message": "Invalid address."}), 400

    contract_address = reqOrder.address
    contract = web3.eth.contract(abi=abi, address=contract_address)

    paid = contract.functions.getDeposit().call()
    if int(reqOrder.price) != paid:
        return jsonify({"message": "Transfer not complete."}), 400

    contract.functions.assignCourier(address).call()

    reqOrder.status = "TRANSIT"
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

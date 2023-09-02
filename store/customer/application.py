import json
from datetime import datetime

from flask import Flask, request, jsonify, Response
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity

from web3 import Web3, HTTPProvider, Account
# from solcx import compile_source

from roleDecorator import roleCheck
from configuration import Configuration
from models import database, Product, Category, Order, OrderProduct
from web3.exceptions import InvalidAddress, ContractLogicError

# from store.courier.application import web3

from blokic import web3

# from store.roleDecorator import roleCheck
# from store.configuration import Configuration
# from store.models import database, Product, Category, Order, OrderProduct

# web3 = Web3(HTTPProvider("http://127.0.0.1:8545"))
owner = web3.eth.accounts[0]

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


def readFile(path):
    with open(path, "r") as file:
        return file.read()


bytecode = readFile("./sol_bytecode.bin")
abi = readFile("./sol_abi.abi")

setContract = web3.eth.contract(
    bytecode=bytecode,
    abi=abi
)


# bytecode = 123
# abi = 123


@application.route("/search", methods=["GET"])
@jwt_required()
@roleCheck("customer")
def search():
    product = request.args.get("name", default="")
    pro = Product.query.filter(Product.name.contains(product)).all()

    categoryName = request.args.get("category", default="")
    cat = Category.query.filter(Category.name.contains(categoryName)).all()

    categoryList = []  # arrCategory
    productList = []

    idHelper = []

    # imam sve kategorije sa imenom category, i sve proizvode sa imenom name

    # products = Product.query.join(ProductCategory).join(Category).filter(
    #     and_(Category.name.contains(categoryName), Product.title.contains(product)))

    # for p in products:
    #     print(p.title +" - ime, " +" \n")
    #     for c in p.categories:
    #         print("-------------" + c.name + " - kategorija " + "\n")

    for p in pro:
        catArr = []
        flag = 0
        for c in p.categories:
            catArr.append(c.name)
            if c in cat:
                flag = 1
                if c.name not in categoryList:
                    categoryList.append(c.name)

        if flag and p.id not in idHelper:
            pomPro = {
                "categories": catArr,  # mozda ne sme 21e142143141353124
                "id": p.id,
                "name": p.name,
                "price": p.price,
            }
            idHelper.append(p.id)
            productList.append(pomPro)

    searchResults = {"categories": categoryList, "products": productList}

    return jsonify(searchResults), 200


@application.route("/order", methods=["POST"])
@jwt_required()
@roleCheck("customer")
def order():
    try:
        requests = request.json.get("requests")

        # conStr = json.loads(requests)
        # if "requests" not in conStr:
        #     return jsonify({"message": "Field requests is missing."}), 400

        for idReq, req in enumerate(requests):
            if req.get("id") is None:
                return jsonify({"message": "Product id is missing for request number " + str(idReq) + "."}), 400
            if req.get("quantity") is None:
                return jsonify({"message": "Product quantity is missing for request number " + str(idReq) + "."}), 400
            if not isinstance(req.get("id"), int) or req.get("id") <= 0:
                return jsonify({"message": "Invalid product id for request number " + str(idReq) + "."}), 400
            if not isinstance(req.get("quantity"), int) or req.get("quantity") <= 0:
                return jsonify({"message": "Invalid product quantity for request number " + str(idReq) + "."}), 400
            if Product.query.filter(Product.id == req.get("id")).first() is None:
                return jsonify({"message": "Invalid product for request number " + str(idReq) + "."}), 400

        address = request.json.get("address")
        if address is None or len(address) == 0:
            return jsonify({"message": "Field address is missing."}), 400
        print(address)

        # addressExists = 0
        # for i in web3.eth.accounts:
        #     if i == address:
        #         addressExists = 1
        #         print("PRONADJENA")
        #
        # if addressExists == 0:
        #     return jsonify({"message": "Invalid address."}), 400

        if not web3.is_address(address):
            return jsonify({"message": "Invalid address."}), 400

        proArr = []
        totalPrice = 0

        newOrd = Order(price=0, status="CREATED", timestamp=datetime.now().isoformat(), buyer=get_jwt_identity(),
                       address=0)
        database.session.add(newOrd)
        database.session.commit()

        for req in requests:
            idPro = req["id"]
            pro = Product.query.filter((Product.id == idPro)).first()

            proArr.append(pro)
            newOrdPro = OrderProduct(orderId=newOrd.id, productId=idPro, price=pro.price, quantity=req["quantity"],
                                     received=0, requested=req["quantity"])
            totalPrice = totalPrice + pro.price * req["quantity"]

            database.session.add(newOrdPro)

            database.session.commit()

        try:
            intPrice = int(totalPrice)
            value = web3.to_wei(intPrice, 'ether')
            conHash = setContract.constructor(address, value).transact({
                "from": owner
            })
            receipt = web3.eth.wait_for_transaction_receipt(conHash)
        except InvalidAddress:
            return jsonify({"message": "Invalid address."}), 400

        newOrd.address = receipt.contractAddress
        newOrd.price = totalPrice
        database.session.commit()

        #######
        # deployed_contract = web3.eth.contract(abi=abi, bytecode=bytecode)
        # constructor_args = (newOrd.id, web3.to_checksum_address("0x3514df7e736618bf1e8f19262b5b79058428ac89"), int(totalPrice))
        # transaction_hash = deployed_contract.constructor(*constructor_args).transact({
        #     'from': address
        # }) #########
        # transaction_receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)
        #
        # # Retrieve the contract address
        # contract_address = transaction_receipt['contractAddress']
        #
        # newOrd.address = contract_address
        ################
        ###
        # contract = web3.eth.contract(abi=abi, address=contract_address)  # ovo loaduje contract da bi pozivao funkcije
        # contract.d
        # ###
        #
        # arguments = [newOrd.id, web3.eth.accounts[0], totalPrice]
        #
        # private_key = ""
        # account = web3.eth.account.privateKeyToAccount(private_key)
        #
        # contract_transaction = contract.constructor(arguments).build_transaction()
        #
        # signed_transaction = account.signTransaction(contract_transaction)
        # tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        # tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        # database.session.commit()

        return jsonify({"id": newOrd.id}), 200

    except (UnboundLocalError, AttributeError, TypeError):
        return jsonify({"message": "Field requests is missing."}), 400


@application.route("/status", methods=["GET"])
@jwt_required()
@roleCheck("customer")
def status():
    email = get_jwt_identity()
    orders = Order.query.filter(Order.buyer == email).all()

    ordersList = []

    for o in orders:
        productList = []
        for po in o.productOrders:
            productCategories = []
            for cP in po.products.categories:
                productCategories.append(cP.name)
            pomPro = {
                "categories": productCategories,
                "name": po.products.name,
                "price": po.price,
                "quantity": po.quantity
            }
            productList.append(pomPro)
        currOrder = {
            "products": productList,
            "price": o.price,
            "status": o.status,
            "timestamp": o.timestamp
        }
        ordersList.append(currOrder)

    return jsonify({"orders": ordersList}), 200


@application.route("/pay", methods=["POST"])
@jwt_required()
@roleCheck("customer")
def pay():
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

    if "keys" not in request.json or request.json["keys"] == "":
        return jsonify({"message": "Missing keys."}), 400

    if "passphrase" not in request.json or len(request.json["passphrase"]) == 0:
        return jsonify({"message": "Missing passphrase."}), 400
    # try:
    #     keys = request.json.get("keys")
    # except (AttributeError, KeyError, TypeError):
    #     return jsonify({"message": "Missing keys."}), 400
    #
    # if keys is None or len(keys) == 0:
    #     return jsonify({"message": "Missing keys."}), 400
    #
    # try:
    #     passphrase = request.json.get("passphrase", None)
    # except AttributeError:
    #     return jsonify({"message": "Missing passphrase."}), 400
    #
    # if not passphrase or len(passphrase) == 0:
    #     return jsonify({"message": "Missing passphrase."}), 400

    passphrase = request.json.get("passphrase")
    keys = request.json.get("keys")
    try:
        private_key = Account.decrypt(keys, passphrase).hex()
        address = web3.to_checksum_address(keys["address"])
    except (KeyError, ValueError, TypeError):
        return jsonify({"message": "Invalid credentials."}), 400

    balance = web3.eth.get_balance(address)
    balanceWei = web3.to_wei(balance, 'ether')
    contract = web3.eth.contract(
        reqOrder.address,
        abi=abi,
        bytecode=bytecode
    )

    if reqOrder.price > balanceWei:
        return jsonify({"message": "Insufficient funds."}), 400

    deposit = contract.functions.getDeposit().call()
    if deposit > 0:
        return jsonify({"message": "Transfer already complete."}), 400

    intPrice = int(reqOrder.price)

    value = web3.from_wei(intPrice, 'ether')  ##OPO

    try:
        transaction = contract.functions.depositFunds().build_transaction({
            "from": address,
            "value": value,
            "gasPrice": 21000,
            "nonce": web3.eth.get_transaction_count(address)
        })

        signedTrans = web3.eth.account.sign_transaction(transaction, private_key)
        transHash = web3.eth.send_raw_transaction(signedTrans.rawTransaction)
        receipt = web3.eth.wait_for_transaction_receipt(transHash)

    except ContractLogicError as e:
        mes = e.message[e.message.find("revert ") + 7:]
        return {"message": mes}, 400

    return application.response_class(status=200)


@application.route("/delivered", methods=["POST"])
@jwt_required()
@roleCheck("customer")
def delivered():
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

    if reqOrder.status != "TRANSIT":
        return jsonify({"message": "Invalid order id."}), 400

    try:
        keys = request.json.get("keys")
    except AttributeError:
        return jsonify({"message": "Missing keys."}), 400

    if keys is None:
        return jsonify({"message": "Missing keys."}), 400

    try:
        passphrase = request.json.get("passphrase")
    except AttributeError:
        return jsonify({"message": "Missing passphrase."}), 400

    if len(passphrase) == 0:
        return jsonify({"message": "Missing passphrase."}), 400

    try:
        private_key = Account.decrypt(keys, passphrase).hex()
    except KeyError:
        return jsonify({"message": "Invalid credentials."}), 400

    account = web3.eth.account.from_key(private_key)
    contract_address = reqOrder.address
    address = web3.to_checksum_address(keys["address"])

    contract = web3.eth.contract(
        abi=abi,
        bytecode=bytecode,
        address=contract_address
    )

    try:
        transaction = contract.functions.confirmDelivery().build_transaction({
            "from": address,
            "gasPrice": 21000,
            "nonce": web3.eth.get_transaction_count(address)
        })
        signedTrans = web3.eth.account.sign_transaction(transaction, private_key)
        transHash = web3.eth.send_raw_transaction(signedTrans.rawTransaction)
        receipt = web3.eth.wait_for_transaction_receipt(transHash)
    except ValueError:
        return jsonify({"message": "Invalid customer account."}), 400
    # print(resp)

    reqOrder.status = "COMPLETE"
    OrderProd = OrderProduct.query.filter(OrderProduct.orderId == reqOrder.id).all()
    print(OrderProd)
    for o in OrderProd:
        o.received = o.quantity
        o.requested = 0
    database.session.commit()

    return application.response_class(status=200)


@application.route("/", methods=["GET"])
def index():
    # contractic()
    return "customer RADI!"


def contractic():
    data = [
        189,
        9,
        57,
        251,
        24,
        221,
        5,
        163,
        209,
        241,
        187,
        42,
        24,
        189,
        69,
        194,
        235,
        206,
        195,
        246,
        65,
        124,
        179,
        208,
        210,
        162,
        199,
        167,
        87,
        14,
        58,
        100
    ]
    bytesData = bytes(data)
    account = Account.from_key(bytesData)

    # print(account.address)
    # for i in web3.eth.accounts:
    #     print(i)
    # account = Account.create()
    passphrase = "iep_project"
    encrypted_key = Account.encrypt(account.key, passphrase)

    key_file = {
        "version": 3,
        # "id": account.uuid,
        "address": account.address,
        "Crypto": encrypted_key
    }
    # Save the key file as a JSON file
    with open("keys_customer1.json", "w") as file:
        json.dump(key_file, file)

    print("Key file created successfully.")
    # # acc = web3.eth.accounts[0]
    # # bal = web3.eth.get_balance(acc)
    # # print(web3.from_wei(bal, 'ether'))
    return "heh"


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5004)

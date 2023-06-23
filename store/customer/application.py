import json
from datetime import datetime

from flask import Flask, request, jsonify, Response
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity

from roleDecorator import roleCheck
from configuration import Configuration
from models import database, Product, Category, Order, OrderProduct

# from store.roleDecorator import roleCheck
# from store.configuration import Configuration
# from store.models import database, Product, Category, Order, OrderProduct

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


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

        proArr = []
        totalPrice = 0

        newOrd = Order(price=0, status="CREATED", timestamp=datetime.now().isoformat(), buyer=get_jwt_identity())
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

        newOrd.price = totalPrice
        database.session.commit()

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

    reqOrder.status = "COMPLETE"
    OrderProd = OrderProduct.query.filter(OrderProduct.orderId == reqOrder.id).all()
    print(OrderProd)
    for o in OrderProd:
        o.received = o.quantity
        o.requested = 0
    database.session.commit()

    return application.response_class(status=200)


@application.route("/", methods=["GET"])
@jwt_required()
@roleCheck("customer")
def index():
    return "customer RADI!"


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5004)

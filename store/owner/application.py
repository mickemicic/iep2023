import json

from flask import Flask, jsonify, Response, request
from flask_jwt_extended import JWTManager, jwt_required
from sqlalchemy import func

from roleDecorator import roleCheck
from configuration import Configuration
from models import database, Product, Category, OrderProduct, ProductCategory

# from store.roleDecorator import roleCheck
# from store.configuration import Configuration
# from store.models import database, Product, Category, OrderProduct, ProductCategory

import io
import csv

application = Flask(__name__)
application.config.from_object(Configuration)

jwt = JWTManager(application)


@application.route("/update", methods=["POST"])
@jwt_required()
@roleCheck(role="owner")
def updateStore():
    # con = request.files["file"].stream.read().decode("utf-8")
    con = request.files.get("file", None)

    if con:
        stream = io.StringIO(con.stream.read().decode("utf-8"))
        reader = list(csv.reader(stream))       #kroz listu moze da se prodje vise puta, kroz reader jednom

        rowNum = 0

        for row in reader:
            if len(row) != 3:
                return Response(json.dumps({"message": f"Incorrect number of values on line {rowNum}."}), status=400)

            name = row[1]

            try:
                float(row[2])
            except ValueError:
                return Response(json.dumps({"message": f"Incorrect price on line {rowNum}."}), status=400)

            if not float(row[2]) > 0:
                return Response(json.dumps({"message": f"Incorrect price on line {rowNum}."}), status=400)

            if Product.query.filter(Product.name == name).first():
                return Response(json.dumps({"message": f"Product {name} already exists."}), status=400)

            rowNum += 1

        for row in reader:
            categories = row[0]
            name = row[1]
            price = float(row[2])
            categories = categories.split("|")

            product = Product(
                name=name,
                price=price
            )

            database.session.add(product)
            for category in categories:
                cat = Category.query.filter(Category.name == category).first()
                if not cat:
                    cat = Category(name=category)
                    database.session.add(cat)
                    database.session.commit()
                productCat = ProductCategory(productId=product.id, categoryId=cat.id)
                database.session.add(productCat)
                database.session.commit()

        database.session.commit()
        return Response(status=200)
    else:
        return Response(json.dumps({"message": "Field file is missing."}), status=400)


@application.route("/product_statistics", methods=["GET"])
@jwt_required()
@roleCheck("owner")
def productStats():
    # orders = OrderProduct.query.group_by(OrderProduct.productId). \
    #     with_entities(OrderProduct.productId,
    #                   func.sum(OrderProduct.requested).label("sold"),
    #                   (func.sum(OrderProduct.requested) - func.sum(OrderProduct.received)).label("waiting")).all()

    orders = OrderProduct.query.group_by(OrderProduct.productId). \
        with_entities(OrderProduct.productId,
                      func.sum(OrderProduct.received).label("sold"),
                      func.sum(OrderProduct.requested).label("waiting")).all()

    statsArr = []

    for o in orders:
        productName = Product.query.filter(Product.id == o.productId).first()
        pomStat = {
            "name":  productName.name,
            "sold": int(o.sold),
            "waiting": int(o.waiting)
        }

        statsArr.append(pomStat)

    return jsonify({"statistics": statsArr}), 200


@application.route("/category_statistics", methods=["GET"])
@jwt_required()
@roleCheck("owner")
def categoryStats():
    reqs = func.coalesce(func.sum(OrderProduct.requested), 0)
    cat = Category.query.outerjoin(ProductCategory, ProductCategory.categoryId == Category.id).outerjoin \
        (OrderProduct, OrderProduct.productId == ProductCategory.productId).group_by(Category.id).order_by(reqs.desc()) \
        .order_by(Category.name).all()

    catArr = []

    for c in cat:
        catArr.append(c.name)

    return jsonify({"statistics": catArr}), 200


@application.route("/probica", methods=["POST"])
def probica():
    con = request.files.get("file", None)
    if con:
        stream = io.StringIO(con.stream.read().decode("utf-8"))
        reader = csv.reader(stream)

        rowNum = 0

        for row in reader:
            print(len(row))
    return jsonify({}), 200



if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5005)

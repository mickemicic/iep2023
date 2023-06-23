import json
import re

from flask import Flask, request, Response, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity
from sqlalchemy import and_

from configuration import Configuration
from models import database, User, UserRole, Role
from roleDecorator import roleCheck

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route("/register_customer", methods=["POST"])
def register_customer():
    message = register("customer")
    if message == "ok":
        return jsonify(), 200
    else:
        return jsonify({"message": message}), 400


@application.route("/register_courier", methods=["POST"])
def register_courier():
    message = register("courier")
    if message == "ok":
        return jsonify(), 200
    else:
        return jsonify({"message": message}), 400


def register(userRole):
    try:
        forename = request.json.get("forename", "")
    except AttributeError:
        return "Field forename is missing."

    try:
        surname = request.json.get("surname", "")
    except AttributeError:
        return "Field surname is missing."

    try:
        email = request.json.get("email", "")
    except AttributeError:
        return "Field email is missing."
        # return Response(json.dumps({"message": "Field email is missing."}), status=400)

    try:
        password = request.json.get("password", "")
    except AttributeError:
        return "Field password is missing."

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0
    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0

    if forenameEmpty:
        return "Field forename is missing."

    if surnameEmpty:
        return "Field surname is missing."

    if emailEmpty:
        return "Field email is missing."

    if passwordEmpty:
        return "Field password is missing."

    # result = parseaddr(email)
    # if len(result[0]) == 0:
    #     return Response("first "+result[0]+" -- -" +result[1], status=400)     RESULT[0]

    emailValid = re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email)

    if not emailValid:
        return "Invalid email."

    if len(password) < 8:
        # or re.search(r"\d", password) is None or re.search(r"[A-Z]", password) is None or \
        # re.search(r"[a-z]", password) is None:
        return "Invalid password."

    if User.query.filter(User.email == email).first():
        return "Email already exists."

    user = User(email=email, password=password, forename=forename, surname=surname)
    database.session.add(user)
    database.session.commit()

    role = Role.query.filter(Role.name == userRole).first()

    roleId = role.id
    userRole = UserRole(userId=user.id, roleId=roleId)
    database.session.add(userRole)
    database.session.commit()

    return "ok"


@application.route("/login", methods=["POST"])
def login():
    try:
        email = request.json.get("email", "")
    except AttributeError:
        return Response(json.dumps({"message": "Field email is missing."}), status=400)

    try:
        password = request.json.get("password", "")
    except AttributeError:
        return Response(json.dumps({"message": "Field password is missing."}), status=400)

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0

    if emailEmpty:
        return Response(json.dumps({"message": "Field email is missing."}), status=400)

    if passwordEmpty:
        return Response(json.dumps({"message": "Field password is missing."}), status=400)

    emailValid = re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email)

    if not emailValid:
        return Response(json.dumps({"message": "Invalid email."}), status=400)

    user = User.query.filter(and_(User.email == email, User.password == password)).first()

    if not user:
        return Response(json.dumps({"message": "Invalid credentials."}), status=400)

    additionalClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": [str(role) for role in user.roles]
    }

    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims)
    # refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims)

    # return Response ( accessToken, status = 200 );
    # return jsonify(accessToken=accessToken, refreshToken=refreshToken)

    return Response(json.dumps({"accessToken": accessToken}), status=200)


@application.route("/delete", methods=["POST"])
@jwt_required()
def delete():
    user = User.query.filter(User.email == get_jwt_identity()).first()

    if not user:
        return Response(json.dumps({"message": "Unknown user."}), status=400)

    User.query.filter(User.email == get_jwt_identity()).delete()
    database.session.commit()

    return Response(status=200)


@application.route("/check", methods=["POST"])
@jwt_required()
def check():
    return "Token is valid!"


@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()

    additionalClaims = {
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "roles": refreshClaims["roles"]
    }

    return jsonify(accessToken=create_access_token(identity=identity, additional_claims=additionalClaims)), 200


#################################################################
@application.route("/proba", methods=["GET"])
def proba():
    user = User.query.filter(and_(User.email == "pera@pera.com", User.password == "1234")).first()

    if not user:
        return Response("Invalid credentials!", status=400)

    return user.forename


##################################################################
@application.route("/", methods=["GET"])
def index():
    return "RADI!"


@application.before_first_request
def startup():
    ownerRole = Role.query.filter(Role.name == "owner").first()
    if ownerRole is None:
        ownerRole = Role(name="owner")
        database.session.add(ownerRole)

    customerRole = Role.query.filter(Role.name == "customer").first()
    if customerRole is None:
        customerRole = Role(name="customer")
        database.session.add(customerRole)

    courierRole = Role.query.filter(Role.name == "courier").first()
    if courierRole is None:
        courierRole = Role(name="courier")
        database.session.add(courierRole)

    owner = User.query.filter(User.email == "onlymoney@gmail.com").first()
    if owner is None:
        owner = User(
            forename="Scrooge",
            surname="McDuck",
            email="onlymoney@gmail.com",
            password="evenmoremoney"
        )
        database.session.add(owner)
        database.session.commit()

        owner = User.query.filter(User.email == "onlymoney@gmail.com").first()

        ownerRole = UserRole(
            userId=owner.id,
            roleId=ownerRole.id
        )
        database.session.add(owner)
        database.session.add(ownerRole)
    database.session.commit()


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5002)

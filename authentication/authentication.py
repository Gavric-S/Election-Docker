from flask import Flask, request, Response;
from configuration import Configuration;
from models import database, User, Role;
from email.utils import parseaddr;
import re;
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity;
from sqlalchemy import and_, or_;
from authorizationDecorator import roleCheck;
import json;

application = Flask(__name__);
application.config.from_object(Configuration);
jwt = JWTManager(application);

@application.route("/register", methods=["POST"])
def register():
    if (request.json is None):
        return Response(json.dumps({
            "message": "Field jmbg is missing."
        }, indent=4), status=400);

    jmbg = request.json.get("jmbg", "");
    forename = request.json.get("forename", "");
    surname = request.json.get("surname", "");
    email = request.json.get("email", "");
    password = request.json.get("password", "");

    if (len(jmbg) == 0):
        return Response(json.dumps({
            "message": "Field jmbg is missing."
        }, indent=4), status=400);
    if (len(forename) == 0):
        return Response(json.dumps({
            "message": "Field forename is missing."
        }, indent=4), status=400);
    if (len(surname) == 0):
        return Response(json.dumps({
            "message": "Field surname is missing."
        }, indent=4), status=400);
    if (len(email) == 0):
        return Response(json.dumps({
            "message": "Field email is missing."
        }, indent=4), status=400);
    if (len(password) == 0):
        return Response(json.dumps({
            "message": "Field password is missing."
        }, indent=4), status=400);

    if (not validJMBG(jmbg)):
        return Response(json.dumps({
            "message": "Invalid jmbg."
        }, indent=4), status=400);

    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    if (not re.fullmatch(regex, email)):
        return Response(json.dumps({
            "message": "Invalid email."
        }, indent=4), status=400);

    # if (len(parseaddr(email)[1]) == 0):
    #     return Response(json.dumps({
    #         "message": "Invalid email."
    #     }, indent=4), status=400);

    if (not validPassword(password)):
        return Response(json.dumps({
            "message": "Invalid password."
        }, indent=4), status=400);

    alreadyExists = User.query.filter(or_(
        User.email == email, User.jmbg == jmbg
    )).first();
    if (alreadyExists):
        return Response(json.dumps({
            "message": "Email already exists."
        }, indent=4), status=400);
    officialRole = Role.query.filter(Role.name == "official").first();
    user = User(forename=forename, surname=surname, email=email, password=password, roleId=officialRole.id, jmbg=jmbg);
    database.session.add(user);
    database.session.commit();

    return Response(status=200);


@application.route("/login", methods=["POST"])
def login():
    if (request.json is None):
        return Response(json.dumps({
            "message": "Field email is missing."
        }, indent=4), status=400);

    email = request.json.get("email", "");
    password = request.json.get("password", "");

    if (len(email) == 0):
        return Response(json.dumps({
            "message": "Field email is missing."
        }, indent=4), status=400);
    if (len(password) == 0):
        return Response(json.dumps({
            "message": "Field password is missing."
        }, indent=4), status=400);

    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # if (len(parseaddr(email)[1]) == 0):
    #     return Response(json.dumps({
    #         "message": "Invalid email."
    #     }, indent=4), status=400);

    if (not re.fullmatch(regex, email)):
        return Response(json.dumps({
            "message": "Invalid email."
        }, indent=4), status=400);

    user = User.query.filter(and_(User.email == email, User.password == password)).first();

    if (not user):
        return Response(json.dumps({
            "message": "Invalid credentials."
        }, indent=4), status=400);

    userRole = Role.query.filter(Role.id == user.roleId).first();

    additionClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "role": userRole.name,
        "jmbg": user.jmbg
    }

    tokens = {
        "accessToken": create_access_token(identity=user.email, additional_claims=additionClaims),
        "refreshToken": create_refresh_token(identity=user.email, additional_claims=additionClaims)
    };

    return Response(json.dumps(tokens, indent=4), status=200);

@application.route("/delete", methods=["POST"])
@roleCheck(role="admin")
def delete():
    print("ulazak delete\n");
    if (request.json is None):
        return Response(json.dumps({
            "message": "Field email is missing."
        }, indent=4), status=400);

    email = request.json.get("email", "");

    if (len(email) == 0):
        return Response(json.dumps({
            "message": "Field email is missing."
        }, indent=4), status=400);

    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # if (len(parseaddr(email)[1]) == 0):
    #     return Response(json.dumps({
    #         "message": "Invalid email."
    #     }, indent=4), status=400);

    if (not re.fullmatch(regex, email)):
        return Response(json.dumps({
            "message": "Invalid email."
        }, indent=4), status=400);

    print("email je: " + email + "\n");

    user = User.query.filter(User.email == email).first();

    if (user):
        print("pronasao user-a, id: " + str(user.id));

    if (not user):
        return Response(json.dumps({
            "message": "Unknown user."
        }, indent=4), status=400);

    User.query.filter(User.email == email).delete();
    database.session.commit()

    print("korisnik obrisan!");

    return Response(status=200);


@application.route("/check", methods=["POST"])
@jwt_required()
def check():
    return "Token is valid!";

@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity();
    refreshClaims = get_jwt();

    additionClaims = {
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "role": refreshClaims["role"],
        "jmbg": refreshClaims["jmbg"]
    }

    return Response(json.dumps({
        "accessToken": create_access_token(identity=identity, additional_claims=additionClaims)
    }, indent=4), status=200);

def validJMBG(jmbg):
    if (len(jmbg) != 13): return False;
    dd = int(jmbg[0:2]);
    if (dd < 1 or dd > 31): return False;
    mm = int(jmbg[2:4]);
    if (mm < 1 or mm > 12): return False;
    yyy = int(jmbg[4:7]);
    if (yyy < 0 or yyy > 999): return False;
    rr = int(jmbg[7:9]);
    if (rr < 70 or rr > 99): return False;
    bbb = int(jmbg[9:12]);
    if (bbb < 0 or bbb > 999): return False;
    if (int(jmbg[12]) != jmbgChecksum(jmbg)): return False;
    return True;

def jmbgChecksum(jmbg):
    m =  11 - ((7 * (int(jmbg[0]) + int(jmbg[6])) + 6 * (int(jmbg[1]) + int(jmbg[7])) + 5 * (int(jmbg[2]) +
        int(jmbg[8])) + 4 * (int(jmbg[3]) + int(jmbg[9])) + 3 * (int(jmbg[4]) + int(jmbg[10])) + 2 * (int(jmbg[5]) +
        int(jmbg[11]))) % 11);
    if (m >= 1 and m <= 9): return m;
    return 0;

def validPassword(password):
    if (len(password) < 8): return False;
    hasDigit = False;
    hasLowerCase = False;
    hasUpperCase = False;
    for char in password:
        if (char.isdigit()):
            hasDigit = True;
            continue;
        if (char.islower ()):
            hasLowerCase = True;
            continue;
        if (char.isupper()):
            hasUpperCase = True;
            continue;
    if (hasDigit and hasLowerCase and hasUpperCase): return True;
    return False;

if (__name__ == "__main__"):
    database.init_app(application);
    application.run(debug=True, host="0.0.0.0", port=5002); # deployment: host="0.0.0.0" ; development: host - default




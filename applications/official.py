from flask import Flask, request, Response;
from configuration import Configuration;
from models import database;
from authorizationDecorator import roleCheck;
from flask_jwt_extended import JWTManager, get_jwt;
from redis import Redis;
import csv;
import io;
import json;


application = Flask(__name__);
application.config.from_object(Configuration);
jwt = JWTManager(application);


@application.route("/vote", methods=["POST"])
@roleCheck(role="official")
def vote():
    if (request.files is None):
        return Response(json.dumps({
            "message": "Field file is missing."
        }, indent=4), status=400);

    file = request.files.get("file", None);

    if (file == None):
        return Response(json.dumps({
            "message": "Field file is missing."
        }, indent=4), status=400);

    bin_data = file.stream.read();

    officialJMBG = get_jwt()["jmbg"];

    # content = bin_data.decode();
    # stream = io.StringIO(content);
    # reader = csv.reader(stream);
    reader = None;
    try:
        reader = csv.reader(io.StringIO(bin_data.decode()));
    except Exception:
        return Response(json.dumps({
            "message": "Field file is missing."
        }, indent=4), status=400);
    if (reader is None):
        return Response(json.dumps({
            "message": "Field file is missing."
        }, indent=4), status=400);

    votes = [];
    lineCounter = 0;
    # next(reader, None);
    for line in reader:
        # print(line[0] + "---" + line[1]);
        if (len(line) != 2):
            print("greska broj parametara");
            return Response(json.dumps({
                "message": "Incorrect number of values on line " + str(lineCounter) + "."
            }, indent=4), status=400);
        # print(line[0] + "---" + line[1]);
        try:
            if (int(line[1]) <= 0):
                print("greska invalid poll number");
                return Response(json.dumps({
                    "message": "Incorrect poll number on line " + str(lineCounter) + "."
                }, indent=4), status=400);
        except Exception:
            return Response(json.dumps({
                "message": "Incorrect poll number on line " + str(lineCounter) + "."
            }, indent=4), status=400);

        votes.append(",".join(line));
        lineCounter += 1;

    with Redis(host=Configuration.REDIS_HOST) as redis:
        for vt in votes:
            vt = vt + "," + officialJMBG;
            redis.rpush(Configuration.REDIS_VOTE_LIST, vt);

    return Response(status=200);



if (__name__ == "__main__"):
    database.init_app(application);
    application.run(debug=True, host="0.0.0.0", port=5001); # deployment: host="0.0.0.0" ; development: host - default
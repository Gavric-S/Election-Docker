import copy;
import json;
from dateutil.tz import gettz;
from dateutil.parser import isoparse;
# from datetime import *;
import datetime;
from copy import deepcopy;
from flask import Flask, request, Response;
from sqlalchemy import and_, or_;
from configuration import Configuration;
from models import database, Candidate, Election, IsRunning, Vote;
from authorizationDecorator import roleCheck;
from flask_jwt_extended import JWTManager;


application = Flask(__name__);
application.config.from_object(Configuration);
jwt = JWTManager(application);


@application.route("/createParticipant", methods=["POST"])
@roleCheck(role="admin")
def createParticipant():
    if (request.json is None):
        return Response(json.dumps({
            "message": "Field name is missing."
        }, indent=4), status=400);

    name = request.json.get("name", "");
    individual = request.json.get("individual", None);

    if (len(name) == 0):
        return Response(json.dumps({
            "message": "Field name is missing."
        }, indent=4), status=400);
    if (individual == None):
        return Response(json.dumps({
            "message": "Field individual is missing."
        }, indent=4), status=400);

    candidate = Candidate(name=name, individual=individual);
    database.session.add(candidate);
    database.session.commit();

    return Response(json.dumps({
        "id": str(candidate.id)
    }, indent=4), status=200);

@application.route("/getParticipants", methods=["GET"])
@roleCheck(role="admin")
def getParticipants():
    candidates = [candidate.as_dict() for candidate in Candidate.query.all()];

    return Response(json.dumps({
        "participants": candidates
    }, indent=4), status=200);


@application.route("/createElection", methods=["POST"])
@roleCheck(role="admin")
def createElection():
    if (request.json is None):
        return Response(json.dumps({
            "message": "Field start is missing."
        }, indent=4), status=400);

    start = request.json.get("start", "");
    end = request.json.get("end", "");
    individual = request.json.get("individual", None);
    participants = request.json.get("participants", None);

    if (len(start) == 0):
        return Response(json.dumps({
            "message": "Field start is missing."
        }, indent=4), status=400);
    if (len(end) == 0):
        return Response(json.dumps({
            "message": "Field end is missing."
        }, indent=4), status=400);
    if (individual == None):
        return Response(json.dumps({
            "message": "Field individual is missing."
        }, indent=4), status=400);
    if (participants == None):
        return Response(json.dumps({
            "message": "Field participants is missing."
        }, indent=4), status=400);


    try:
        start_time = isoparse(start);
        end_time = isoparse(end);
    except Exception:
        return Response(json.dumps({
            "message": "Invalid date and time."
        }, indent=4), status=400);

    if (start > end):
        return Response(json.dumps({
            "message": "Invalid date and time."
        }, indent=4), status=400);


    if (Election.query.filter(or_(
        and_(Election.start_time > start_time, Election.start_time < end_time)
        ,
        and_(Election.end_time > start_time, Election.end_time < end_time)
    )).first()):
        return Response(json.dumps({
            "message": "Invalid date and time."
        }, indent=4), status=400);

    validParticipants = True;
    if (len(participants) < 2):
        return Response(json.dumps({
            "message": "Invalid participants."
        }, indent=4), status=400);
    for candidateId in participants:
        candidate = Candidate.query.filter(Candidate.id == candidateId).first();
        if (not candidate or (candidate.individual != individual)):
            return Response(json.dumps({
                "message": "Invalid participants."
            }, indent=4), status=400);

    election = Election(start_time=start_time, end_time=end_time, individual=individual);
    database.session.add(election);
    database.session.commit();

    runningParticipants = [];
    for i in range(0, len(participants)):
        isRunning = IsRunning(candidateId=participants[i], electionId=election.id, pollNumber=i+1);
        runningParticipants.append(isRunning);
    database.session.add_all(runningParticipants);
    database.session.commit();

    return Response(json.dumps({
        "pollNumbers": list(range(1, len(participants) + 1))
    }, indent=4), status=200);


@application.route("/getElections", methods=["GET"])
@roleCheck(role="admin")
def getElections():
    elections = [election.as_dict() for election in Election.query.all()];
    return Response(json.dumps({
        "elections": elections
    }, indent=4), status=200);


@application.route("/getResults", methods=["GET"])
@roleCheck(role="admin")
def getResults():
    if (request.args is None):
        return Response(json.dumps({
            "message": "Field id is missing."
        }, indent=4), status=400);

    election_id = request.args.get("id");
    if (not election_id or election_id == ""):
        return Response(json.dumps({
            "message": "Field id is missing."
        }, indent=4), status=400);

    election_id = int(election_id);
    election = Election.query.filter(Election.id == election_id).first();
    if (not election):
        return Response(json.dumps({
            "message": "Election does not exist."
        }, indent=4), status=400);

    # if (datetime.now() < election.end_time): TODO VRATITI
    if (datetime.datetime.now() + datetime.timedelta(hours = 2) < election.end_time):
        return Response(json.dumps({
            "message": "Election is ongoing."
        }, indent=4), status=400);

    participants = IsRunning.query.filter(
                IsRunning.electionId == election_id
    ).all();

    votesPerParticipant = [];
    votesInTotal = 0;
    participantNames = [];
    for participant in participants:
        voteCount = Vote.query.filter(and_(
            Vote.electionId == election_id, Vote.pollNumber == participant.pollNumber,
            Vote.reason == None)).count();
        participantNames.append(Candidate.query.filter(Candidate.id == participant.candidateId).first().name)
        votesPerParticipant.append(voteCount);
        votesInTotal += voteCount;

    results = [];
    if (election.individual): # predsednicki izbori
        results = countTheVotesPresidential(votesPerParticipant=votesPerParticipant, votesInTotal=votesInTotal);


    else: # parlamentarni izbori
        results = countTheVotesDHondt(votesPerParticipant=votesPerParticipant, votesInTotal=votesInTotal, numOfParticipants=len(participants));

    for i in range(0, len(participants)):
        participants[i] = {
            "pollNumber": participants[i].pollNumber,
            "name": participantNames[i],
            "result": results[i]
        }

    invalidVotes = getInvalidVotes(election_id);

    return Response(json.dumps({
        "participants": participants,
        "invalidVotes": invalidVotes
    }, indent=4), status=200);

def countTheVotesPresidential(votesPerParticipant, votesInTotal):
    results = [0] * len(votesPerParticipant);
    for i in range(0, len(votesPerParticipant)):
        if (votesInTotal == 0):
            results[i] = round(0.00, 2);
        else:
            results[i] = round(votesPerParticipant[i] / votesInTotal, 2);
    return results;

def countTheVotesDHondt(votesPerParticipant, votesInTotal, numOfParticipants):
    census = 0.05;
    seatCount = 250;

    # indMax = votesPerParticipant.index(max(votesPerParticipant));
    for i in range(0, len(votesPerParticipant)):
        if (votesPerParticipant[i] <= census * votesInTotal):
            # votesPerParticipant[indMax] += votesPerParticipant[i];
            votesPerParticipant[i] = 0;

    results = [0] * len(votesPerParticipant);
    remainingVotes = copy.deepcopy(votesPerParticipant);
    for i in range(0, seatCount):
        indMax = remainingVotes.index(max(remainingVotes));
        results[indMax] += 1;
        remainingVotes[indMax] = votesPerParticipant[indMax] / (results[indMax] + 1);
    return results;

def getInvalidVotes(election_id):
    invalidVotes = [vote.as_dict() for vote in Vote.query.filter(and_(
        Vote.electionId == election_id, Vote.reason != None
    )).all()];
    return invalidVotes;


if (__name__ == "__main__"):
    database.init_app(application);
    application.run(debug=True, host="0.0.0.0", port=5000); # deployment: host="0.0.0.0" ; development: host - default


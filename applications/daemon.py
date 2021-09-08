from flask import Flask, request, Response;
from configuration import Configuration;
from models import database, Election, Vote, IsRunning;
from sqlalchemy import and_, or_;
from redis import Redis;
import dateutil;
# from datetime import *;
import datetime;

application = Flask(__name__);
application.config.from_object(Configuration);
database.init_app(application);

with application.app_context() as context:
    with Redis(host=Configuration.REDIS_HOST) as redis:
        while (True):
            bytes = redis.lpop(Configuration.REDIS_VOTE_LIST);
            if (bytes == None): continue;
            vote = bytes.decode("utf-8").split(",");
            guid = vote[0];
            pollNumber = vote[1];
            officialJMBG = vote[2];

            # election = Election.query.filter(and_( TODO: vratiti
            #         Election.start_time < datetime.now(), datetime.now() < Election.end_time
            # )).first();
            election = Election.query.filter(and_(
                Election.start_time < datetime.datetime.now() + datetime.timedelta(hours = 2), datetime.datetime.now() + datetime.timedelta(hours = 2) < Election.end_time
            )).first();
            if (not election): continue;
            already_exists = Vote.query.filter(Vote.ballotGuid == guid).first();
            if (already_exists):
                invalidVote = Vote(ballotGuid=guid, electionOfficialJmbg=officialJMBG, pollNumber=pollNumber, electionId=election.id, reason="Duplicate ballot.");
                database.session.add(invalidVote);
                database.session.commit();
                continue;

            validPoll = IsRunning.query.filter(and_(
                IsRunning.electionId == election.id, IsRunning.pollNumber == pollNumber
            )).first();
            if (not validPoll):
                invalidVote = Vote(ballotGuid=guid, electionOfficialJmbg=officialJMBG, pollNumber=pollNumber,
                                   electionId=election.id, reason="Invalid poll number.");
                database.session.add(invalidVote);
                database.session.commit();
                continue;

            validVote = Vote(ballotGuid=guid, electionOfficialJmbg=officialJMBG, pollNumber=pollNumber, electionId=election.id);
            database.session.add(validVote);
            database.session.commit();



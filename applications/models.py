import json;
from flask_sqlalchemy import SQLAlchemy;

database = SQLAlchemy();


class IsRunning(database.Model):
    __tablename__ = "isRunning";
    id = database.Column(database.Integer, primary_key=True);
    candidateId = database.Column(database.Integer, database.ForeignKey("candidates.id"), nullable=False);
    electionId = database.Column(database.Integer, database.ForeignKey("elections.id"), nullable=False);
    pollNumber = database.Column(database.Integer, nullable=False);

class Candidate(database.Model):
    __tablename__ = "candidates";
    id = database.Column(database.Integer, primary_key=True);
    name = database.Column(database.String(256), nullable=False);
    individual = database.Column(database.Boolean, nullable=False);

    elections = database.relationship("Election", secondary=IsRunning.__table__, back_populates="candidates");

    # def __repr__(self):
    #     return json.dumps({
    #         "id": self.id,
    #         "name": self.name,
    #         "individual": self.individual
    #     }, indent=4);

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "individual": self.individual
        };

class Election(database.Model):
    __tablename__ = "elections";
    id = database.Column(database.Integer, primary_key=True);
    start_time = database.Column(database.DateTime, nullable=False);
    end_time = database.Column(database.DateTime, nullable=False);
    individual = database.Column(database.Boolean, nullable=False);

    candidates = database.relationship("Candidate", secondary=IsRunning.__table__, back_populates="elections");

    def as_dict(self):
        participant_ids = [isRunning.candidateId for isRunning in IsRunning.query.filter(
            IsRunning.electionId == self.id
        ).all()];

        participants = [];
        for participantId in participant_ids:
            participant = Candidate.query.filter(Candidate.id == participantId).first();
            participants.append({
                "id": participant.id,
                "name": participant.name
            });

        dict = {
            "id": self.id,
            "start": self.start_time.isoformat(),
            "end": self.end_time.isoformat(),
            "individual": self.individual,
            "participants": participants
        }
        return dict;


class Vote(database.Model):
    __tablename__ = "votes";
    id = database.Column(database.Integer, primary_key=True);
    ballotGuid = database.Column(database.String(36), nullable=False);
    electionOfficialJmbg = database.Column(database.String(13), nullable=False);
    pollNumber = database.Column(database.Integer, nullable=False);

    electionId = database.Column(database.Integer, database.ForeignKey("elections.id"), nullable=False);
    reason = database.Column(database.String(256), nullable=True);

    def as_dict(self):
        return {
            "electionOfficialJmbg": self.electionOfficialJmbg,
            "ballotGuid": self.ballotGuid,
            "pollNumber": self.pollNumber,
            "reason": self.reason
        };
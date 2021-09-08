from flask_sqlalchemy import SQLAlchemy;

database = SQLAlchemy();


class User(database.Model):
    __tablename__ = "users";

    id = database.Column(database.Integer, primary_key=True);
    jmbg = database.Column(database.String(13), nullable=False, unique=False);
    email = database.Column(database.String(256), nullable=False, unique=True);
    password = database.Column(database.String(256), nullable=False);
    forename = database.Column(database.String(256), nullable=False);
    surname = database.Column(database.String(256), nullable=False);
    # role = database.Column(database.Integer, database.ForeignKey("roles.id"), nullable=False);
    # parent = database.relationship("Role", back_populates="users");

    # roleId = database.Column(database.Integer, database.ForeignKey('roles.id'), nullable=False);
    # role = database.relationship("Role");

    roleId = database.Column(database.Integer, database.ForeignKey('roles.id'), nullable=False);

class Role(database.Model):
    __tablename__ = "roles";

    id = database.Column(database.Integer, primary_key=True);
    name = database.Column(database.String(256), nullable=False);

    def __repr__(self):
        return self.name;

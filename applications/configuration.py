import os;

dbURL = os.environ["DATABASE_URL"];

# redisURL = os.environ["REDIS_URL"];

class Configuration():
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{dbURL}/elections";
    # SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@localhost/elections";
    REDIS_HOST = "redis"; # deployment: redis ; development: localhost
    REDIS_VOTE_LIST = "votes";
    JWT_SECRET_KEY = "JWT_SECRET_KEY";
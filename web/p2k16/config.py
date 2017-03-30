import os

def from_env(app=None):
    print("Loading config from environment")

    if os.getenv('P2K16_DB_URL') is not None:
        db_url = os.getenv('P2K16_DB_URL')
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        print("Found env variable P2K16_DB_URL = {}".format(db_url))

    if os.getenv('SECRET_KEY') is not None:
        secret_key = os.getenv('SECRET_KEY')
        app.config['SECRET_KEY'] = secret_key
        print("Found env variable SECRET_KEY = {}".format(secret_key))

    return app
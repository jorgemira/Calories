import os

import connexion
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))

# Create the connexion application instance
connex_app = connexion.App(__name__, specification_dir=basedir)

# Get the underlying Flask app instance
app = connex_app.app

# Build the Sqlite ULR for SqlAlchemy
# sqlite_url = "sqlite:////" + os.path.join(basedir, "calories.db")
url = 'localhost'
user = 'jorge'
pw = 'jorge_password'
db = 'calories'

db_url = f'postgresql+psycopg2://{user}:{pw}@{url}/{db}'
# Configure the SqlAlchemy part of the app instance
app.config["SQLALCHEMY_ECHO"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Create the SqlAlchemy db instance
db = SQLAlchemy(app)

# Initialize Marshmallow
ma = Marshmallow(app)

import os

import connexion
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy

from .config import config_by_name, basedir

db = SQLAlchemy()
ma = Marshmallow()
cfg = config_by_name[os.getenv('CLS_ENV') or 'dev']
logger = None


def create_app():
    global logger
    # Create the connexion application instance
    connex_app = connexion.App(__name__, specification_dir=basedir, options={"swagger_ui": cfg.SWAGGER_UI})

    # Get the underlying Flask app instance
    app = connex_app.app

    app.config.from_object(cfg)
    db.init_app(app)
    ma.init_app(app)
    logger = app.logger

    connex_app.add_api("swagger.yml", strict_validation=True, validate_responses=True)

    return connex_app

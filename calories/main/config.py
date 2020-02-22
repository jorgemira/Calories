import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEBUG = False
    TOKEN_SECRET_KEY = os.getenv('TOKEN_SECRET_KEY', '*&UbA>>D5nj6S_6KaIp*$5sppQS-B')
    TOKEN_LIFETIME_SECONDS = os.getenv('TOKEN_LIFETIME_SECONDS', 1800)
    NTX_BASE_URL = os.getenv('NTX_BASE_URL', 'https://api.nutritionix.com/v1_1')
    NTX_APP_ID = os.getenv('NTX_APP_ID', '29787544')
    NTX_API_KEY = os.getenv('NTX_API_KEY', 'e0ecc4ea5307e6392caba2dd9023085f')
    SWAGGER_UI = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'flask_calories_main.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SWAGGER_UI = True

class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'flask_calories_test.db')
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False
    _PG_USER = os.getenv('PG_USER', 'my_user')
    _PG_PWD = os.getenv('PG_PWD', 'my_password')
    _PG_URL = os.getenv('PG_URL', 'localhost')
    _PG_DB = os.getenv('PG_DB', 'calories')
    SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{_PG_USER}:{_PG_PWD}@{_PG_URL}/{_PG_DB}'
    SQLALCHEMY_ECHO = False


config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    prod=ProductionConfig
)

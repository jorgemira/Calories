from flask_testing import TestCase

from calories.main import db
from calories.main.build_database import build_db, populate_db
from manage import app


class BaseTestCase(TestCase):
    """ Base Tests """

    def create_app(self):
        app.config.from_object("calories.main.config.TestingConfig")
        return app

    def setUp(self):
        build_db()
        populate_db()

    def tearDown(self):
        db.session.remove()

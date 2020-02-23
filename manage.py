import unittest

from flask_script import Manager

from calories.deploy import gunicorn
from calories.main import build_database
from calories.main import create_app, cfg

connex_app = create_app()

app = connex_app.app

app.app_context().push()

manager = Manager(app)


@manager.command
def build_db():
    """Build the database"""
    build_database.build_db()


@manager.command
def run():
    """Run the app"""
    if cfg.__name__ == 'ProductionConfig':
        gunicorn.run(connex_app)
    else:
        connex_app.run(port=cfg.PORT)


@manager.command
def test():
    """Run the unit tests."""
    tests = unittest.TestLoader().discover('calories/test', pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1


if __name__ == '__main__':
    manager.run()

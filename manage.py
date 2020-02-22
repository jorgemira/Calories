import unittest

from flask_script import Manager

from calories.main import build_database
from calories.main import create_app

connex_app = create_app()

app = connex_app.app

app.app_context().push()

manager = Manager(app)


@manager.command
def build_db():
    build_database.build_db()


@manager.command
def run():
    connex_app.run()


@manager.command
def test():
    """Runs the unit tests."""
    tests = unittest.TestLoader().discover('calories/test', pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1


if __name__ == '__main__':
    manager.run()

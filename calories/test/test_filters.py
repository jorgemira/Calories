import unittest

from fiql_parser import FiqlException
from sqlalchemy_filters.exceptions import InvalidPage, FieldNotFound
from werkzeug.exceptions import BadRequest

from calories.main.models.models import User
from calories.main.util.filters import apply_filter
from calories.test.base import BaseTestCase


class TestExternalAPIs(BaseTestCase):
    def test_filters(self):
        users = User.query.order_by(User.username)

        # Test Filtering
        filtered = apply_filter(users, 'username eq user1').all()
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].username, 'user1')

        filtered = apply_filter(users, 'username ne user1').all()
        self.assertEqual(len(filtered), 4)
        self.assertEqual(filtered[0].username, 'admin')
        self.assertEqual(filtered[1].username, 'manager1')
        self.assertEqual(filtered[2].username, 'manager2')
        self.assertEqual(filtered[3].username, 'user2')

        filtered = apply_filter(users, "username ne 'user1' AND daily_calories lt 2000").all()
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].username, 'admin')

        filtered = apply_filter(users, "username ne 'user1' AND (daily_calories lt 3000 AND daily_calories gt 1000)").all()
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].username, 'manager1')

        filtered = apply_filter(users, "username eq 'wronguser'").all()
        self.assertEqual(len(filtered), 0)

        with self.assertRaises(BadRequest):
            apply_filter(users, "wrongfield eq 'wronguser'").all()

        with self.assertRaises(BadRequest):
            apply_filter(users, "wrongfilter").all()

        # Test pagination
        filtered = apply_filter(users, page_number=1, page_size=2).all()
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].username, 'admin')
        self.assertEqual(filtered[1].username, 'manager1')

        filtered = apply_filter(users, page_number=2, page_size=2).all()
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].username, 'manager2')
        self.assertEqual(filtered[1].username, 'user1')

        filtered = apply_filter(users, page_number=3, page_size=2).all()
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].username, 'user2')

        filtered = apply_filter(users, page_number=4, page_size=2).all()
        self.assertEqual(len(filtered), 0)

        with self.assertRaises(InvalidPage):
            apply_filter(users, page_number=0, page_size=2)


if __name__ == '__main__':
    unittest.main()

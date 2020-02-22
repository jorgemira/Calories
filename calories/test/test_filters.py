import unittest

from sqlalchemy_filters.exceptions import InvalidPage
from werkzeug.exceptions import BadRequest

from calories.main.models.models import User
from calories.main.util.filters import apply_filter
from calories.test.base import BaseTestCase


class TestExternalAPIs(BaseTestCase):
    def test_filters(self):
        users = User.query.order_by(User.username)

        # Test Filtering
        query, pagination = apply_filter(users, 'username eq user1')
        filtered = query.all()
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].username, 'user1')
        self.assertEqual(pagination.num_pages, 1)
        self.assertEqual(pagination.total_results, 1)

        query, pagination = apply_filter(users, 'username ne user1')
        filtered = query.all()
        self.assertEqual(len(filtered), 4)
        self.assertEqual(filtered[0].username, 'admin')
        self.assertEqual(filtered[1].username, 'manager1')
        self.assertEqual(filtered[2].username, 'manager2')
        self.assertEqual(filtered[3].username, 'user2')
        self.assertEqual(pagination.num_pages, 1)
        self.assertEqual(pagination.total_results, 4)

        query, pagination = apply_filter(users, "username ne 'user1' AND daily_calories lt 2000")
        filtered = query.all()
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].username, 'admin')
        self.assertEqual(pagination.num_pages, 1)
        self.assertEqual(pagination.total_results, 1)

        query, pagination = apply_filter(users, "username ne 'user1' AND (daily_calories lt 3000 AND daily_calories "
                                                "gt 1000)")
        filtered = query.all()
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].username, 'manager1')
        self.assertEqual(pagination.num_pages, 1)
        self.assertEqual(pagination.total_results, 1)

        query, pagination = apply_filter(users, "username eq 'wronguser'")
        filtered = query.all()
        self.assertEqual(len(filtered), 0)
        self.assertEqual(pagination.num_pages, 0)
        self.assertEqual(pagination.total_results, 0)

        with self.assertRaises(BadRequest):
            apply_filter(users, "wrongfield eq 'wronguser'")

        with self.assertRaises(BadRequest):
            apply_filter(users, "wrongfilter")

        # Test pagination
        query, pagination = apply_filter(users, page_number=1, page_size=2)
        filtered = query.all()
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].username, 'admin')
        self.assertEqual(filtered[1].username, 'manager1')
        self.assertEqual(pagination.num_pages, 3)
        self.assertEqual(pagination.total_results, 5)

        query, pagination = apply_filter(users, page_number=2, page_size=2)
        filtered = query.all()
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].username, 'manager2')
        self.assertEqual(filtered[1].username, 'user1')
        self.assertEqual(pagination.num_pages, 3)
        self.assertEqual(pagination.total_results, 5)

        query, pagination = apply_filter(users, page_number=3, page_size=2)
        filtered = query.all()
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].username, 'user2')
        self.assertEqual(pagination.num_pages, 3)
        self.assertEqual(pagination.total_results, 5)

        query, pagination = apply_filter(users, page_number=4, page_size=2)
        filtered = query.all()
        self.assertEqual(len(filtered), 0)
        self.assertEqual(pagination.num_pages, 3)
        self.assertEqual(pagination.total_results, 5)

        with self.assertRaises(InvalidPage):
            apply_filter(users, page_number=0, page_size=2)


if __name__ == '__main__':
    unittest.main()

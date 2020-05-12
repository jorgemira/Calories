"""Test module for calories.main.util.filters"""

import unittest

from sqlalchemy_filters.exceptions import InvalidPage
from werkzeug.exceptions import BadRequest

from calories.main.models.models import User
from calories.main.util.filters import apply_filter
from calories.test import BaseTestCase


class TestExternalAPIs(BaseTestCase):
    """Test class for calories.main.util.filters"""

    def setUp(self):
        super().setUp()
        self.users = User.query.order_by(User.username)

    def test_filters_eq(self):
        """Test filtering eq operator"""
        query, pagination = apply_filter(self.users, "username eq user1")
        filtered = query.all()
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].username, "user1")
        self.assertEqual(pagination.num_pages, 1)
        self.assertEqual(pagination.total_results, 1)

    def test_filters_ne(self):
        """Test filtering ne operator"""
        query, pagination = apply_filter(self.users, "username ne user1")
        filtered = query.all()
        self.assertEqual(len(filtered), 4)
        self.assertEqual(filtered[0].username, "admin")
        self.assertEqual(filtered[1].username, "manager1")
        self.assertEqual(filtered[2].username, "manager2")
        self.assertEqual(filtered[3].username, "user2")
        self.assertEqual(pagination.num_pages, 1)
        self.assertEqual(pagination.total_results, 4)

    def test_filters_and(self):
        """Test filtering and operator"""
        query, pagination = apply_filter(
            self.users, "username ne 'user1' AND daily_calories lt 2000"
        )
        filtered = query.all()
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].username, "admin")
        self.assertEqual(pagination.num_pages, 1)
        self.assertEqual(pagination.total_results, 1)

    def test_filters_complex(self):
        """Test filtering with complex filter"""
        query, pagination = apply_filter(
            self.users,
            "username ne 'user1' AND (daily_calories lt 3000 AND "
            "daily_calories gt 1000)",
        )
        filtered = query.all()
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].username, "manager1")
        self.assertEqual(pagination.num_pages, 1)
        self.assertEqual(pagination.total_results, 1)

    def test_filters_no_results(self):
        """Test filtering returning no results"""
        query, pagination = apply_filter(self.users, "username eq 'wronguser'")
        filtered = query.all()
        self.assertEqual(len(filtered), 0)
        self.assertEqual(pagination.num_pages, 0)
        self.assertEqual(pagination.total_results, 0)

    def test_filters_wrong_field(self):
        """Test filtering providing wrong fields"""
        with self.assertRaises(BadRequest):
            apply_filter(self.users, "wrongfield eq 'wronguser'")

    def test_filters_wrong_filter(self):
        """Test filtering providing wrong filters"""
        with self.assertRaises(BadRequest):
            apply_filter(self.users, "wrongfilter")

    def test_pagination_1_2(self):
        """Test pagination page_number=1 and page_size=2"""
        query, pagination = apply_filter(self.users, page_number=1, page_size=2)
        filtered = query.all()
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].username, "admin")
        self.assertEqual(filtered[1].username, "manager1")
        self.assertEqual(pagination.num_pages, 3)
        self.assertEqual(pagination.total_results, 5)

    def test_pagination_2_2(self):
        """Test pagination page_number=2 and page_size=2"""
        query, pagination = apply_filter(self.users, page_number=2, page_size=2)
        filtered = query.all()
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].username, "manager2")
        self.assertEqual(filtered[1].username, "user1")
        self.assertEqual(pagination.num_pages, 3)
        self.assertEqual(pagination.total_results, 5)

    def test_pagination_3_2(self):
        """Test pagination page_number=3 and page_size=2"""
        query, pagination = apply_filter(self.users, page_number=3, page_size=2)
        filtered = query.all()
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].username, "user2")
        self.assertEqual(pagination.num_pages, 3)
        self.assertEqual(pagination.total_results, 5)

    def test_pagination_4_2(self):
        """Test pagination page_number=4 and page_size=2"""
        query, pagination = apply_filter(self.users, page_number=4, page_size=2)
        filtered = query.all()
        self.assertEqual(len(filtered), 0)
        self.assertEqual(pagination.num_pages, 3)
        self.assertEqual(pagination.total_results, 5)

    def test_pagination_0_2(self):
        """Test pagination invalid page_number=0 and page_size=2"""
        with self.assertRaises(InvalidPage):
            apply_filter(self.users, page_number=0, page_size=2)


if __name__ == "__main__":
    unittest.main()

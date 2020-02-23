import unittest
from unittest.mock import patch

from requests import ConnectionError

from calories.main.util.external_apis import calories_from_nutritionix
from calories.test.base import BaseTestCase


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if args[0] == 'https://api.nutritionix.com/v1_1/search/pizza':
        return MockResponse({'total_hits': 26947, 'hits': [{'fields': {'item_id': 'pizza_id'}}]}, 200)
    elif args[0] == 'https://api.nutritionix.com/v1_1/search/custard':
        raise ValueError('Wrong JSON')
    elif args[0] == 'https://api.nutritionix.com/v1_1/search/tomatoes':
        return MockResponse({'plan': 'Hacker Plan (Free)', 'error_code': None,
                             'error_message': 'application key "XXX" is invalid', 'status_code': 409}, 409)
    elif args[0] == 'https://api.nutritionix.com/v1_1/search/icecream':
        return MockResponse({'total_hits': 26947, 'hits': [{'fields': {'item_id': 'icecream_id'}}]}, 200)
    elif args[0] == 'https://api.nutritionix.com/v1_1/item':
        if kwargs['params']['id'] == 'pizza_id':
            return MockResponse({'nf_calories': 2268.98}, 200)
        if kwargs['params']['id'] == 'icecream_id':
            raise ConnectionError

    return MockResponse(None, 404)


class TestExternalAPIs(BaseTestCase):

    @patch('requests.get')
    def test_calories_from_nutritionix_success(self, mock_get):
        """Successful request"""
        mock_get.side_effect = mocked_requests_get
        self.assertEqual(calories_from_nutritionix('pizza'), 2268.98)

    @patch('requests.get')
    def test_calories_from_nutritionix_wrong_JSON(self, mock_get):
        """Server returns wrong JSON"""
        mock_get.side_effect=mocked_requests_get
        self.assertEqual(calories_from_nutritionix('custard'), 0)

    @patch('requests.get')
    def test_calories_from_nutritionix_wrong_API_key(self, mock_get):
        """Wrong API key"""
        mock_get.side_effect = mocked_requests_get
        self.assertEqual(calories_from_nutritionix('tomatoes'), 0)

    @patch('requests.get')
    def test_calories_from_nutritionix_connection_error(self, mock_get):
        """Connection error"""
        mock_get.side_effect = mocked_requests_get
        self.assertEqual(calories_from_nutritionix('icecream'), 0)


if __name__ == '__main__':
    unittest.main()

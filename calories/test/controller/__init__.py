import json
import unittest
from typing import Dict, Union, List, Any
from urllib.parse import quote

from calories.test import BaseTestCase

HeaderType = Dict[str, str]


class TestAPI(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.path = 'api'

    def delete(self, path: str, headers: HeaderType = None):
        return self.client.delete(path, content_type='application/json', headers=headers)

    def get(self, path: str, headers: HeaderType = None):
        return self.client.get(path, content_type='application/json', headers=headers)

    def post(self, path: str, data: HeaderType, headers: HeaderType = None):
        return self.client.post(path, data=json.dumps(data), content_type='application/json', headers=headers)

    def put(self, path: str, data, headers: HeaderType = None):
        return self.client.put(path, data=json.dumps(data), content_type='application/json', headers=headers)

    def _login(self, username: str = 'admin', password: str = 'admin1234') -> str:
        path = 'api/login'
        request_data = {'username': username, 'password': password}

        response = self.post(path, request_data)
        data = json.loads(response.data.decode())

        return data['Authorization']

    def _get_headers(self, username: str = 'admin', password: str = 'admin1234') -> HeaderType:
        return {'accept': 'application/json', 'Authorization': f'Bearer {self._login(username, password)}'}

    def _check_error(self, response: ..., code: int, title: str, detail: str) -> None:
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], code)
        self.assertEqual(data['title'], title)
        self.assertEqual(data['detail'], detail)
        self.assertEqual(response.content_type, 'application/problem+json')
        self.assertEqual(response.status_code, code)

    def _check_succes(self, expected: Any, response: ..., code: int) -> None:
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], code)
        self.assertEqual(data['title'], 'Success')
        self.assertEqual(data['data'], expected)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, code)

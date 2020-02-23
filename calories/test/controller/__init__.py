import json
import unittest
from urllib.parse import quote

from calories.test import BaseTestCase


class TestAPI(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.path = 'api'

    def delete(self, path, headers=None):
        return self.client.delete(path, content_type='application/json', headers=headers)

    def get(self, path, headers=None):
        return self.client.get(path, content_type='application/json', headers=headers)

    def post(self, path, data, headers=None):
        return self.client.post(path, data=json.dumps(data), content_type='application/json', headers=headers)

    def put(self, path, data, headers=None):
        return self.client.put(path, data=json.dumps(data), content_type='application/json', headers=headers)

    def _login(self, username='admin', password='admin1234'):
        path = 'api/login'
        request_data = {'username': username, 'password': password}

        response = self.post(path, request_data)
        data = json.loads(response.data.decode())

        return data['Authorization']

    def _get_headers(self, username='admin', password='admin1234'):
        return {'accept': 'application/json', 'Authorization': f'Bearer {self._login(username, password)}'}

    def _check_error(self, response, code, title, detail):
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], code)
        self.assertEqual(data['title'], title)
        self.assertEqual(data['detail'], detail)
        self.assertEqual(response.content_type, 'application/problem+json')
        self.assertEqual(response.status_code, code)

    def _check_succes(self, expected, response, code):
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], code)
        self.assertEqual(data['title'], 'Success')
        self.assertEqual(data['data'], expected)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, code)

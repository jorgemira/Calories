"""Test module for calories.main.controller.auth"""
import json
import unittest

from calories.test.controller import TestAPI


class TestAuth(TestAPI):
    """Test class for calories.main.controller.auth"""

    def test_login_success(self):
        """Succesful login"""
        path = '/'.join([self.path, 'login'])
        with self.client:
            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.post(path, request_data)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 201)
            self.assertEqual(data['title'], 'Success')
            self.assertTrue(data['Authorization'])
            self.assertEqual(data['detail'], "User 'admin' successfully logged in")
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 201)

    def test_login_wrong_user(self):
        """Wrong user"""
        path = '/'.join([self.path, 'login'])
        with self.client:
            request_data = {'username': 'wrong_user', 'password': 'wrong_password'}
            response = self.post(path, request_data)
            self._check_error(response, 404, 'Not Found', "User 'wrong_user' not found")

    def test_login_wrong_password(self):
        """Wrong password"""
        path = '/'.join([self.path, 'login'])
        with self.client:
            request_data = {'username': 'admin', 'password': 'wrong_password'}
            response = self.post(path, request_data)
            self._check_error(response, 401, 'Unauthorized', "Wrong password for user 'admin'")

    def test_login_wrong_request_body(self):
        """Wrong request body"""
        path = '/'.join([self.path, 'login'])
        with self.client:
            request_data = {'username': 'admin'}
            response = self.post(path, request_data)
            self._check_error(response, 400, 'Bad Request', "'password' is a required property")


if __name__ == '__main__':
    unittest.main()

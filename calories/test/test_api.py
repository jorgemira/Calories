import json
import unittest

from calories.test.base import BaseTestCase


class TestAPI(BaseTestCase):

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

    def test_login(self):
        path = 'api/login'
        with self.client:
            # Succesful login
            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.post(path, request_data)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 201)
            self.assertEqual(data['title'], 'Success')
            self.assertTrue(data['Authorization'])
            self.assertEqual(data['detail'], "User 'admin' successfully logged in")
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 201)

            # Wrong user
            request_data = {'username': 'wrong_user', 'password': 'wrong_password'}
            response = self.post(path, request_data)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'], "User 'wrong_user' not found")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # Wrong password
            request_data = {'username': 'admin', 'password': 'wrong_password'}
            response = self.post(path, request_data)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'], "Wrong password for user 'admin'")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # Wrong request body
            request_data = {'username': 'admin'}
            response = self.post(path, request_data)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 400)
            self.assertEqual(data['title'], 'Bad Request')
            self.assertEqual(data['detail'], "'password' is a required property")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 400)

    def test_get_all_users(self):
        path = 'api/users'
        auth_token = self._login()
        headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}

        with self.client:
            # Unauthenticated request request
            response = self.get(path, None)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'], 'No authorization token provided')
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # Successful request as admin
            response = self.get(path, headers)
            data = json.loads(response.data.decode())
            self.assertTrue(data)  # TODO: Change to check values
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # User is not allowed to see user list
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path, headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'],
                             "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # Manager is allowed
            auth_token = self._login('manager1', 'pass_manager1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path, headers)
            data = json.loads(response.data.decode())
            self.assertTrue(data)  # TODO: Change to check values
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # TODO: Test filtering and pagination

    def test_post_user(self):
        path = 'api/users'
        auth_token = self._login()
        headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}

        with self.client:
            # Unauthenticated request
            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.post(path, request_data, None)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'], 'No authorization token provided')
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # Request missing parameters
            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.post(path, request_data, headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 400)
            self.assertEqual(data['title'], 'Bad Request')
            self.assertEqual(data['detail'], "'name' is a required property")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 400)

            # Correct request
            request_data = {'username': 'user3',
                            'name': 'User 3',
                            'email': 'user3@users.com',
                            'role': 'USER',
                            'daily_calories': 2500,
                            'password': 'pass_user3'}
            result = request_data.copy()
            result.pop('password')
            response = self.post(path, request_data, headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data, result)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 201)

            # Username exists
            request_data = {'username': 'user1',
                            'name': 'User 1',
                            'email': 'user1@users.com',
                            'role': 'USER',
                            'daily_calories': 2500,
                            'password': 'pass_user1'}
            response = self.post(path, request_data, headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 409)
            self.assertEqual(data['title'], 'Conflict')
            self.assertEqual(data['detail'], "User 'user1' exists already")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 409)

            # Role user tries to add user
            request_data = {'username': 'user4',
                            'name': 'User 4',
                            'email': 'user4@users.com',
                            'role': 'USER',
                            'daily_calories': 2500,
                            'password': 'pass_user4'}

            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}

            response = self.post(path, request_data, headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'],
                             "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # Manager tries to add a user
            request_data = {'username': 'user4',
                            'name': 'User 4',
                            'email': 'user4@users.com',
                            'role': 'USER',
                            'daily_calories': 2500,
                            'password': 'pass_user4'}
            result = request_data.copy()
            result.pop('password')

            auth_token = self._login('manager1', 'pass_manager1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}

            response = self.post(path, request_data, headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data, result)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 201)

    def test_delete_user(self):
        path = 'api/users'

        with self.client:
            # Unauthenticated request
            response = self.delete('/'.join([path, 'user1']), None)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'], 'No authorization token provided')
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # User cannot delete other users
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete('/'.join([path, 'manager1']), headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'],
                             "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # User can delete himself
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete('/'.join([path, 'user1']), headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['success'], True)
            self.assertEqual(data['message'], "User 'user1' deleted")
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # User managers can delete users
            auth_token = self._login('manager1', 'pass_manager1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete('/'.join([path, 'manager2']), headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['success'], True)
            self.assertEqual(data['message'], "User 'manager2' deleted")
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # Error deleting non existing user
            response = self.delete('/'.join([path, 'manager2']), headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 404)
            self.assertEqual(data['title'], 'Not Found')
            self.assertEqual(data['detail'], "User 'manager2' not found")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 404)

    def test_get_user(self):
        path = 'api/users'

        with self.client:
            # Unauthenticated request
            response = self.get('/'.join([path, 'user1']), None)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'], 'No authorization token provided')
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # User cannot get other users
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get('/'.join([path, 'manager1']), headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'],
                             "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # User can get himself
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get('/'.join([path, 'user1']), headers)
            data = json.loads(response.data.decode())
            self.assertTrue(data)  # TODO: Change to check values
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # User managers can get users
            auth_token = self._login('manager1', 'pass_manager1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get('/'.join([path, 'manager2']), headers)
            data = json.loads(response.data.decode())
            self.assertTrue(data)  # TODO: Change to check values
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # Error getting non existing user
            response = self.get('/'.join([path, 'user3']), headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 404)
            self.assertEqual(data['title'], 'Not Found')
            self.assertEqual(data['detail'], "User 'user3' not found")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 404)

    def test_put_user(self):
        path = 'api/users'

        with self.client:
            # Unauthenticated request
            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.put('/'.join([path, 'user1']), request_data, None)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'], 'No authorization token provided')
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # User cannot get other users
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.put('/'.join([path, 'manager1']), request_data, headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'],
                             "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # User can put himself
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            request_data = {'username': 'user1a', 'password': 'new_password', 'name': 'User 1A'}
            response = self.put('/'.join([path, 'user1']), request_data, headers)
            data = json.loads(response.data.decode())
            self.assertTrue(data)  # TODO: Change to check values
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # User managers can get users
            auth_token = self._login('manager1', 'pass_manager1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get('/'.join([path, 'manager2']), headers)
            data = json.loads(response.data.decode())
            self.assertTrue(data)  # TODO: Change to check values
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # Error getting non existing user
            response = self.get('/'.join([path, 'user3']), headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 404)
            self.assertEqual(data['title'], 'Not Found')
            self.assertEqual(data['detail'], "User 'user3' not found")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 404)

            # TODO: test users can't change roles

    def test_get_all_meals(self):
        # TODO remove endpoint
        pass

    def test_get_user_meals(self):
        path = 'api/users'
        auth_token = self._login()
        headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}

        with self.client:
            # Unauthenticated request request
            path_user1 = '/'.join([path, 'user1', 'meals'])
            response = self.get(path_user1, None)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'], 'No authorization token provided')
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # Successful request as admin
            response = self.get(path_user1, headers)
            data = json.loads(response.data.decode())
            self.assertTrue(data)  # TODO: Change to check values
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # User is allowed to see its own meals
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path_user1, headers)
            data = json.loads(response.data.decode())
            self.assertTrue(data)  # TODO: Change to check values
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # User is not allowed to see other user meals
            # TODO: Fix
            # path_user2 = '/'.join([path, 'user2', 'meals'])
            # response = self.get(path_user2, headers)
            # data = json.loads(response.data.decode())
            # self.assertEqual(data['status'], 401)
            # self.assertEqual(data['title'], 'Unauthorized')
            # self.assertEqual(data['detail'],
            #                  "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")
            # self.assertEqual(response.content_type, 'application/problem+json')
            # self.assertEqual(response.status_code, 401)

            # Managers are not allowed to see other meals
            auth_token = self._login('manager1', 'pass_manager1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path_user1, headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'],
                             "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # Managers are not allowed to see meals, even their own TODO: Fix it
            # path_manager1 = '/'.join([path, 'manager1', 'meals'])
            # response = self.get(path_manager1, headers)
            # data = json.loads(response.data.decode())
            # self.assertEqual(data['status'], 401)
            # self.assertEqual(data['title'], 'Unauthorized')
            # self.assertEqual(data['detail'],
            #                  "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")
            # self.assertEqual(response.content_type, 'application/problem+json')
            # self.assertEqual(response.status_code, 401)

    def test_post_meal(self):
        path = 'api/users'
        auth_token = self._login()
        headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}

        with self.client:
            # Unauthenticated request
            path_user1 = '/'.join([path, 'user1', 'meals'])

            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.post(path_user1, request_data, None)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'], 'No authorization token provided')
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # Request missing parameters
            request_data = {'description': 'description', 'calories': 0}
            response = self.post(path, request_data, headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 400)
            self.assertEqual(data['title'], 'Bad Request')
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 400)

            # Correct request from admin
            request_data = {"date": '2020-11-2',
                            "time": '15:05:28',
                            "name": "meal 3",
                            "grams": 800,
                            "description": "Meal 3 User 1",
                            "calories": 500}
            response = self.post(path_user1, request_data, headers)
            data = json.loads(response.data.decode())
            self.assertTrue(data)  # TODO: check real values and check under_total_daily
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 201)

            # Wrong user from admin
            path_wronguser = '/'.join([path, 'wronguser', 'meals'])
            response = self.post(path_wronguser, request_data, headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 404)
            self.assertEqual(data['title'], 'Not Found')
            self.assertEqual(data['detail'], "User 'wronguser' not found")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 404)

            # User can add meals to himseld
            auth_token = self._login('user1', 'pass_user1')
            headers_user1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.post(path_user1, request_data, headers_user1)
            data = json.loads(response.data.decode())
            self.assertTrue(data)  # TODO: check real values and check under_total_daily
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 201)

            # User cannot add meals other users # TODO: fix it
            # path_user2 = '/'.join([path, 'user2', 'meals'])
            # response = self.post(path_user2, request_data, headers_user1)
            # data = json.loads(response.data.decode())
            # self.assertTrue(data)  # TODO: check real values and check under_total_daily
            # self.assertEqual(response.content_type, 'application/json')
            # self.assertEqual(response.status_code, 201)

            # Managers cannot add meals to other users
            auth_token = self._login('manager1', 'pass_manager1')
            headers_manager1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            path_user2 = '/'.join([path, 'user2', 'meals'])
            response = self.post(path_user2, request_data, headers_manager1)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'],
                             "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # Managers cannot add meals to themselves # TODO: Fix it
            # path_manager1 = '/'.join([path, 'manager1', 'meals'])
            # response = self.post(path_manager1, request_data, headers_manager1)
            # data = json.loads(response.data.decode())
            # self.assertEqual(data['status'], 401)
            # self.assertEqual(data['title'], 'Unauthorized')
            # self.assertEqual(data['detail'],
            #                  "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")
            # self.assertEqual(response.content_type, 'application/problem+json')
            # self.assertEqual(response.status_code, 401)

    def test_delete_meal(self):
        path = 'api/users'

        with self.client:
            # Unauthenticated request
            path_meal1 = '/'.join([path, 'user1', 'meals', '1'])
            response = self.delete(path_meal1, None)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'], 'No authorization token provided')
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

            # Admin can delete a meal
            auth_token = self._login()
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete(path_meal1, headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['success'], True)
            self.assertEqual(data['message'], "Meal '1' deleted")
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # Admin mistake on user
            auth_token = self._login()
            path_wrong = '/'.join([path, 'wronguser', 'meals', '2'])
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete(path_wrong, headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 404)
            self.assertEqual(data['title'], 'Not Found')
            self.assertEqual(data['detail'], "User 'wronguser' not found")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 404)

            # User cannot delete other users meals # TODO: Fix it
            # path_meal3 = '/'.join([path, 'user2', 'meals','3'])
            # auth_token = self._login('user1', 'pass_user1')
            # headers_user1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            # response = self.delete(path_meal3, headers_user1)
            # data = json.loads(response.data.decode())
            # self.assertEqual(data['status'], 401)
            # self.assertEqual(data['title'], 'Unauthorized')
            # self.assertEqual(data['detail'],
            #                  "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")
            # self.assertEqual(response.content_type, 'application/problem+json')
            # self.assertEqual(response.status_code, 401)

            # User can delete his own meals
            path_meal2 = '/'.join([path, 'user1', 'meals', '2'])
            auth_token = self._login('user1', 'pass_user1')
            headers_user1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete(path_meal2, headers_user1)
            data = json.loads(response.data.decode())
            self.assertEqual(data['success'], True)
            self.assertEqual(data['message'], "Meal '2' deleted")
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # Meal doesnt exist
            response = self.delete(path_meal2, headers_user1)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 404)
            self.assertEqual(data['title'], 'Not Found')
            self.assertEqual(data['detail'], "Meal '2' not found")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 404)

            # User managers cannot delete their meals # TODO Fixme: they cannot delete their own either
            # auth_token = self._login('manager1', 'pass_manager1')
            # path_meal4 = '/'.join([path, 'manager1', 'meals', '4'])
            # headers_manager1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            # response = self.delete(path_meal4, headers_manager1)
            # data = json.loads(response.data.decode())
            # self.assertEqual(data['success'], True)
            # self.assertEqual(data['message'], "User 'manager2' deleted")
            # self.assertEqual(response.content_type, 'application/json')
            # self.assertEqual(response.status_code, 200)

            # User managers cannot delete meals
            auth_token = self._login('manager1', 'pass_manager1')
            path_meal4 = '/'.join([path, 'manager2', 'meals', '4'])
            headers_manager1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete(path_meal4, headers_manager1)
            data = json.loads(response.data.decode())
            self.assertEqual(data['status'], 401)
            self.assertEqual(data['title'], 'Unauthorized')
            self.assertEqual(data['detail'],
                             "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")
            self.assertEqual(response.content_type, 'application/problem+json')
            self.assertEqual(response.status_code, 401)

    def test_get_meal(self):
        # TODO
        pass

    def test_put_meal(self):
        # TODO
        pass


if __name__ == '__main__':
    unittest.main()

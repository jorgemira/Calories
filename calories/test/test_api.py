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

    def _check_error(self, response, code, title, detail):
        data = json.loads(response.data.decode())
        self.assertEqual(data['status'], code)
        self.assertEqual(data['title'], title)
        self.assertEqual(data['detail'], detail)
        self.assertEqual(response.content_type, 'application/problem+json')
        self.assertEqual(response.status_code, code)

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
            self._check_error(response, 401, 'Unauthorized', "User 'wrong_user' not found")

            # Wrong password
            request_data = {'username': 'admin', 'password': 'wrong_password'}
            response = self.post(path, request_data)
            self._check_error(response, 401, 'Unauthorized', "Wrong password for user 'admin'")

            # Wrong request body
            request_data = {'username': 'admin'}
            response = self.post(path, request_data)
            self._check_error(response, 400, 'Bad Request', "'password' is a required property")

    def test_get_all_users(self):
        path = 'api/users'
        auth_token = self._login()
        headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}

        with self.client:
            # Unauthenticated request request
            response = self.get(path, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

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
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")

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
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

            # Request missing parameters
            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.post(path, request_data, headers)
            self._check_error(response, 400, 'Bad Request', "'name' is a required property")

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
            self._check_error(response, 409, 'Conflict', "User 'user1' exists already")

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
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")

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
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

            # User cannot delete other users
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete('/'.join([path, 'manager1']), headers)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")

            # User can delete himself
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete('/'.join([path, 'user1']), headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data['success'], True)
            self.assertEqual(data['message'], "User 'user1' deleted")
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # Managers cannot delete managers
            auth_token = self._login('manager1', 'pass_manager1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete('/'.join([path, 'manager2']), headers)
            self._check_error(response, 401, 'Unauthorized', "User 'manager1' can only delete users with role USER")

            # Error deleting non existing user
            response = self.delete('/'.join([path, 'user1']), headers)
            self._check_error(response, 404, 'Not Found', "User 'user1' not found")

    def test_get_user(self):
        path = 'api/users'

        with self.client:
            # Unauthenticated request
            response = self.get('/'.join([path, 'user1']), None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

            # User cannot get other users
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get('/'.join([path, 'manager1']), headers)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")

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
            self._check_error(response, 404, 'Not Found', "User 'user3' not found")

    def test_put_user(self):
        path = 'api/users'

        with self.client:
            # Unauthenticated request
            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.put('/'.join([path, 'user1']), request_data, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

            # User cannot get other users
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.put('/'.join([path, 'manager1']), request_data, headers)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")

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
            self._check_error(response, 404, 'Not Found', "User 'user3' not found")

            # TODO: test users can't change roles

    def test_get_user_meals(self):
        path = 'api/users'
        auth_token = self._login()
        headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}

        with self.client:
            # Unauthenticated request request
            path_user1 = '/'.join([path, 'user1', 'meals'])
            response = self.get(path_user1, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

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
            path_user2 = '/'.join([path, 'user2', 'meals'])
            response = self.get(path_user2, headers)
            self._check_error(response, 401, 'Unauthorized', "User 'user1' cannot perform the action for other user")

            # Managers are not allowed to see other meals
            auth_token = self._login('manager1', 'pass_manager1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path_user1, headers)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

            # Managers are not allowed to see meals, even their own
            path_manager1 = '/'.join([path, 'manager1', 'meals'])
            response = self.get(path_manager1, headers)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

    def test_post_meal(self):
        path = 'api/users'
        auth_token = self._login()
        headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}

        with self.client:
            # Unauthenticated request
            path_user1 = '/'.join([path, 'user1', 'meals'])

            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.post(path_user1, request_data, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

            # Request missing parameters
            request_data = {'description': 'description', 'calories': 0}
            response = self.post(path, request_data, headers)
            self._check_error(response, 400, 'Bad Request', "'username' is a required property")

            # Wrongly formatted parameters
            request_data = {"date": '2020/11/2',
                            "time": '15:99:28',
                            "name": "meal 3",
                            "grams": 800,
                            "description": "Meal 3 User 1",
                            "calories": 500}
            response = self.post(path_user1, request_data, headers)
            self._check_error(response, 400, 'Bad Request', "Field(s): 'time', 'date' have the wrong format")

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
            self._check_error(response, 404, 'Not Found', "User 'wronguser' not found")

            # User can add meals to himseld
            auth_token = self._login('user1', 'pass_user1')
            headers_user1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.post(path_user1, request_data, headers_user1)
            data = json.loads(response.data.decode())
            self.assertTrue(data)  # TODO: check real values and check under_total_daily
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 201)

            # User cannot add meals other users
            path_user2 = '/'.join([path, 'user2', 'meals'])
            response = self.post(path_user2, request_data, headers_user1)
            self._check_error(response, 401, 'Unauthorized', "User 'user1' cannot perform the action for other user")

            # Managers cannot add meals to other users
            auth_token = self._login('manager1', 'pass_manager1')
            headers_manager1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            path_user2 = '/'.join([path, 'user2', 'meals'])
            response = self.post(path_user2, request_data, headers_manager1)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

            # Managers cannot add meals to themselves
            path_manager1 = '/'.join([path, 'manager1', 'meals'])
            response = self.post(path_manager1, request_data, headers_manager1)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

    def test_delete_meal(self):
        path = 'api/users'

        with self.client:
            # Unauthenticated request
            path_meal1 = '/'.join([path, 'user1', 'meals', '1'])
            response = self.delete(path_meal1, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

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
            self._check_error(response, 404, 'Not Found', "User 'wronguser' not found")

            # User cannot delete other users meals
            path_meal3 = '/'.join([path, 'user2', 'meals', '3'])
            auth_token = self._login('user1', 'pass_user1')
            headers_user1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete(path_meal3, headers_user1)
            self._check_error(response, 401, 'Unauthorized', "User 'user1' cannot perform the action for other user")

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
            self._check_error(response, 404, 'Not Found', "Meal '2' not found")

            # User managers cannot delete their meals
            auth_token = self._login('manager1', 'pass_manager1')
            path_meal4 = '/'.join([path, 'manager1', 'meals', '4'])
            headers_manager1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete(path_meal4, headers_manager1)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")
            # User managers cannot delete meals
            auth_token = self._login('manager1', 'pass_manager1')
            path_meal4 = '/'.join([path, 'manager2', 'meals', '4'])
            headers_manager1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete(path_meal4, headers_manager1)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

    def test_get_meal(self):
        path = 'api/users'

        with self.client:
            # Unauthenticated request
            path_meal1 = '/'.join([path, 'user1', 'meals', '1'])
            response = self.get(path_meal1, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

            # Admin can see any meal
            auth_token = self._login()
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            expected = {'calories': 500, 'date': '2020-02-11', 'description': 'Meal 1 User 1', 'grams': 100, 'id': 1,
                        'name': 'meal 1', 'time': '15:00:03', 'under_daily_total': True, 'user': 2}
            response = self.get(path_meal1, headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data, expected)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # Admin mistake on user
            auth_token = self._login()
            path_wrong = '/'.join([path, 'wronguser', 'meals', '2'])
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path_wrong, headers)
            self._check_error(response, 404, 'Not Found', "User 'wronguser' not found")

            # User cannot get other users meals
            path_meal3 = '/'.join([path, 'user2', 'meals', '3'])
            auth_token = self._login('user1', 'pass_user1')
            headers_user1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path_meal3, headers_user1)
            self._check_error(response, 401, 'Unauthorized', "User 'user1' cannot perform the action for other user")

            # User can get his own meals
            path_meal2 = '/'.join([path, 'user1', 'meals', '1'])
            auth_token = self._login('user1', 'pass_user1')
            headers_user1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path_meal2, headers_user1)
            data = json.loads(response.data.decode())
            self.assertEqual(data, expected)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # Meal doesnt exist
            path_meal4 = '/'.join([path, 'user1', 'meals', '4'])
            response = self.get(path_meal4, headers_user1)
            self._check_error(response, 404, 'Not Found', "Meal '4' not found")

            # User managers cannot get their meals
            auth_token = self._login('manager1', 'pass_manager1')
            path_meal4 = '/'.join([path, 'manager1', 'meals', '4'])
            headers_manager1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path_meal4, headers_manager1)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

            # User managers cannot get meals
            auth_token = self._login('manager1', 'pass_manager1')
            path_meal4 = '/'.join([path, 'manager2', 'meals', '4'])
            headers_manager1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path_meal4, headers_manager1)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

    def test_put_meal(self):
        path = 'api/users'

        with self.client:
            # Unauthenticated request
            path_meal1 = '/'.join([path, 'user1', 'meals', '1'])
            response = self.get(path_meal1, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

            # Admin can see any meal
            auth_token = self._login()
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            expected = {'calories': 500, 'date': '2020-02-11', 'description': 'Meal 1 User 1', 'grams': 100, 'id': 1,
                        'name': 'meal 1', 'time': '15:00:03', 'under_daily_total': True, 'user': 2}
            response = self.get(path_meal1, headers)
            data = json.loads(response.data.decode())
            self.assertEqual(data, expected)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # Admin mistake on user
            auth_token = self._login()
            path_wrong = '/'.join([path, 'wronguser', 'meals', '2'])
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path_wrong, headers)
            self._check_error(response, 404, 'Not Found', "User 'wronguser' not found")

            # User cannot get other users meals
            path_meal3 = '/'.join([path, 'user2', 'meals', '3'])
            auth_token = self._login('user1', 'pass_user1')
            headers_user1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path_meal3, headers_user1)
            self._check_error(response, 401, 'Unauthorized', "User 'user1' cannot perform the action for other user")

            # User can get his own meals
            path_meal2 = '/'.join([path, 'user1', 'meals', '1'])
            auth_token = self._login('user1', 'pass_user1')
            headers_user1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path_meal2, headers_user1)
            data = json.loads(response.data.decode())
            self.assertEqual(data, expected)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 200)

            # Meal doesnt exist
            path_meal4 = '/'.join([path, 'user1', 'meals', '4'])
            response = self.get(path_meal4, headers_user1)
            self._check_error(response, 404, 'Not Found', "Meal '4' not found")

            # User managers cannot get their meals
            auth_token = self._login('manager1', 'pass_manager1')
            path_meal4 = '/'.join([path, 'manager1', 'meals', '4'])
            headers_manager1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path_meal4, headers_manager1)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

            # User managers cannot get meals
            auth_token = self._login('manager1', 'pass_manager1')
            path_meal4 = '/'.join([path, 'manager2', 'meals', '4'])
            headers_manager1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path_meal4, headers_manager1)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")


if __name__ == '__main__':
    unittest.main()

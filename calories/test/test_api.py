import json
import unittest
from urllib.parse import quote

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

    def _check_succes(self, expected, response, code):
        data = json.loads(response.data.decode())
        self.assertEqual(data, expected)
        self.assertEqual(response.status_code, code)
        self.assertEqual(response.content_type, 'application/json')

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
            self._check_error(response, 404, 'Not Found', "User 'wrong_user' not found")

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
            expected = [{'daily_calories': 0, 'email': 'admin@adminmail.com', 'name': 'Administrator', 'role': 'ADMIN',
                         'username': 'admin'},
                        {'daily_calories': 2000, 'email': 'manager1@managermail.com', 'name': 'Manager 1',
                         'role': 'MANAGER', 'username': 'manager1'},
                        {'daily_calories': 4000, 'email': 'manager2@managermail.com', 'name': 'Manager 2',
                         'role': 'MANAGER', 'username': 'manager2'},
                        {'daily_calories': 2500, 'email': 'user1@usermail.com', 'name': 'User 1', 'role': 'USER',
                         'username': 'user1'},
                        {'daily_calories': 3000, 'email': 'user2@usemail.com', 'name': 'User 2', 'role': 'USER',
                         'username': 'user2'}]
            response = self.get(path, headers)
            self._check_succes(expected, response, 200)

            # User is not allowed to see user list
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path, headers)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")

            # Manager is allowed
            expected = [{'daily_calories': 0, 'email': 'admin@adminmail.com', 'name': 'Administrator', 'role': 'ADMIN',
                         'username': 'admin'},
                        {'daily_calories': 2000, 'email': 'manager1@managermail.com', 'name': 'Manager 1',
                         'role': 'MANAGER', 'username': 'manager1'},
                        {'daily_calories': 4000, 'email': 'manager2@managermail.com', 'name': 'Manager 2',
                         'role': 'MANAGER', 'username': 'manager2'},
                        {'daily_calories': 2500, 'email': 'user1@usermail.com', 'name': 'User 1', 'role': 'USER',
                         'username': 'user1'},
                        {'daily_calories': 3000, 'email': 'user2@usemail.com', 'name': 'User 2', 'role': 'USER',
                         'username': 'user2'}]
            auth_token = self._login('manager1', 'pass_manager1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path, headers)
            self._check_succes(expected, response, 200)

            # Test pagination: first page
            expected = [{'daily_calories': 0, 'email': 'admin@adminmail.com', 'name': 'Administrator', 'role': 'ADMIN',
                         'username': 'admin'},
                        {'daily_calories': 2000, 'email': 'manager1@managermail.com', 'name': 'Manager 1',
                         'role': 'MANAGER', 'username': 'manager1'}]
            paged_path = path + '?itemsPerPage=2&pageNumber=1'
            response = self.get(paged_path, headers)
            self._check_succes(expected, response, 200)

            # Test pagination: last page
            expected = [{'daily_calories': 3000, 'email': 'user2@usemail.com', 'name': 'User 2', 'role': 'USER',
                         'username': 'user2'}]
            paged_path = path + '?itemsPerPage=2&pageNumber=3'
            response = self.get(paged_path, headers)
            self._check_succes(expected, response, 200)

            # Test pagination: beyond last page
            expected = []
            paged_path = path + '?itemsPerPage=2&pageNumber=20'
            response = self.get(paged_path, headers)
            self._check_succes(expected, response, 200)

            # Test filtering:
            expected = [{'daily_calories': 3000, 'email': 'user2@usemail.com', 'name': 'User 2', 'role': 'USER',
                         'username': 'user2'}]
            filtered_path = path + "?filter=" + quote("(username ne 'user1') AND "
                                                      "((daily_calories gt 2200) AND (daily_calories lt 3500))")
            response = self.get(filtered_path, headers)
            self._check_succes(expected, response, 200)

            # Test filtering:
            expected = [{'daily_calories': 3000, 'email': 'user2@usemail.com', 'name': 'User 2', 'role': 'USER',
                         'username': 'user2'}]
            filtered_path = path + "?filter=" + quote('wrongfilter')
            response = self.get(filtered_path, headers)
            self._check_error(response, 400, 'Bad Request', "Filter 'wrongfilter' is invalid")

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
            expected = request_data.copy()
            expected.pop('password')
            response = self.post(path, request_data, headers)
            self._check_succes(expected, response, 201)

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
            expected = request_data.copy()
            expected.pop('password')
            auth_token = self._login('manager1', 'pass_manager1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.post(path, request_data, headers)
            self._check_succes(expected, response, 201)

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
            expected = {'message': "User 'user1' deleted", 'success': True}
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete('/'.join([path, 'user1']), headers)
            data = json.loads(response.data.decode())
            self._check_succes(expected, response, 200)

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
            expected = {'daily_calories': 2500, 'email': 'user1@usermail.com', 'name': 'User 1', 'role': 'USER',
                        'username': 'user1'}
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get('/'.join([path, 'user1']), headers)
            self._check_succes(expected, response, 200)

            # User managers can get users
            expected = {'daily_calories': 4000, 'email': 'manager2@managermail.com', 'name': 'Manager 2',
                        'role': 'MANAGER', 'username': 'manager2'}
            auth_token = self._login('manager1', 'pass_manager1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get('/'.join([path, 'manager2']), headers)
            self._check_succes(expected, response, 200)

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
            expected = {'daily_calories': 2500, 'email': 'user1@usermail.com', 'name': 'User 1A', 'role': 'USER',
                        'username': 'user1a'}
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            request_data = {'username': 'user1a', 'password': 'new_password', 'name': 'User 1A'}
            response = self.put('/'.join([path, 'user1']), request_data, headers)
            self._check_succes(expected, response, 200)

            # User managers can get users
            expected = {'daily_calories': 4000, 'email': 'manager2@managermail.com', 'name': 'Manager 2',
                        'role': 'MANAGER', 'username': 'manager2'}
            auth_token = self._login('manager1', 'pass_manager1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get('/'.join([path, 'manager2']), headers)
            self._check_succes(expected, response, 200)

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
            expected = [{'calories': 500, 'date': '2020-02-11', 'description': 'Meal 1 User 1', 'grams': 100, 'id': 1,
                         'name': 'meal 1', 'time': '15:00:03', 'under_daily_total': True},
                        {'calories': 2100, 'date': '2020-02-11', 'description': 'Meal 2 User 1', 'grams': 100, 'id': 2,
                         'name': 'meal 2', 'time': '15:10:03', 'under_daily_total': True}]
            response = self.get(path_user1, headers)
            self._check_succes(expected, response, 200)

            # User is allowed to see its own meals
            auth_token = self._login('user1', 'pass_user1')
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path_user1, headers)
            self._check_succes(expected, response, 200)

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
            self._check_error(response, 400, 'Bad Request', "Field(s): 'date', 'time' have the wrong format")

            # Correct request from admin
            expected = {'calories': 500, 'date': '2020-02-11', 'description': 'Meal 3 User 1', 'grams': 800, 'id': 4,
                        'name': 'meal 3', 'time': '15:05:28', 'under_daily_total': False}
            request_data = {"date": '2020-02-11', "time": '15:05:28', "name": "meal 3", "grams": 800,
                            "description": "Meal 3 User 1", "calories": 500}
            response = self.post(path_user1, request_data, headers)
            self._check_succes(expected, response, 201)

            # Wrong user from admin
            path_wronguser = '/'.join([path, 'wronguser', 'meals'])
            response = self.post(path_wronguser, request_data, headers)
            self._check_error(response, 404, 'Not Found', "User 'wronguser' not found")

            # User can add meals to himself
            expected = {'calories': 500, 'date': '2020-02-11', 'description': 'Meal 3 User 1', 'grams': 800, 'id': 5,
                        'name': 'meal 3', 'time': '15:05:28', 'under_daily_total': False}
            auth_token = self._login('user1', 'pass_user1')
            headers_user1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.post(path_user1, request_data, headers_user1)
            self._check_succes(expected, response, 201)

            # User can add meals to himself under daily total
            expected = {'calories': 500, 'date': '2020-02-12', 'description': 'Meal 4 User 1', 'grams': 800, 'id': 6,
                        'name': 'meal 4', 'time': '15:05:28', 'under_daily_total': True}
            request_data = {"date": '2020-02-12', "time": '15:05:28', "name": "meal 4", "grams": 800,
                            "description": "Meal 4 User 1", "calories": 500}
            auth_token = self._login('user1', 'pass_user1')
            headers_user1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.post(path_user1, request_data, headers_user1)
            self._check_succes(expected, response, 201)

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
            expected = {'message': "Meal '1' deleted", 'success': True}
            auth_token = self._login()
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete(path_meal1, headers)
            self._check_succes(expected, response, 200)

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
            expected = {'message': "Meal '2' deleted", 'success': True}
            path_meal2 = '/'.join([path, 'user1', 'meals', '2'])
            auth_token = self._login('user1', 'pass_user1')
            headers_user1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.delete(path_meal2, headers_user1)
            self._check_succes(expected, response, 200)

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
            expected = {'calories': 500, 'date': '2020-02-11', 'description': 'Meal 1 User 1', 'grams': 100, 'id': 1,
                        'name': 'meal 1', 'time': '15:00:03', 'under_daily_total': True}
            auth_token = self._login()
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            expected = {'calories': 500, 'date': '2020-02-11', 'description': 'Meal 1 User 1', 'grams': 100, 'id': 1,
                        'name': 'meal 1', 'time': '15:00:03', 'under_daily_total': True}
            response = self.get(path_meal1, headers)
            self._check_succes(expected, response, 200)

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
            expected = {'calories': 500, 'date': '2020-02-11', 'description': 'Meal 1 User 1', 'grams': 100, 'id': 1,
                        'name': 'meal 1', 'time': '15:00:03', 'under_daily_total': True}
            path_meal2 = '/'.join([path, 'user1', 'meals', '1'])
            auth_token = self._login('user1', 'pass_user1')
            headers_user1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.get(path_meal2, headers_user1)
            self._check_succes(expected, response, 200)

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
            path_meal1 = '/'.join([path, 'user1', 'meals', '2'])
            response = self.get(path_meal1, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

            # Admin can put any meal
            auth_token = self._login()
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            expected = {'calories': 500, 'date': '2020-02-11', 'description': 'Meal 1 User 1b', 'grams': 800, 'id': 2,
                        'name': 'meal 1b', 'time': '15:10:03', 'under_daily_total': True}
            request_data = {'calories': 500, 'description': 'Meal 1 User 1b', 'grams': 800, 'name': 'meal 1b'}
            response = self.put(path_meal1, request_data, headers)
            self._check_succes(expected, response, 200)

            # Admin mistake on user
            auth_token = self._login()
            path_wrong = '/'.join([path, 'wronguser', 'meals', '2'])
            headers = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.put(path_wrong, request_data, headers)
            self._check_error(response, 404, 'Not Found', "User 'wronguser' not found")

            # User cannot put other users meals
            path_meal3 = '/'.join([path, 'user2', 'meals', '3'])
            auth_token = self._login('user1', 'pass_user1')
            headers_user1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.put(path_meal3, request_data, headers_user1)
            self._check_error(response, 401, 'Unauthorized', "User 'user1' cannot perform the action for other user")

            # User can put his own meals
            expected = {'calories': 5000, 'date': '2020-02-13', 'description': 'Meal 1 User 1', 'grams': 100, 'id': 1,
                        'name': 'meal 1', 'time': '15:00:03', 'under_daily_total': False}
            request_data = {'calories': 5000, 'date': '2020-02-13'}
            path_meal2 = '/'.join([path, 'user1', 'meals', '1'])
            auth_token = self._login('user1', 'pass_user1')
            headers_user1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.put(path_meal2, request_data, headers_user1)
            self._check_succes(expected, response, 200)

            # Meal doesnt exist
            path_meal4 = '/'.join([path, 'user1', 'meals', '4'])
            response = self.put(path_meal4, request_data, headers_user1)
            self._check_error(response, 404, 'Not Found', "Meal '4' not found")

            # User managers cannot put their meals
            auth_token = self._login('manager1', 'pass_manager1')
            path_meal4 = '/'.join([path, 'manager1', 'meals', '4'])
            headers_manager1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.put(path_meal4, request_data,  headers_manager1)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

            # User managers cannot put meals
            auth_token = self._login('manager1', 'pass_manager1')
            path_meal4 = '/'.join([path, 'manager2', 'meals', '4'])
            headers_manager1 = {'accept': 'application/json', 'Authorization': f'Bearer {auth_token}'}
            response = self.put(path_meal4, request_data,  headers_manager1)
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")


if __name__ == '__main__':
    unittest.main()

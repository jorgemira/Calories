import json
import unittest
from urllib.parse import quote

from calories.test.base import BaseTestCase


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

    def test_get_all_users_unauthenticated(self):
        """Unauthenticated request"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            response = self.get(path, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

    def test_get_all_users_success_admin(self):
        """Successful request as admin"""
        path = '/'.join([self.path, 'users'])
        with self.client:
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
            response = self.get(path, self._get_headers())
            self._check_succes(expected, response, 200)

    def test_get_all_users_user_not_allowed(self):
        """User is not allowed to see user list"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            response = self.get(path, self._get_headers('user1', 'pass_user1'))
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")

    def test_get_all_users_manager_allowed(self):
        """Manager is allowed to see user list"""
        path = '/'.join([self.path, 'users'])
        with self.client:
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
            response = self.get(path, self._get_headers('manager1', 'pass_manager1'))
            self._check_succes(expected, response, 200)

    def test_get_all_users_manager_allowed_first_page(self):
        """Manager is allowed to see user list, test pagination: first page"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            expected = [{'daily_calories': 0, 'email': 'admin@adminmail.com', 'name': 'Administrator', 'role': 'ADMIN',
                         'username': 'admin'},
                        {'daily_calories': 2000, 'email': 'manager1@managermail.com', 'name': 'Manager 1',
                         'role': 'MANAGER', 'username': 'manager1'}]
            paged_path = path + '?itemsPerPage=2&pageNumber=1'
            response = self.get(paged_path, self._get_headers('manager1', 'pass_manager1'))
            self._check_succes(expected, response, 200)

    def test_get_all_users_manager_allowed_last_page(self):
        """Manager is allowed to see user list, test pagination: last page"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            expected = [{'daily_calories': 3000, 'email': 'user2@usemail.com', 'name': 'User 2', 'role': 'USER',
                         'username': 'user2'}]
            paged_path = path + '?itemsPerPage=2&pageNumber=3'
            response = self.get(paged_path, self._get_headers('manager1', 'pass_manager1'))
            self._check_succes(expected, response, 200)

    def test_get_all_users_manager_allowed_beyond_last_page(self):
        """Manager is allowed to see user list, test pagination: beyond last page"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            expected = []
            paged_path = path + '?itemsPerPage=2&pageNumber=20'
            response = self.get(paged_path, self._get_headers('manager1', 'pass_manager1'))
            self._check_succes(expected, response, 200)

    def test_get_all_users_manager_allowed_filtering1(self):
        """Manager is allowed to see user list, filtering 1"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            expected = [{'daily_calories': 3000, 'email': 'user2@usemail.com', 'name': 'User 2', 'role': 'USER',
                         'username': 'user2'}]
            filtered_path = path + "?filter=" + quote("(username ne 'user1') AND "
                                                      "((daily_calories gt 2200) AND (daily_calories lt 3500))")
            response = self.get(filtered_path, self._get_headers('manager1', 'pass_manager1'))
            self._check_succes(expected, response, 200)

    def test_get_all_users_manager_allowed_filtering2(self):
        """Manager is allowed to see user list, filtering 2"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            filtered_path = path + "?filter=" + quote('wrongfilter')
            response = self.get(filtered_path, self._get_headers('manager1', 'pass_manager1'))
            self._check_error(response, 400, 'Bad Request', "Filter 'wrongfilter' is invalid")

    def test_post_user_unauthenticated(self):
        """Unauthenticated request"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.post(path, request_data, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

    def test_post_user_missing_parameters(self):
        """Request missing parameters"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.post(path, request_data, self._get_headers())
            self._check_error(response, 400, 'Bad Request', "'name' is a required property")

    def test_post_user_correct_request(self):
        """Correct request"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            request_data = {'username': 'user3',
                            'name': 'User 3',
                            'email': 'user3@users.com',
                            'role': 'USER',
                            'daily_calories': 2500,
                            'password': 'pass_user3'}
            expected = request_data.copy()
            expected.pop('password')
            response = self.post(path, request_data, self._get_headers())
            self._check_succes(expected, response, 201)

    def test_post_user_username_exists(self):
        """Username exists"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            request_data = {'username': 'user1',
                            'name': 'User 1',
                            'email': 'user1@users.com',
                            'role': 'USER',
                            'daily_calories': 2500,
                            'password': 'pass_user1'}
            response = self.post(path, request_data, self._get_headers())
            self._check_error(response, 409, 'Conflict', "User 'user1' exists already")

    def test_post_user_user_add_user(self):
        """Role user tries to add user"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            request_data = {'username': 'user4',
                            'name': 'User 4',
                            'email': 'user4@users.com',
                            'role': 'USER',
                            'daily_calories': 2500,
                            'password': 'pass_user4'}

            response = self.post(path, request_data, self._get_headers('user1', 'pass_user1'))
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")

    def test_post_user_manager_add_user(self):
        """Manager tries to add a user"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            request_data = {'username': 'user4',
                            'name': 'User 4',
                            'email': 'user4@users.com',
                            'role': 'USER',
                            'daily_calories': 2500,
                            'password': 'pass_user4'}
            expected = request_data.copy()
            expected.pop('password')
            response = self.post(path, request_data, self._get_headers('manager1', 'pass_manager1'))
            self._check_succes(expected, response, 201)

    def test_delete_user_unauthenticated(self):
        """Unauthenticated request"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            response = self.delete('/'.join([path, 'user1']), None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

    def test_delete_user_user_not_allowed(self):
        """User cannot delete other users"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            response = self.delete('/'.join([path, 'manager1']), self._get_headers('user1', 'pass_user1'))
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")

    def test_delete_user_user_himself(self):
        """User can delete himself"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            expected = None
            response = self.delete('/'.join([path, 'user1']), self._get_headers('user1', 'pass_user1'))
            self._check_succes(expected, response, 200)

    def test_delete_user_manager_to_manager(self):
        """Managers cannot delete managers"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            response = self.delete('/'.join([path, 'manager2']), self._get_headers('manager1', 'pass_manager1'))
            self._check_error(response, 401, 'Unauthorized', "User 'manager1' can only delete users with role USER")

    def test_delete_user_not_exists(self):
        """Error deleting non existing user"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            response = self.delete('/'.join([path, 'user4']), self._get_headers('manager1', 'pass_manager1'))
            self._check_error(response, 404, 'Not Found', "User 'user4' not found")

    def test_get_user_unauthenticated(self):
        """Unauthenticated request"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            response = self.get('/'.join([path, 'user1']), None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

    def test_get_user_user_other(self):
        """User cannot get other users"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            response = self.get('/'.join([path, 'manager1']), self._get_headers('user1', 'pass_user1'))
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")

    def test_get_user_himself(self):
        """User can get himself request"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            expected = {'daily_calories': 2500, 'email': 'user1@usermail.com', 'name': 'User 1', 'role': 'USER',
                        'username': 'user1'}
            response = self.get('/'.join([path, 'user1']), self._get_headers('user1', 'pass_user1'))
            self._check_succes(expected, response, 200)

    def test_get_user_manager_users(self):
        """User managers can get users"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            expected = {'daily_calories': 4000, 'email': 'manager2@managermail.com', 'name': 'Manager 2',
                        'role': 'MANAGER', 'username': 'manager2'}
            response = self.get('/'.join([path, 'manager2']), self._get_headers('manager1', 'pass_manager1'))
            self._check_succes(expected, response, 200)

    def test_get_user_error_not_found(self):
        """Error getting non existing user"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            response = self.get('/'.join([path, 'user3']), self._get_headers('manager1', 'pass_manager1'))
            self._check_error(response, 404, 'Not Found', "User 'user3' not found")

    def test_put_user_unauthenticated(self):
        """Unauthenticated request"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.put('/'.join([path, 'user1']), request_data, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

    def test_put_user_user_other_users(self):
        """User cannot get other users"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.put('/'.join([path, 'manager1']), request_data, self._get_headers('user1', 'pass_user1'))
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'user1' belongs to the role 'USER' and is not allowed to perform the action")

    def test_put_user_user_himself(self):
        """User can put himself"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            expected = {'daily_calories': 2500, 'email': 'user1@usermail.com', 'name': 'User 1A', 'role': 'USER',
                        'username': 'user1a'}
            request_data = {'username': 'user1a', 'password': 'new_password', 'name': 'User 1A'}
            response = self.put('/'.join([path, 'user1']), request_data, self._get_headers('user1', 'pass_user1'))
            self._check_succes(expected, response, 200)

    def test_put_user_manager_user(self):
        """User managers can put users"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            expected = {'daily_calories': 2500, 'email': 'user1@usermail.com', 'name': 'User 1', 'role': 'USER',
                        'username': 'user1'}
            request_data = {'password': 'new_password'}
            response = self.put('/'.join([path, 'user1']), request_data, self._get_headers('manager1', 'pass_manager1'))
            self._check_succes(expected, response, 200)

    def test_put_user_non_existing(self):
        """Error getting non existing user"""
        path = '/'.join([self.path, 'users'])
        with self.client:
            request_data = {'password': 'new_password'}
            response = self.put('/'.join([path, 'user3']), request_data, self._get_headers('manager1', 'pass_manager1'))
            self._check_error(response, 404, 'Not Found', "User 'user3' not found")

    def test_get_user_meals_unauthenticated(self):
        """Unauthenticated request request"""
        path = '/'.join([self.path, 'users', 'user1', 'meals'])
        with self.client:
            response = self.get(path, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

    def test_get_user_meals_success_admin(self):
        """Successful request as admin"""
        path = '/'.join([self.path, 'users', 'user1', 'meals'])
        with self.client:
            expected = [{'calories': 500, 'date': '2020-02-11', 'description': 'Meal 1 User 1', 'grams': 100, 'id': 1,
                         'name': 'meal 1', 'time': '15:00:03', 'under_daily_total': True},
                        {'calories': 2100, 'date': '2020-02-11', 'description': 'Meal 2 User 1', 'grams': 100, 'id': 2,
                         'name': 'meal 2', 'time': '15:10:03', 'under_daily_total': True}]
            response = self.get(path, self._get_headers())
            self._check_succes(expected, response, 200)

    def test_get_user_meals_user_himself(self):
        """User is allowed to see its own meals"""
        path = '/'.join([self.path, 'users', 'user1', 'meals'])
        with self.client:
            expected = [{'calories': 500, 'date': '2020-02-11', 'description': 'Meal 1 User 1', 'grams': 100, 'id': 1,
                         'name': 'meal 1', 'time': '15:00:03', 'under_daily_total': True},
                        {'calories': 2100, 'date': '2020-02-11', 'description': 'Meal 2 User 1', 'grams': 100, 'id': 2,
                         'name': 'meal 2', 'time': '15:10:03', 'under_daily_total': True}]
            response = self.get(path, self._get_headers('user1', 'pass_user1'))
            self._check_succes(expected, response, 200)

    def test_get_user_meals_user_others(self):
        """User is not allowed to see other user meals"""
        path = '/'.join([self.path, 'users', 'user2', 'meals'])
        with self.client:
            response = self.get(path, self._get_headers('user1', 'pass_user1'))
            self._check_error(response, 401, 'Unauthorized', "User 'user1' cannot perform the action for other user")

    def test_get_user_manager_others(self):
        """Managers are not allowed to see other meals"""
        path = '/'.join([self.path, 'users', 'user1', 'meals'])
        with self.client:
            response = self.get(path, self._get_headers('manager1', 'pass_manager1'))
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

    def test_get_user_meals_managers_himself(self):
        """Managers are not allowed to see their own meals"""
        path = '/'.join([self.path, 'users', 'manager1', 'meals'])
        with self.client:
            response = self.get(path, self._get_headers('manager1', 'pass_manager1'))
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

    def test_post_meal_unauthenticated(self):
        """Unauthenticated request"""
        path = '/'.join([self.path, 'users', 'user1', 'meals'])
        with self.client:
            request_data = {'username': 'admin', 'password': 'admin1234'}
            response = self.post(path, request_data, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

    def test_post_meal_missing_parameters(self):
        """Request missing parameters"""
        path = '/'.join([self.path, 'users', 'user1', 'meals'])
        with self.client:
            request_data = {'description': 'description', 'calories': 0}
            response = self.post(path, request_data, self._get_headers())
            self._check_error(response, 400, 'Bad Request', "'date' is a required property")

    def test_post_meal_wrong_params(self):
        """Wrongly formatted parameters"""
        path = '/'.join([self.path, 'users', 'user1', 'meals'])
        with self.client:
            request_data = {"date": '2020/11/2',
                            "time": '15:99:28',
                            "name": "meal 3",
                            "grams": 800,
                            "description": "Meal 3 User 1",
                            "calories": 500}
            response = self.post(path, request_data, self._get_headers())
            self._check_error(response, 400, 'Bad Request', "Field(s): 'date', 'time' have the wrong format")

    def test_post_meal_success_admin(self):
        """Correct request from admin"""
        path = '/'.join([self.path, 'users', 'user1', 'meals'])
        with self.client:
            expected = {'calories': 500, 'date': '2020-02-11', 'description': 'Meal 3 User 1', 'grams': 800, 'id': 4,
                        'name': 'meal 3', 'time': '15:05:28', 'under_daily_total': False}
            request_data = {"date": '2020-02-11', "time": '15:05:28', "name": "meal 3", "grams": 800,
                            "description": "Meal 3 User 1", "calories": 500}
            response = self.post(path, request_data, self._get_headers())
            self._check_succes(expected, response, 201)

    def test_post_meal_wrong_user_admin(self):
        """Wrong user from admin"""
        path = '/'.join([self.path, 'users', 'wronguser', 'meals'])
        with self.client:
            request_data = {"date": '2020-02-11', "time": '15:05:28', "name": "meal 3", "grams": 800,
                            "description": "Meal 3 User 1", "calories": 500}
            response = self.post(path, request_data, self._get_headers())
            self._check_error(response, 404, 'Not Found', "User 'wronguser' not found")

    def test_post_meal_user_himself(self):
        """User can add meals to himself"""
        path = '/'.join([self.path, 'users', 'user1', 'meals'])
        with self.client:
            request_data = {"date": '2020-02-11', "time": '15:05:28', "name": "meal 3", "grams": 800,
                            "description": "Meal 3 User 1", "calories": 500}
            expected = {'calories': 500, 'date': '2020-02-11', 'description': 'Meal 3 User 1', 'grams': 800, 'id': 4,
                        'name': 'meal 3', 'time': '15:05:28', 'under_daily_total': False}
            response = self.post(path, request_data, self._get_headers('user1', 'pass_user1'))
            self._check_succes(expected, response, 201)

    def test_post_meal_user_under_daily_total(self):
        """User can add meals to himself under daily total"""
        path = '/'.join([self.path, 'users', 'user1', 'meals'])
        with self.client:
            expected = {'calories': 500, 'date': '2020-02-12', 'description': 'Meal 4 User 1', 'grams': 800, 'id': 4,
                        'name': 'meal 4', 'time': '15:05:28', 'under_daily_total': True}
            request_data = {"date": '2020-02-12', "time": '15:05:28', "name": "meal 4", "grams": 800,
                            "description": "Meal 4 User 1", "calories": 500}
            response = self.post(path, request_data, self._get_headers('user1', 'pass_user1'))
            self._check_succes(expected, response, 201)

    def test_post_meal_user_others(self):
        """User cannot add meals other users"""
        path = '/'.join([self.path, 'users', 'user2', 'meals'])
        with self.client:
            request_data = {"date": '2020-02-12', "time": '15:05:28', "name": "meal 4", "grams": 800,
                            "description": "Meal 4 User 1", "calories": 500}
            response = self.post(path, request_data, self._get_headers('user1', 'pass_user1'))
            self._check_error(response, 401, 'Unauthorized', "User 'user1' cannot perform the action for other user")

    def test_post_manager_others(self):
        """Managers cannot add meals to other users"""
        path = '/'.join([self.path, 'users', 'user2', 'meals'])
        with self.client:
            request_data = {"date": '2020-02-12', "time": '15:05:28', "name": "meal 4", "grams": 800,
                            "description": "Meal 4 User 1", "calories": 500}
            response = self.post(path, request_data, self._get_headers('manager1', 'pass_manager1'))
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

    def test_post_meal_manager_himself(self):
        """Managers cannot add meals to themselves"""
        path = '/'.join([self.path, 'users', 'manager1', 'meals'])
        with self.client:
            request_data = {"date": '2020-02-12', "time": '15:05:28', "name": "meal 4", "grams": 800,
                            "description": "Meal 4 User 1", "calories": 500}
            response = self.post(path, request_data, self._get_headers('manager1', 'pass_manager1'))
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

    def test_delete_meal_unauthenticated(self):
        """Unauthenticated request"""
        path = '/'.join([self.path, 'users', 'user1', 'meals', '1'])
        with self.client:
            response = self.delete(path, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

    def test_delete_meal_admin_success(self):
        """Admin can delete a meal"""
        path = '/'.join([self.path, 'users', 'user1', 'meals', '1'])
        with self.client:
            expected = None
            response = self.delete(path, self._get_headers())
            self._check_succes(expected, response, 200)

    def test_delete_meal_admin_wrong_user(self):
        """Unauthenticated request"""
        path = '/'.join([self.path, 'users', 'wronguser', 'meals', '1'])
        with self.client:
            # Admin mistake on user
            response = self.delete(path, self._get_headers())
            self._check_error(response, 404, 'Not Found', "User 'wronguser' not found")

    def test_delete_meal_user_others(self):
        """User cannot delete other users meals"""
        path = '/'.join([self.path, 'users', 'user2', 'meals', '3'])
        with self.client:
            # User cannot delete other users meals
            response = self.delete(path, self._get_headers('user1', 'pass_user1'))
            self._check_error(response, 401, 'Unauthorized', "User 'user1' cannot perform the action for other user")

    def test_delete_meal_user_himself(self):
        """User can delete his own meals"""
        path = '/'.join([self.path, 'users', 'user1', 'meals', '2'])
        with self.client:
            expected = None
            response = self.delete(path, self._get_headers('user1', 'pass_user1'))
            self._check_succes(expected, response, 200)

    def test_delete_meal_no_meal(self):
        """Meal doesnt exist"""
        path = '/'.join([self.path, 'users', 'user1', 'meals', '4'])
        with self.client:
            response = self.delete(path, self._get_headers('user1', 'pass_user1'))
            self._check_error(response, 404, 'Not Found', "Meal '4' not found")

    def test_delete_meal_manager_own(self):
        """User managers cannot delete their meals"""
        path = '/'.join([self.path, 'users', 'manager1', 'meals', '1'])
        with self.client:
            response = self.delete(path, self._get_headers('manager1', 'pass_manager1'))
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

    def test_delete_meal_manager_others(self):
        """User managers cannot delete meals"""
        path = '/'.join([self.path, 'users', 'user2', 'meals', '1'])
        with self.client:
            response = self.delete(path, self._get_headers('manager1', 'pass_manager1'))
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

    def test_get_meal_unauthenticated(self):
        """Unauthenticated request"""
        path = '/'.join([self.path, 'users', 'user1', 'meals', '1'])
        with self.client:
            response = self.get(path, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

    def test_get_meal_success_admin(self):
        """Admin can see any meal"""
        path = '/'.join([self.path, 'users', 'user1', 'meals', '1'])
        with self.client:
            expected = {'calories': 500, 'date': '2020-02-11', 'description': 'Meal 1 User 1', 'grams': 100, 'id': 1,
                        'name': 'meal 1', 'time': '15:00:03', 'under_daily_total': True}
            response = self.get(path, self._get_headers())
            self._check_succes(expected, response, 200)

    def test_get_meal_wrong_user(self):
        """Admin mistake on user"""
        path = '/'.join([self.path, 'users', 'wronguser', 'meals', '1'])
        with self.client:
            response = self.get(path, self._get_headers())
            self._check_error(response, 404, 'Not Found', "User 'wronguser' not found")

    def test_get_meal_user_others(self):
        """User cannot get other users meals"""
        path = '/'.join([self.path, 'users', 'user2', 'meals', '3'])
        with self.client:
            response = self.get(path, self._get_headers('user1', 'pass_user1'))
            self._check_error(response, 401, 'Unauthorized', "User 'user1' cannot perform the action for other user")

    def test_get_meal_user_own(self):
        """User can get his own meals"""
        path = '/'.join([self.path, 'users', 'user1', 'meals', '1'])
        with self.client:
            expected = {'calories': 500, 'date': '2020-02-11', 'description': 'Meal 1 User 1', 'grams': 100, 'id': 1,
                        'name': 'meal 1', 'time': '15:00:03', 'under_daily_total': True}
            response = self.get(path, self._get_headers('user1', 'pass_user1'))
            self._check_succes(expected, response, 200)

    def test_get_meal_user_no_meal(self):
        """Meal doesnt exist"""
        path = '/'.join([self.path, 'users', 'user1', 'meals', '4'])
        with self.client:
            response = self.get(path, self._get_headers('user1', 'pass_user1'))
            self._check_error(response, 404, 'Not Found', "Meal '4' not found")

    def test_get_meal_manager_own(self):
        """Managers cannot get their meals"""
        path = '/'.join([self.path, 'users', 'manager1', 'meals', '1'])
        with self.client:
            response = self.get(path, self._get_headers('manager1', 'pass_manager1'))
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

    def test_get_meal_manager_others(self):
        """Managers cannot get meals belonging to others"""
        path = '/'.join([self.path, 'users', 'manager2', 'meals', '1'])
        with self.client:
            response = self.get(path, self._get_headers('manager1', 'pass_manager1'))
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

    def test_put_meal_unauthenticated(self):
        """Unauthenticated request"""
        path = '/'.join([self.path, 'users', 'user1', 'meals', '2'])
        with self.client:
            response = self.get(path, None)
            self._check_error(response, 401, 'Unauthorized', 'No authorization token provided')

    def test_put_meal_success_admin(self):
        """Admin can put any meal"""
        path = '/'.join([self.path, 'users', 'user1', 'meals', '2'])
        with self.client:
            expected = {'calories': 500, 'date': '2020-02-11', 'description': 'Meal 1 User 1b', 'grams': 800, 'id': 2,
                        'name': 'meal 1b', 'time': '15:10:03', 'under_daily_total': True}
            request_data = {'calories': 500, 'description': 'Meal 1 User 1b', 'grams': 800, 'name': 'meal 1b'}
            response = self.put(path, request_data, self._get_headers())
            self._check_succes(expected, response, 200)

    def test_put_meal_admin_wrong_user(self):
        """Admin mistake on user"""
        path = '/'.join([self.path, 'users', 'wronguser', 'meals', '2'])
        with self.client:
            request_data = {'calories': 500, 'description': 'Meal 1 User 1b', 'grams': 800, 'name': 'meal 1b'}
            response = self.put(path, request_data, self._get_headers())
            self._check_error(response, 404, 'Not Found', "User 'wronguser' not found")

    def test_put_meal_user_others(self):
        """User cannot put other users meals"""
        path = '/'.join([self.path, 'users', 'user2', 'meals', '3'])
        with self.client:
            request_data = {'calories': 500, 'description': 'Meal 1 User 1b', 'grams': 800, 'name': 'meal 1b'}
            response = self.put(path, request_data, self._get_headers('user1', 'pass_user1'))
            self._check_error(response, 401, 'Unauthorized', "User 'user1' cannot perform the action for other user")

    def test_put_meal_user_own(self):
        """User can put his own meals"""
        path = '/'.join([self.path, 'users', 'user1', 'meals', '1'])
        with self.client:
            expected = {'calories': 5000, 'date': '2020-02-13', 'description': 'Meal 1 User 1', 'grams': 100, 'id': 1,
                        'name': 'meal 1', 'time': '15:00:03', 'under_daily_total': False}
            request_data = {'calories': 5000, 'date': '2020-02-13'}
            response = self.put(path, request_data, self._get_headers('user1', 'pass_user1'))
            self._check_succes(expected, response, 200)

    def test_put_meal_no_meal(self):
        """Meal doesnt exist"""
        path = '/'.join([self.path, 'users', 'user1', 'meals', '4'])
        with self.client:
            request_data = {'calories': 5000, 'date': '2020-02-13'}
            response = self.put(path, request_data, self._get_headers('user1', 'pass_user1'))
            self._check_error(response, 404, 'Not Found', "Meal '4' not found")

    def test_put_meal_manager_own(self):
        """User managers cannot put their meals"""
        path = '/'.join([self.path, 'users', 'manager', 'meals', '4'])
        with self.client:
            request_data = {'calories': 5000, 'date': '2020-02-13'}
            response = self.put(path, request_data, self._get_headers('manager1', 'pass_manager1'))
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")

    def test_put_meal_manager_others(self):
        """User managers cannot put meals"""
        path = '/'.join([self.path, 'users', 'user1', 'meals', '2'])
        with self.client:
            request_data = {'calories': 5000, 'date': '2020-02-13'}
            response = self.put(path, request_data, self._get_headers('manager1', 'pass_manager1'))
            self._check_error(response, 401,
                              'Unauthorized',
                              "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action")


if __name__ == '__main__':
    unittest.main()

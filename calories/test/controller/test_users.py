"""Test module for calories.main.controller.users"""

import unittest
from urllib.parse import quote

from calories.test.controller import TestAPI


class TestUsers(TestAPI):
    """Test class for calories.main.controller.users"""

    def test_get_all_users_unauthenticated(self):
        """Unauthenticated request"""
        path = "/".join([self.path, "users"])
        with self.client:
            response = self.get(path, None)
            self._check_error(
                response, 401, "Unauthorized", "No authorization token provided"
            )

    def test_get_all_users_success_admin(self):
        """Successful request as admin"""
        path = "/".join([self.path, "users"])
        with self.client:
            expected = [
                {
                    "daily_calories": 0,
                    "email": "admin@adminmail.com",
                    "name": "Administrator",
                    "role": "ADMIN",
                    "username": "admin",
                },
                {
                    "daily_calories": 2000,
                    "email": "manager1@managermail.com",
                    "name": "Manager 1",
                    "role": "MANAGER",
                    "username": "manager1",
                },
                {
                    "daily_calories": 4000,
                    "email": "manager2@managermail.com",
                    "name": "Manager 2",
                    "role": "MANAGER",
                    "username": "manager2",
                },
                {
                    "daily_calories": 2500,
                    "email": "user1@usermail.com",
                    "name": "User 1",
                    "role": "USER",
                    "username": "user1",
                },
                {
                    "daily_calories": 3000,
                    "email": "user2@usemail.com",
                    "name": "User 2",
                    "role": "USER",
                    "username": "user2",
                },
            ]
            response = self.get(path, self._get_headers())
            self._check_succes(expected, response, 200)

    def test_get_all_users_user_not_allowed(self):
        """User is not allowed to see user list"""
        path = "/".join([self.path, "users"])
        with self.client:
            response = self.get(path, self._get_headers("user1", "pass_user1"))
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'user1' belongs to the role 'USER' and is not allowed to perform the action",
            )

    def test_get_all_users_manager_allowed(self):
        """Manager is allowed to see user list"""
        path = "/".join([self.path, "users"])
        with self.client:
            expected = [
                {
                    "daily_calories": 0,
                    "email": "admin@adminmail.com",
                    "name": "Administrator",
                    "role": "ADMIN",
                    "username": "admin",
                },
                {
                    "daily_calories": 2000,
                    "email": "manager1@managermail.com",
                    "name": "Manager 1",
                    "role": "MANAGER",
                    "username": "manager1",
                },
                {
                    "daily_calories": 4000,
                    "email": "manager2@managermail.com",
                    "name": "Manager 2",
                    "role": "MANAGER",
                    "username": "manager2",
                },
                {
                    "daily_calories": 2500,
                    "email": "user1@usermail.com",
                    "name": "User 1",
                    "role": "USER",
                    "username": "user1",
                },
                {
                    "daily_calories": 3000,
                    "email": "user2@usemail.com",
                    "name": "User 2",
                    "role": "USER",
                    "username": "user2",
                },
            ]
            response = self.get(path, self._get_headers("manager1", "pass_manager1"))
            self._check_succes(expected, response, 200)

    def test_get_all_users_manager_allowed_first_page(self):
        """Manager is allowed to see user list, test pagination: first page"""
        path = "/".join([self.path, "users"])
        with self.client:
            expected = [
                {
                    "daily_calories": 0,
                    "email": "admin@adminmail.com",
                    "name": "Administrator",
                    "role": "ADMIN",
                    "username": "admin",
                },
                {
                    "daily_calories": 2000,
                    "email": "manager1@managermail.com",
                    "name": "Manager 1",
                    "role": "MANAGER",
                    "username": "manager1",
                },
            ]
            paged_path = path + "?items_per_page=2&page_number=1"
            response = self.get(
                paged_path, self._get_headers("manager1", "pass_manager1")
            )
            self._check_succes(expected, response, 200)

    def test_get_all_users_manager_allowed_last_page(self):
        """Manager is allowed to see user list, test pagination: last page"""
        path = "/".join([self.path, "users"])
        with self.client:
            expected = [
                {
                    "daily_calories": 3000,
                    "email": "user2@usemail.com",
                    "name": "User 2",
                    "role": "USER",
                    "username": "user2",
                }
            ]
            paged_path = path + "?items_per_page=2&page_number=3"
            response = self.get(
                paged_path, self._get_headers("manager1", "pass_manager1")
            )
            self._check_succes(expected, response, 200)

    def test_get_all_users_manager_allowed_beyond_last_page(self):
        """Manager is allowed to see user list, test pagination: beyond last page"""
        path = "/".join([self.path, "users"])
        with self.client:
            expected = []
            paged_path = path + "?items_per_page=2&page_number=20"
            response = self.get(
                paged_path, self._get_headers("manager1", "pass_manager1")
            )
            self._check_succes(expected, response, 200)

    def test_get_all_users_manager_allowed_filtering1(self):
        """Manager is allowed to see user list, filtering 1"""
        path = "/".join([self.path, "users"])
        with self.client:
            expected = [
                {
                    "daily_calories": 3000,
                    "email": "user2@usemail.com",
                    "name": "User 2",
                    "role": "USER",
                    "username": "user2",
                }
            ]
            filtered_path = (
                    path
                    + "?filter_results="
                    + quote(
                "(username ne 'user1') AND "
                "((daily_calories gt 2200) AND (daily_calories lt 3500))"
            )
            )
            response = self.get(
                filtered_path, self._get_headers("manager1", "pass_manager1")
            )
            self._check_succes(expected, response, 200)

    def test_get_all_users_manager_allowed_filtering2(self):
        """Manager is allowed to see user list, filtering 2"""
        path = "/".join([self.path, "users"])
        with self.client:
            filtered_path = path + "?filter_results=" + quote("wrongfilter")
            response = self.get(
                filtered_path, self._get_headers("manager1", "pass_manager1")
            )
            self._check_error(
                response, 400, "Bad Request", "Filter 'wrongfilter' is invalid"
            )

    def test_post_user_unauthenticated(self):
        """Unauthenticated request"""
        path = "/".join([self.path, "users"])
        with self.client:
            request_data = {"username": "admin", "password": "admin1234"}
            response = self.post(path, request_data, None)
            self._check_error(
                response, 401, "Unauthorized", "No authorization token provided"
            )

    def test_post_user_missing_parameters(self):
        """Request missing parameters"""
        path = "/".join([self.path, "users"])
        with self.client:
            request_data = {"username": "admin", "password": "admin1234"}
            response = self.post(path, request_data, self._get_headers())
            self._check_error(
                response, 400, "Bad Request", "'name' is a required property"
            )

    def test_post_user_correct_request(self):
        """Correct request"""
        path = "/".join([self.path, "users"])
        with self.client:
            request_data = {
                "username": "user3",
                "name": "User 3",
                "email": "user3@users.com",
                "role": "USER",
                "daily_calories": 2500,
                "password": "pass_user3",
            }
            expected = request_data.copy()
            expected.pop("password")
            response = self.post(path, request_data, self._get_headers())
            self._check_succes(expected, response, 201)

    def test_post_user_username_exists(self):
        """Username exists"""
        path = "/".join([self.path, "users"])
        with self.client:
            request_data = {
                "username": "user1",
                "name": "User 1",
                "email": "user1@users.com",
                "role": "USER",
                "daily_calories": 2500,
                "password": "pass_user1",
            }
            response = self.post(path, request_data, self._get_headers())
            self._check_error(response, 409, "Conflict", "User 'user1' exists already")

    def test_post_user_user_add_user(self):
        """Role user tries to add user"""
        path = "/".join([self.path, "users"])
        with self.client:
            request_data = {
                "username": "user4",
                "name": "User 4",
                "email": "user4@users.com",
                "role": "USER",
                "daily_calories": 2500,
                "password": "pass_user4",
            }

            response = self.post(
                path, request_data, self._get_headers("user1", "pass_user1")
            )
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'user1' belongs to the role 'USER' and is not allowed to perform the action",
            )

    def test_post_user_manager_add_user(self):
        """Manager tries to add a user"""
        path = "/".join([self.path, "users"])
        with self.client:
            request_data = {
                "username": "user4",
                "name": "User 4",
                "email": "user4@users.com",
                "role": "USER",
                "daily_calories": 2500,
                "password": "pass_user4",
            }
            expected = request_data.copy()
            expected.pop("password")
            response = self.post(
                path, request_data, self._get_headers("manager1", "pass_manager1")
            )
            self._check_succes(expected, response, 201)

    def test_delete_user_unauthenticated(self):
        """Unauthenticated request"""
        path = "/".join([self.path, "users"])
        with self.client:
            response = self.delete("/".join([path, "user1"]), None)
            self._check_error(
                response, 401, "Unauthorized", "No authorization token provided"
            )

    def test_delete_user_user_not_allowed(self):
        """User cannot delete other users"""
        path = "/".join([self.path, "users"])
        with self.client:
            response = self.delete(
                "/".join([path, "manager1"]), self._get_headers("user1", "pass_user1")
            )
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'user1' belongs to the role 'USER' and is not allowed to perform the action",
            )

    def test_delete_user_user_himself(self):
        """User can delete himself"""
        path = "/".join([self.path, "users"])
        with self.client:
            expected = None
            response = self.delete(
                "/".join([path, "user1"]), self._get_headers("user1", "pass_user1")
            )
            self._check_succes(expected, response, 200)

    def test_delete_user_manager_to_manager(self):
        """Managers cannot delete managers"""
        path = "/".join([self.path, "users"])
        with self.client:
            response = self.delete(
                "/".join([path, "manager2"]),
                self._get_headers("manager1", "pass_manager1"),
            )
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'manager1' can only delete users with role USER",
            )

    def test_delete_user_not_exists(self):
        """Error deleting non existing user"""
        path = "/".join([self.path, "users"])
        with self.client:
            response = self.delete(
                "/".join([path, "user4"]),
                self._get_headers("manager1", "pass_manager1"),
            )
            self._check_error(response, 404, "Not Found", "User 'user4' not found")

    def test_get_user_unauthenticated(self):
        """Unauthenticated request"""
        path = "/".join([self.path, "users"])
        with self.client:
            response = self.get("/".join([path, "user1"]), None)
            self._check_error(
                response, 401, "Unauthorized", "No authorization token provided"
            )

    def test_get_user_user_other(self):
        """User cannot get other users"""
        path = "/".join([self.path, "users"])
        with self.client:
            response = self.get(
                "/".join([path, "manager1"]), self._get_headers("user1", "pass_user1")
            )
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'user1' belongs to the role 'USER' and is not allowed to perform the action",
            )

    def test_get_user_himself(self):
        """User can get himself request"""
        path = "/".join([self.path, "users"])
        with self.client:
            expected = {
                "daily_calories": 2500,
                "email": "user1@usermail.com",
                "name": "User 1",
                "role": "USER",
                "username": "user1",
            }
            response = self.get(
                "/".join([path, "user1"]), self._get_headers("user1", "pass_user1")
            )
            self._check_succes(expected, response, 200)

    def test_get_user_manager_users(self):
        """User managers can get users"""
        path = "/".join([self.path, "users"])
        with self.client:
            expected = {
                "daily_calories": 4000,
                "email": "manager2@managermail.com",
                "name": "Manager 2",
                "role": "MANAGER",
                "username": "manager2",
            }
            response = self.get(
                "/".join([path, "manager2"]),
                self._get_headers("manager1", "pass_manager1"),
            )
            self._check_succes(expected, response, 200)

    def test_get_user_error_not_found(self):
        """Error getting non existing user"""
        path = "/".join([self.path, "users"])
        with self.client:
            response = self.get(
                "/".join([path, "user3"]),
                self._get_headers("manager1", "pass_manager1"),
            )
            self._check_error(response, 404, "Not Found", "User 'user3' not found")

    def test_put_user_unauthenticated(self):
        """Unauthenticated request"""
        path = "/".join([self.path, "users"])
        with self.client:
            request_data = {"username": "admin", "password": "admin1234"}
            response = self.put("/".join([path, "user1"]), request_data, None)
            self._check_error(
                response, 401, "Unauthorized", "No authorization token provided"
            )

    def test_put_user_user_other_users(self):
        """User cannot get other users"""
        path = "/".join([self.path, "users"])
        with self.client:
            request_data = {"username": "admin", "password": "admin1234"}
            response = self.put(
                "/".join([path, "manager1"]),
                request_data,
                self._get_headers("user1", "pass_user1"),
            )
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'user1' belongs to the role 'USER' and is not allowed to perform the action",
            )

    def test_put_user_user_himself(self):
        """User can put himself"""
        path = "/".join([self.path, "users"])
        with self.client:
            expected = {
                "daily_calories": 2500,
                "email": "user1@usermail.com",
                "name": "User 1A",
                "role": "USER",
                "username": "user1a",
            }
            request_data = {
                "username": "user1a",
                "password": "new_password",
                "name": "User 1A",
            }
            response = self.put(
                "/".join([path, "user1"]),
                request_data,
                self._get_headers("user1", "pass_user1"),
            )
            self._check_succes(expected, response, 200)

    def test_put_user_manager_user(self):
        """User managers can put users"""
        path = "/".join([self.path, "users"])
        with self.client:
            expected = {
                "daily_calories": 2500,
                "email": "user1@usermail.com",
                "name": "User 1",
                "role": "USER",
                "username": "user1",
            }
            request_data = {"password": "new_password"}
            response = self.put(
                "/".join([path, "user1"]),
                request_data,
                self._get_headers("manager1", "pass_manager1"),
            )
            self._check_succes(expected, response, 200)

    def test_put_user_non_existing(self):
        """Error getting non existing user"""
        path = "/".join([self.path, "users"])
        with self.client:
            request_data = {"password": "new_password"}
            response = self.put(
                "/".join([path, "user3"]),
                request_data,
                self._get_headers("manager1", "pass_manager1"),
            )
            self._check_error(response, 404, "Not Found", "User 'user3' not found")


if __name__ == "__main__":
    unittest.main()

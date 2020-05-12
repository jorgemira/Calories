"""Test module for calories.main.controller.meals"""
import unittest

from calories.test.controller import TestAPI


class TestMeals(TestAPI):
    """Test class for calories.main.controller.meals"""

    def test_get_user_meals_unauthenticated(self):
        """Unauthenticated request request"""
        path = "/".join([self.path, "users", "user1", "meals"])
        with self.client:
            response = self.get(path, None)
            self._check_error(
                response, 401, "Unauthorized", "No authorization token provided"
            )

    def test_get_user_meals_success_admin(self):
        """Successful request as admin"""
        path = "/".join([self.path, "users", "user1", "meals"])
        with self.client:
            expected = [
                {
                    "calories": 500,
                    "date": "2020-02-11",
                    "description": "Meal 1 User 1",
                    "grams": 100,
                    "id": 1,
                    "name": "meal 1",
                    "time": "15:00:03",
                    "under_daily_total": True,
                },
                {
                    "calories": 2100,
                    "date": "2020-02-11",
                    "description": "Meal 2 User 1",
                    "grams": 100,
                    "id": 2,
                    "name": "meal 2",
                    "time": "15:10:03",
                    "under_daily_total": True,
                },
            ]
            response = self.get(path, self._get_headers())
            self._check_succes(expected, response, 200)

    def test_get_user_meals_user_himself(self):
        """User is allowed to see its own meals"""
        path = "/".join([self.path, "users", "user1", "meals"])
        with self.client:
            expected = [
                {
                    "calories": 500,
                    "date": "2020-02-11",
                    "description": "Meal 1 User 1",
                    "grams": 100,
                    "id": 1,
                    "name": "meal 1",
                    "time": "15:00:03",
                    "under_daily_total": True,
                },
                {
                    "calories": 2100,
                    "date": "2020-02-11",
                    "description": "Meal 2 User 1",
                    "grams": 100,
                    "id": 2,
                    "name": "meal 2",
                    "time": "15:10:03",
                    "under_daily_total": True,
                },
            ]
            response = self.get(path, self._get_headers("user1", "pass_user1"))
            self._check_succes(expected, response, 200)

    def test_get_user_meals_user_others(self):
        """User is not allowed to see other user meals"""
        path = "/".join([self.path, "users", "user2", "meals"])
        with self.client:
            response = self.get(path, self._get_headers("user1", "pass_user1"))
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'user1' cannot perform the action for other user",
            )

    def test_get_user_manager_others(self):
        """Managers are not allowed to see other meals"""
        path = "/".join([self.path, "users", "user1", "meals"])
        with self.client:
            response = self.get(path, self._get_headers("manager1", "pass_manager1"))
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action",
            )

    def test_get_user_meals_managers_himself(self):
        """Managers are not allowed to see their own meals"""
        path = "/".join([self.path, "users", "manager1", "meals"])
        with self.client:
            response = self.get(path, self._get_headers("manager1", "pass_manager1"))
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action",
            )

    def test_post_meal_unauthenticated(self):
        """Unauthenticated request"""
        path = "/".join([self.path, "users", "user1", "meals"])
        with self.client:
            request_data = {"username": "admin", "password": "admin1234"}
            response = self.post(path, request_data, None)
            self._check_error(
                response, 401, "Unauthorized", "No authorization token provided"
            )

    def test_post_meal_missing_parameters(self):
        """Request missing parameters"""
        path = "/".join([self.path, "users", "user1", "meals"])
        with self.client:
            request_data = {"description": "description", "calories": 0}
            response = self.post(path, request_data, self._get_headers())
            self._check_error(
                response, 400, "Bad Request", "'name' is a required property"
            )

    def test_post_meal_wrong_params(self):
        """Wrongly formatted parameters"""
        path = "/".join([self.path, "users", "user1", "meals"])
        with self.client:
            request_data = {
                "date": "2020/11/2",
                "time": "15:99:28",
                "name": "meal 3",
                "grams": 800,
                "description": "Meal 3 User 1",
                "calories": 500,
            }
            response = self.post(path, request_data, self._get_headers())
            self._check_error(
                response,
                400,
                "Bad Request",
                "Field(s): 'date', 'time' have the wrong format",
            )

    def test_post_meal_success_admin(self):
        """Correct request from admin"""
        path = "/".join([self.path, "users", "user1", "meals"])
        with self.client:
            expected = {
                "calories": 500,
                "date": "2020-02-11",
                "description": "Meal 3 User 1",
                "grams": 800,
                "id": 4,
                "name": "meal 3",
                "time": "15:05:28",
                "under_daily_total": False,
            }
            request_data = {
                "date": "2020-02-11",
                "time": "15:05:28",
                "name": "meal 3",
                "grams": 800,
                "description": "Meal 3 User 1",
                "calories": 500,
            }
            response = self.post(path, request_data, self._get_headers())
            self._check_succes(expected, response, 201)

    def test_post_meal_wrong_user_admin(self):
        """Wrong user from admin"""
        path = "/".join([self.path, "users", "wronguser", "meals"])
        with self.client:
            request_data = {
                "date": "2020-02-11",
                "time": "15:05:28",
                "name": "meal 3",
                "grams": 800,
                "description": "Meal 3 User 1",
                "calories": 500,
            }
            response = self.post(path, request_data, self._get_headers())
            self._check_error(response, 404, "Not Found", "User 'wronguser' not found")

    def test_post_meal_user_himself(self):
        """User can add meals to himself"""
        path = "/".join([self.path, "users", "user1", "meals"])
        with self.client:
            request_data = {
                "date": "2020-02-11",
                "time": "15:05:28",
                "name": "meal 3",
                "grams": 800,
                "description": "Meal 3 User 1",
                "calories": 500,
            }
            expected = {
                "calories": 500,
                "date": "2020-02-11",
                "description": "Meal 3 User 1",
                "grams": 800,
                "id": 4,
                "name": "meal 3",
                "time": "15:05:28",
                "under_daily_total": False,
            }
            response = self.post(
                path, request_data, self._get_headers("user1", "pass_user1")
            )
            self._check_succes(expected, response, 201)

    def test_post_meal_user_under_daily_total(self):
        """User can add meals to himself under daily total"""
        path = "/".join([self.path, "users", "user1", "meals"])
        with self.client:
            expected = {
                "calories": 500,
                "date": "2020-02-12",
                "description": "Meal 4 User 1",
                "grams": 800,
                "id": 4,
                "name": "meal 4",
                "time": "15:05:28",
                "under_daily_total": True,
            }
            request_data = {
                "date": "2020-02-12",
                "time": "15:05:28",
                "name": "meal 4",
                "grams": 800,
                "description": "Meal 4 User 1",
                "calories": 500,
            }
            response = self.post(
                path, request_data, self._get_headers("user1", "pass_user1")
            )
            self._check_succes(expected, response, 201)

    def test_post_meal_user_others(self):
        """User cannot add meals other users"""
        path = "/".join([self.path, "users", "user2", "meals"])
        with self.client:
            request_data = {
                "date": "2020-02-12",
                "time": "15:05:28",
                "name": "meal 4",
                "grams": 800,
                "description": "Meal 4 User 1",
                "calories": 500,
            }
            response = self.post(
                path, request_data, self._get_headers("user1", "pass_user1")
            )
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'user1' cannot perform the action for other user",
            )

    def test_post_manager_others(self):
        """Managers cannot add meals to other users"""
        path = "/".join([self.path, "users", "user2", "meals"])
        with self.client:
            request_data = {
                "date": "2020-02-12",
                "time": "15:05:28",
                "name": "meal 4",
                "grams": 800,
                "description": "Meal 4 User 1",
                "calories": 500,
            }
            response = self.post(
                path, request_data, self._get_headers("manager1", "pass_manager1")
            )
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action",
            )

    def test_post_meal_manager_himself(self):
        """Managers cannot add meals to themselves"""
        path = "/".join([self.path, "users", "manager1", "meals"])
        with self.client:
            request_data = {
                "date": "2020-02-12",
                "time": "15:05:28",
                "name": "meal 4",
                "grams": 800,
                "description": "Meal 4 User 1",
                "calories": 500,
            }
            response = self.post(
                path, request_data, self._get_headers("manager1", "pass_manager1")
            )
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action",
            )

    def test_delete_meal_unauthenticated(self):
        """Unauthenticated request"""
        path = "/".join([self.path, "users", "user1", "meals", "1"])
        with self.client:
            response = self.delete(path, None)
            self._check_error(
                response, 401, "Unauthorized", "No authorization token provided"
            )

    def test_delete_meal_admin_success(self):
        """Admin can delete a meal"""
        path = "/".join([self.path, "users", "user1", "meals", "1"])
        with self.client:
            expected = None
            response = self.delete(path, self._get_headers())
            self._check_succes(expected, response, 200)

    def test_delete_meal_admin_wrong_user(self):
        """Unauthenticated request"""
        path = "/".join([self.path, "users", "wronguser", "meals", "1"])
        with self.client:
            # Admin mistake on user
            response = self.delete(path, self._get_headers())
            self._check_error(response, 404, "Not Found", "User 'wronguser' not found")

    def test_delete_meal_user_others(self):
        """User cannot delete other users meals"""
        path = "/".join([self.path, "users", "user2", "meals", "3"])
        with self.client:
            # User cannot delete other users meals
            response = self.delete(path, self._get_headers("user1", "pass_user1"))
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'user1' cannot perform the action for other user",
            )

    def test_delete_meal_user_himself(self):
        """User can delete his own meals"""
        path = "/".join([self.path, "users", "user1", "meals", "2"])
        with self.client:
            expected = None
            response = self.delete(path, self._get_headers("user1", "pass_user1"))
            self._check_succes(expected, response, 200)

    def test_delete_meal_no_meal(self):
        """Meal doesnt exist"""
        path = "/".join([self.path, "users", "user1", "meals", "4"])
        with self.client:
            response = self.delete(path, self._get_headers("user1", "pass_user1"))
            self._check_error(response, 404, "Not Found", "Meal '4' not found")

    def test_delete_meal_manager_own(self):
        """User managers cannot delete their meals"""
        path = "/".join([self.path, "users", "manager1", "meals", "1"])
        with self.client:
            response = self.delete(path, self._get_headers("manager1", "pass_manager1"))
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action",
            )

    def test_delete_meal_manager_others(self):
        """User managers cannot delete meals"""
        path = "/".join([self.path, "users", "user2", "meals", "1"])
        with self.client:
            response = self.delete(path, self._get_headers("manager1", "pass_manager1"))
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action",
            )

    def test_get_meal_unauthenticated(self):
        """Unauthenticated request"""
        path = "/".join([self.path, "users", "user1", "meals", "1"])
        with self.client:
            response = self.get(path, None)
            self._check_error(
                response, 401, "Unauthorized", "No authorization token provided"
            )

    def test_get_meal_success_admin(self):
        """Admin can see any meal"""
        path = "/".join([self.path, "users", "user1", "meals", "1"])
        with self.client:
            expected = {
                "calories": 500,
                "date": "2020-02-11",
                "description": "Meal 1 User 1",
                "grams": 100,
                "id": 1,
                "name": "meal 1",
                "time": "15:00:03",
                "under_daily_total": True,
            }
            response = self.get(path, self._get_headers())
            self._check_succes(expected, response, 200)

    def test_get_meal_wrong_user(self):
        """Admin mistake on user"""
        path = "/".join([self.path, "users", "wronguser", "meals", "1"])
        with self.client:
            response = self.get(path, self._get_headers())
            self._check_error(response, 404, "Not Found", "User 'wronguser' not found")

    def test_get_meal_user_others(self):
        """User cannot get other users meals"""
        path = "/".join([self.path, "users", "user2", "meals", "3"])
        with self.client:
            response = self.get(path, self._get_headers("user1", "pass_user1"))
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'user1' cannot perform the action for other user",
            )

    def test_get_meal_user_own(self):
        """User can get his own meals"""
        path = "/".join([self.path, "users", "user1", "meals", "1"])
        with self.client:
            expected = {
                "calories": 500,
                "date": "2020-02-11",
                "description": "Meal 1 User 1",
                "grams": 100,
                "id": 1,
                "name": "meal 1",
                "time": "15:00:03",
                "under_daily_total": True,
            }
            response = self.get(path, self._get_headers("user1", "pass_user1"))
            self._check_succes(expected, response, 200)

    def test_get_meal_user_no_meal(self):
        """Meal doesnt exist"""
        path = "/".join([self.path, "users", "user1", "meals", "4"])
        with self.client:
            response = self.get(path, self._get_headers("user1", "pass_user1"))
            self._check_error(response, 404, "Not Found", "Meal '4' not found")

    def test_get_meal_manager_own(self):
        """Managers cannot get their meals"""
        path = "/".join([self.path, "users", "manager1", "meals", "1"])
        with self.client:
            response = self.get(path, self._get_headers("manager1", "pass_manager1"))
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action",
            )

    def test_get_meal_manager_others(self):
        """Managers cannot get meals belonging to others"""
        path = "/".join([self.path, "users", "manager2", "meals", "1"])
        with self.client:
            response = self.get(path, self._get_headers("manager1", "pass_manager1"))
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action",
            )

    def test_put_meal_unauthenticated(self):
        """Unauthenticated request"""
        path = "/".join([self.path, "users", "user1", "meals", "2"])
        with self.client:
            response = self.get(path, None)
            self._check_error(
                response, 401, "Unauthorized", "No authorization token provided"
            )

    def test_put_meal_success_admin(self):
        """Admin can put any meal"""
        path = "/".join([self.path, "users", "user1", "meals", "2"])
        with self.client:
            expected = {
                "calories": 500,
                "date": "2020-02-11",
                "description": "Meal 1 User 1b",
                "grams": 800,
                "id": 2,
                "name": "meal 1b",
                "time": "15:10:03",
                "under_daily_total": True,
            }
            request_data = {
                "calories": 500,
                "description": "Meal 1 User 1b",
                "grams": 800,
                "name": "meal 1b",
            }
            response = self.put(path, request_data, self._get_headers())
            self._check_succes(expected, response, 200)

    def test_put_meal_admin_wrong_user(self):
        """Admin mistake on user"""
        path = "/".join([self.path, "users", "wronguser", "meals", "2"])
        with self.client:
            request_data = {
                "calories": 500,
                "description": "Meal 1 User 1b",
                "grams": 800,
                "name": "meal 1b",
            }
            response = self.put(path, request_data, self._get_headers())
            self._check_error(response, 404, "Not Found", "User 'wronguser' not found")

    def test_put_meal_user_others(self):
        """User cannot put other users meals"""
        path = "/".join([self.path, "users", "user2", "meals", "3"])
        with self.client:
            request_data = {
                "calories": 500,
                "description": "Meal 1 User 1b",
                "grams": 800,
                "name": "meal 1b",
            }
            response = self.put(
                path, request_data, self._get_headers("user1", "pass_user1")
            )
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'user1' cannot perform the action for other user",
            )

    def test_put_meal_user_own(self):
        """User can put his own meals"""
        path = "/".join([self.path, "users", "user1", "meals", "1"])
        with self.client:
            expected = {
                "calories": 5000,
                "date": "2020-02-13",
                "description": "Meal 1 User 1",
                "grams": 100,
                "id": 1,
                "name": "meal 1",
                "time": "15:00:03",
                "under_daily_total": False,
            }
            request_data = {"calories": 5000, "date": "2020-02-13"}
            response = self.put(
                path, request_data, self._get_headers("user1", "pass_user1")
            )
            self._check_succes(expected, response, 200)

    def test_put_meal_no_meal(self):
        """Meal doesnt exist"""
        path = "/".join([self.path, "users", "user1", "meals", "4"])
        with self.client:
            request_data = {"calories": 5000, "date": "2020-02-13"}
            response = self.put(
                path, request_data, self._get_headers("user1", "pass_user1")
            )
            self._check_error(response, 404, "Not Found", "Meal '4' not found")

    def test_put_meal_manager_own(self):
        """User managers cannot put their meals"""
        path = "/".join([self.path, "users", "manager", "meals", "4"])
        with self.client:
            request_data = {"calories": 5000, "date": "2020-02-13"}
            response = self.put(
                path, request_data, self._get_headers("manager1", "pass_manager1")
            )
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action",
            )

    def test_put_meal_manager_others(self):
        """User managers cannot put meals"""
        path = "/".join([self.path, "users", "user1", "meals", "2"])
        with self.client:
            request_data = {"calories": 5000, "date": "2020-02-13"}
            response = self.put(
                path, request_data, self._get_headers("manager1", "pass_manager1")
            )
            self._check_error(
                response,
                403,
                "Forbidden",
                "User 'manager1' belongs to the role 'MANAGER' and is not allowed to perform the action",
            )


if __name__ == "__main__":
    unittest.main()

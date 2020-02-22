"""
This module contains helper functions to be used on the endpoints
"""

from flask import abort
from sqlalchemy.sql import func

from calories.main import db
from calories.main.models.models import Meal, User


def get_user(username):
    """Get the specified user from the database or abort with a 404 error if he doesn't exist

    :param username:
    :type username: str
    :return: The model User
    :rtype: User
    """
    user = User.query.filter(User.username == username).one_or_none()

    if user is None:
        abort(404, f"User '{username}' not found")

    return user


def get_meal(username, id):
    """Get the specified meal from the database or abort with a 404 error if either the user or the meal don't exist

    :param username: Username that the meal belongs to
    :type username: str
    :param id: Meal id
    :type id: int
    :return: The database object for the meal
    :rtype: Meal
    """
    user = get_user(username)
    meal = Meal.query.join(User, User.id == Meal.user_id).filter(User.username == user.username,
                                                                 Meal.id == id).one_or_none()

    if meal is None:
        abort(404, f"Meal '{id}' not found")

    return meal


def get_daily_calories(user, date):
    """Get the daily calories for a given user on a specified date

    :param user:
    :type user: User
    :param date:
    :type date: datetime.date
    :return: Calories for the user on the date
    :rtype: int
    """
    calories = (db.session.query(func.sum(Meal.calories))
                .join(User, User.id == Meal.user_id).
                filter(User.username == user.username, Meal.date == date)
                .one())
    return 0 if calories[0] is None else calories[0]


def update_meals(user, date, under_daily_total):
    """Update field under_daily_total of a given user on a givend day to the selected value. It does not commit changes to
    the database so everything can be part of the same transaction

    :param user: Username to update its meals
    :type user: User
    :param date: Date of the meals to be updated
    :type date: datetime.date
    :param under_daily_total: New value for under_daily_total
    :type under_daily_total: bool
    :return: Nothing
    """
    for meal in Meal.query.filter(User.username == user.username, Meal.date == date):
        meal.under_daily_total = under_daily_total

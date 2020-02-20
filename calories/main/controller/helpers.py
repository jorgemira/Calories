from flask import abort
from sqlalchemy.sql import func

from calories.main.models.models import Meal, User
from calories.main import db


def get_meal(username, id):
    user = get_user(username)
    meal = Meal.query.join(User, User.id == Meal.user_id).filter(User.username == user.username,
                                                                 Meal.id == id).one_or_none()

    if meal is None:
        abort(404, f"Meal '{id}' not found")

    return meal


def get_user(username):
    user = User.query.filter(User.username == username).one_or_none()

    if user is None:
        abort(404, f"User '{username}' not found")

    return user


def get_daily_calories(user, date):
    calories = (db.session.query(func.sum(Meal.calories))
                .join(User, User.id == Meal.user_id).
                filter(User.username == user.username, Meal.date == date)
                .one())
    return 0 if calories[0] is None else calories[0]


def update_meals(user, date, under_daily_total):
    for meal in Meal.query.filter(User.username == user.username, Meal.date == date):
        meal.under_daily_total = under_daily_total

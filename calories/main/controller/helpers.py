from flask import abort

from calories.main.models.models import Meal, User


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

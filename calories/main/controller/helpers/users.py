"""
This module contains helper functions to be used on the user endpoints
"""
from datetime import datetime

from marshmallow import INCLUDE
from sqlalchemy.sql import func

from calories.main import db
from calories.main.controller import RequestBodyType
from calories.main.controller.helpers import NotFound, Conflict, Forbidden, BadRequest
from calories.main.models.models import Meal, User, UserSchema, Role
from calories.main.util.filters import apply_filter

user_schema = UserSchema(exclude=("id", "_password", "meals"), unknown=INCLUDE)
users_schema = UserSchema(
    many=True, exclude=("id", "_password", "meals"), unknown=INCLUDE
)


def get_users(filter_str: str, items_per_page: int, page_number: int) -> ...:
    """Get the list of users from the database

    :param filter_str: Filter string for the result
    :param items_per_page: Number of items per page
    :param page_number: Page requested
    :return: The list of the users filtered and paginated
    """
    users = User.query.order_by(User.username)
    users, pagination = apply_filter(users, filter_str, items_per_page, page_number)

    return users_schema.dump(users), pagination


def get_user(username: str) -> User:
    """Get the information of a user"""
    return user_schema.dump(_get_user(username))


def crt_user(req_user: str, username: str, data: RequestBodyType) -> User:
    """Create a user on the database

    :param req_user: Username of the user that requests the action
    :param username: Username of the user to update
    :param data: Data of the user
    :return: The already updated user
    :raises Forbidden: If the user does not have permissions to do the action
    :raises BadRequest: If the username has not alphanumeric characters
    """
    try:
        _get_user(username)
        raise Conflict(f"User '{username}' exists already")
    except NotFound:
        pass

    owner = _get_user(req_user)
    new_user = user_schema.load(data, session=db.session)

    if owner.role == Role.MANAGER and new_user.role != Role.USER:
        raise Forbidden(f"User '{req_user}' can only create users with role USER")

    if not data["username"].isalnum():
        raise BadRequest(f"Username must contain only alphanumeric characters")

    db.session.add(new_user)
    db.session.commit()

    return user_schema.dump(new_user)


def updt_user(req_user: str, username: str, data: RequestBodyType) -> User:
    """Update the information of a user

    :param req_user: Username of the user that requests the action
    :param username: Username of the user to update
    :param data: New data for the user
    :return: The already updated user
    :raises Forbidden: If the user does not have permissions to do the action
    :raises BadRequest: If the username has not alphanumeric characters
    """
    u_user = _get_user(username)
    owner = _get_user(req_user)

    updated = user_schema.load(data, session=db.session)

    if updated.role and updated.role != u_user.role and owner.role != Role.ADMIN:
        raise Forbidden(f"User '{req_user}' is not allowed to change Role")

    if not data.get("username", "a").isalnum():
        raise BadRequest(f"Username must contain only alphanumeric characters")

    updated.id = u_user.id

    db.session.merge(updated)
    db.session.commit()

    return user_schema.dump(u_user)


def dlt_user(req_user: str, username: str) -> None:
    """ Delete an user from the database

    :param req_user: Username of the user that requests the action
    :param username: Username of the user to delete
    :raises Forbiden: If the user is not allowed to perform the action
    """
    d_user = _get_user(username)
    owner = _get_user(req_user)

    if owner.role == Role.MANAGER and d_user.role != Role.USER:
        raise Forbidden(f"User '{req_user}' can only delete users with role USER")

    db.session.delete(d_user)
    db.session.commit()


def _get_user(username: str) -> User:
    """Get the specified user from the database

    :raises NotFound: If the user is not on the database
    """
    user = User.query.filter(User.username == username).one_or_none()

    if user is None:
        raise NotFound(f"User '{username}' not found")

    return user


def get_daily_calories(user: User, date: datetime.date) -> int:
    """Get the daily calories for a given user on a specified date"""
    calories = (
        db.session.query(func.sum(Meal.calories))
            .join(User, User.id == Meal.user_id)
            .filter(User.username == user.username, Meal.date == date)
            .one()
    )
    return 0 if calories[0] is None else calories[0]

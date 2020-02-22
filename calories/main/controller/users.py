"""
This is the users module and supports all the REST actions for the Users data
"""

from flask import abort
from marshmallow import INCLUDE

from calories.main import db, logger
from calories.main.controller.auth import is_allowed
from calories.main.controller.helpers import get_user
from calories.main.models.models import User, UserSchema, Role
from calories.main.util.filters import apply_filter


@is_allowed(roles_allowed=[Role.MANAGER])
def read_users(user, filter='', itemsPerPage=None, pageNumber=None):
    """Read the full list of users

    :param user: The user that requests the action
    :type user: str
    :param filter: Filter string for the results
    :type filter: str
    :param itemsPerPage: Number of items of every page, defaults to 10
    :type itemsPerPage: int
    :param pageNumber: Page number of the results defaults to 1
    :type pageNumber: int
    :return: Success mesage with the list of users
    """
    users = User.query.order_by(User.username)
    users, pagination = apply_filter(users, filter, itemsPerPage, pageNumber)

    user_schema = UserSchema(many=True, exclude=('id', '_password', 'meals'))
    data = user_schema.dump(users)

    logger.info(f"User: '{user}', read user list, filter: '{filter}', itemsPerPage: '{itemsPerPage}'"
                f"pageNumber: '{pageNumber}'")

    return {'status': 200,
            'title': 'Success',
            'detail': f"List of users succesfully read",
            'data': data,
            'numPages': pagination.num_pages,
            'totalResults': pagination.total_results
            }, 200


@is_allowed(roles_allowed=[Role.MANAGER], allow_self=True)
def read_user(user, username):
    """Read a user

    :param user: User that requests the action
    :type user: str
    :param username: User to be read
    :type username: str
    :return: Success message or 404 if user not found
    """
    c_user = get_user(username)
    user_schema = UserSchema(exclude=('id', '_password', 'meals'))
    data = user_schema.dump(c_user)

    logger.info(f"User: '{user}' read user: '{username}'")

    return {'status': 200,
            'title': 'Success',
            'detail': f"User: '{username}' succesfully read",
            'data': data
            }, 200


@is_allowed(roles_allowed=[Role.MANAGER])
def create_user(user, body):
    """Create a user

    :param user: User that request the action
    :type user: str
    :param body: Information of the new user
    :type body: dict
    :return: Succes message, 409 if user already exists, 401 if role is wrong, 400 if wrong username
    """
    username = body.get("username")
    existing_user = User.query.filter(User.username == username).one_or_none()
    owner = get_user(user)

    if existing_user:
        logger.warning(f"User: '{user}' with tried to create already existing user: '{username}'")
        abort(409, f"User '{username}' exists already")

    schema = UserSchema(exclude=('id', '_password', 'meals'), unknown=INCLUDE)
    new_user = schema.load(body, session=db.session)

    if owner.role == Role.MANAGER and new_user.role != Role.USER:
        logger.warning(f"User: '{user}' with role '{owner.role}' tried to create user: '{username}' with role "
                       f"'{new_user.role}'")
        abort(401, f"User '{user}' can only create users with role USER")

    if not body['username'].isalnum():
        logger.warning(f"User: '{user}' with role '{owner.role}' tried to update user: '{username}' with username "
                       f"'{new_user.username}'")
        abort(400, f"Username must contain only alphanumeric characters")

    db.session.add(new_user)
    db.session.commit()

    data = schema.dump(new_user)

    logger.info(f"User: '{user}' created user: '{username}'")

    return {'status': 201,
            'title': 'Success',
            'detail': f"User: '{username}' succesfully created",
            'data': data
            }, 201


@is_allowed(roles_allowed=[Role.MANAGER], allow_self=True)
def update_user(user, username, body):
    """Update user

    :param user: User that performs the action
    :type user: str
    :param username: User to be updated
    :type username: str
    :param body: Information of the new user to be created
    :type body: dict
    :return: Success message or 401 if there are role issues or 400 if the username is wrong
    """
    u_user = get_user(username)
    owner = get_user(user)

    schema = UserSchema(exclude=('id', '_password', 'meals'), unknown=INCLUDE)
    updated = schema.load(body, session=db.session)

    if updated.role and updated.role != u_user.role and owner.role != Role.ADMIN:
        logger.warning(f"User: '{user}' with role '{owner.role}' tried to update user: '{username}' with role "
                       f"'{u_user.role}'")
        abort(401, f"User '{user}' is not allowed to change Role")

    if not body.get('username', 'a').isalnum():
        logger.warning(f"User: '{user}' with role '{owner.role}' tried to update user: '{username}' with username "
                       f"'{u_user.username}'")
        abort(400, f"Username must contain only alphanumeric characters")

    updated.id = u_user.id

    db.session.merge(updated)
    db.session.commit()

    data = schema.dump(u_user)

    logger.info(f"User: '{user}' updated user: '{username}'")

    return {'status': 200,
            'title': 'Success',
            'detail': f"User: '{username}' succesfully updated",
            'data': data
            }, 200


@is_allowed(roles_allowed=[Role.MANAGER], allow_self=True)
def delete_user(user, username):
    """Deletes given user

    :param user: User that performs the action
    :type user: str
    :param username: User to be deleted
    :type user: str
    :return: Success message or 404 if user not found
    """
    d_user = get_user(username)
    owner = get_user(user)

    if owner.role == Role.MANAGER and d_user.role != Role.USER:
        logger.warning(f"User: '{user}' with role '{owner.role}' failed to delete user: '{username}' with role "
                       f"'{d_user.username}'")
        abort(401, f"User '{user}' can only delete users with role USER")

    db.session.delete(d_user)
    db.session.commit()

    logger.info(f"User: '{user}' deleted user: '{username}'")

    return {'status': 200,
            'title': 'Success',
            'detail': f"User: '{username}' succesfully deleted",
            'data': None
            }, 200

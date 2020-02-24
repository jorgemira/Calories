"""
This is the users module and supports all the REST actions for the Users data
"""

from flask import abort

from calories.main import logger
from calories.main.controller.helpers import RequestError
from calories.main.controller.helpers.auth import is_allowed
from calories.main.controller.helpers.users import get_users, get_user, crt_user, updt_user, dlt_user
from calories.main.models.models import Role


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
    try:
        data, pagination = get_users(filter, itemsPerPage, pageNumber)
    except RequestError as e:
        data = pagination = None
        logger.warn(e.message)
        abort(e.code, e.message)

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
    try:
        data = get_user(username)
    except RequestError as e:
        data = None
        logger.warn(e.message)
        abort(e.code, e.message)

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
    :return: Succes message, 409 if user already exists, 403 if role is wrong, 400 if wrong username
    """
    username = body.get("username")
    try:
        data = crt_user(user, username, body)
    except RequestError as e:
        data = None
        logger.warn(e.message)
        abort(e.code, e.message)

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
    :return: Success message or 403 if there are role issues or 400 if the username is wrong
    """
    try:
        data = updt_user(user, username, body)
    except RequestError as e:
        data = None
        logger.warn(e.message)
        abort(e.code, e.message)

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
    try:
        dlt_user(user, username)
    except RequestError as e:
        logger.warn(e.message)
        abort(e.code, e.message)

    logger.info(f"User: '{user}' deleted user: '{username}'")

    return {'status': 200,
            'title': 'Success',
            'detail': f"User: '{username}' succesfully deleted",
            'data': None
            }, 200

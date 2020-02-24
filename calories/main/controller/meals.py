"""
This is the meals module and supports all the REST actions for the Meals data
"""

from flask import abort

from calories.main import logger
from calories.main.controller.helpers import RequestError
from calories.main.controller.helpers.auth import is_allowed
from calories.main.controller.helpers.meals import get_meals, get_meal, crt_meal, updt_meal, dlt_meals
from calories.main.models.models import Role


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def read_meals(user, username, filter=None, itemsPerPage=10, pageNumber=1):
    """Read the list of meals for a given user

    :param user: The user that requests the action
    :type user: str
    :param username: User to return al his meals
    :type username: str
    :param filter: Filter string for the results
    :type filter: str
    :param itemsPerPage: Number of items of every page, defaults to 10
    :type itemsPerPage: int
    :param pageNumber: Page number of the results defaults to 1
    :type pageNumber: int
    :return:
    """
    try:
        data, pagination = get_meals(username, filter, itemsPerPage, pageNumber)
    except RequestError as e:
        data = pagination = None
        logger.warn(e.message)
        abort(e.code, e.message)

    logger.info(f"User: '{user}', read meals for user: '{username}', filter: '{filter}', itemsPerPage: '{itemsPerPage}'"
                f"pageNumber: '{pageNumber}'")

    return {'status': 200,
            'title': 'Success',
            'detail': f"List of meals succesfully read for user: '{username}'",
            'data': data,
            'num_pages': pagination.num_pages,
            'total_result': pagination.total_results
            }, 200


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def read_meal(user, username, id):
    """Read a meal that belongs to a user

    :param user: The user that requests the action
    :type user: str
    :param username: Username to read his meal
    :type username: str
    :param id: Id of the meal
    :type id: int
    :return:
    """
    try:
        data = get_meal(username, id)
    except RequestError as e:
        data = None
        logger.warn(e.message)
        abort(e.code, e.message)

    logger.info(f"User: '{user}' read meal: '{id}' of  user: '{username}'")

    return {'status': 200,
            'title': 'Success',
            'detail': f"Meal: '{id}' of  user: '{username}' succesfully read",
            'data': data
            }, 200


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def create_meal(user, username, body):
    """Create a meal

    :param user: User that requests the action
    :type user: str
    :param username: User whose meal is going to be created
    :type username: str
    :param body: Information about the new meal
    :type body: dict
    :return: A success message if the meal was found or a 400 error if any parameter was wrong
    """
    try:
        data = crt_meal(username, body)
    except RequestError as e:
        data = None
        logger.warn(e.message)
        abort(e.code, e.message)

    logger.info(f"User: '{user}' created meal: '{data.get('id')}' for  user: '{username}'")

    return {'status': 201,
            'title': 'Success',
            'detail': f"Meal: '{data.get('id')}' of  user: '{username}' succesfully created",
            'data': data
            }, 201


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def update_meal(user, username, id, body):
    """Update a meal

    :param user: User that requests the action
    :type user: str
    :param username: User whose meal is going to be updated
    :type username: str
    :param id: Meal id to update
    :type id: int
    :param body: New body of the updated meal
    :type body: str
    :return: A success message if the meal was found or a 404 error if either the user or the meal does not exist
    """
    try:
        data = updt_meal(username, id, body)
    except RequestError as e:
        data = None
        logger.warn(e.message)
        abort(e.code, e.message)

    logger.info(f"User: '{user}' updated meal: '{id}' for  user: '{username}'")

    return {'status': 200,
            'title': 'Success',
            'detail': f"Meal: '{id}' of  user: '{username}' succesfully updated",
            'data': data
            }, 200


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def delete_meal(user, username, id):
    """Delete a meal

    :param user: User that requests the action
    :type user: str
    :param username: User whose meal is going to be deleted
    :type username: str
    :param id: Meal id to delete
    :type id: int
    :return: A success message if the meal was found or a 404 error if either the user or the meal does not exist
    """
    try:
        dlt_meals(username, id)
    except RequestError as e:
        logger.warn(e.message)
        abort(e.code, e.message)

    logger.info(f"User: '{user}' deleted meal: '{id}' for  user: '{username}'")

    return {'status': 200,
            'title': 'Success',
            'detail': f"Meal: '{id}' of  user: '{username}' succesfully deleted",
            'data': None
            }, 200

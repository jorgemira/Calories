"""
This is the meals module and supports all the REST actions for the Meals data
"""

from flask import abort

from calories.main import logger
from calories.main.controller import ResponseType, RequestBodyType
from calories.main.controller.helpers import RequestError
from calories.main.controller.helpers.auth import is_allowed
from calories.main.controller.helpers.meals import (
    get_meals,
    get_meal,
    crt_meal,
    updt_meal,
    dlt_meals,
)
from calories.main.models.models import Role


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def read_meals(
        user: str,
        username: str,
        filter_results: str = None,
        items_per_page: int = 10,
        page_number: int = 1,
) -> ResponseType:
    """Read the list of meals for a given user

    :param user: The user that requests the action
    :param username: User to return al his meals
    :param filter_results: Filter string for the results
    :param items_per_page: Number of items of every page, defaults to 10
    :param page_number: Page number of the results defaults to 1
    """

    try:
        data, pagination = get_meals(
            username, filter_results, items_per_page, page_number
        )
    except RequestError as e:
        data = pagination = None
        logger.warning(e.message)
        abort(e.code, e.message)

    logger.info(
        f"User: '{user}', read meals for user: '{username}',"
        f" filter: '{filter_results}', itemsPerPage: '{items_per_page}',"
        f" pageNumber: '{page_number}'"
    )

    return (
        {
            "status": 200,
            "title": "Success",
            "detail": f"List of meals succesfully read for user: '{username}'",
            "data": data,
            "num_pages": pagination.num_pages,
            "total_result": pagination.total_results,
        },
        200,
    )


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def read_meal(user: str, username: str, meal_id: int) -> ResponseType:
    """Read a meal that belongs to a user

    :param user: The user that requests the action
    :param username: Username to read his meal
    :param meal_id: Id of the meal
    """
    try:
        data = get_meal(username, meal_id)
    except RequestError as e:
        data = None
        logger.warning(e.message)
        abort(e.code, e.message)

    logger.info(f"User: '{user}' read meal: '{meal_id}' of  user: '{username}'")

    return (
        {
            "status": 200,
            "title": "Success",
            "detail": f"Meal: '{meal_id}' of  user: '{username}' succesfully read",
            "data": data,
        },
        200,
    )


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def create_meal(user: str, username: str, body: RequestBodyType) -> ResponseType:
    """Create a meal

    :param user: User that requests the action
    :param username: User whose meal is going to be created
    :param body: Information about the new meal
    :return: A success message if the meal was found or a 400 error
    if any parameter was wrong
    """
    try:
        data = crt_meal(username, body)
    except RequestError as e:
        data = None
        logger.warning(e.message)
        abort(e.code, e.message)

    logger.info(
        f"User: '{user}' created meal: '{data.get('id')}' for  user: '{username}'"
    )

    return (
        {
            "status": 201,
            "title": "Success",
            "detail": f"Meal: '{data.get('id')}' of  user: '{username}' "
                      f"succesfully created",
            "data": data,
        },
        201,
    )


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def update_meal(
        user: str, username: str, meal_id: int, body: RequestBodyType
) -> ResponseType:
    """Update a meal

    :param user: User that requests the action
    :param username: User whose meal is going to be updated
    :param meal_id: Meal id to update
    :param body: New body of the updated meal
    :return: A success message if the meal was found or a 404 error if either the user or the meal does not exist
    """
    try:
        data = updt_meal(username, meal_id, body)
    except RequestError as e:
        data = None
        logger.warning(e.message)
        abort(e.code, e.message)

    logger.info(f"User: '{user}' updated meal: '{meal_id}' for  user: '{username}'")

    return (
        {
            "status": 200,
            "title": "Success",
            "detail": f"Meal: '{meal_id}' of  user: '{username}' succesfully updated",
            "data": data,
        },
        200,
    )


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def delete_meal(user: str, username: str, meal_id: int) -> ResponseType:
    """Delete a meal

    :param user: User that requests the action
    :param username: User whose meal is going to be deleted
    :param meal_id: Meal id to delete
    :return: A success message if the meal was found or a 404 error if either the user
     or the meal does not exist
    """
    try:
        dlt_meals(username, meal_id)
    except RequestError as e:
        logger.warning(e.message)
        abort(e.code, e.message)

    logger.info(f"User: '{user}' deleted meal: '{meal_id}' for  user: '{username}'")

    return (
        {
            "status": 200,
            "title": "Success",
            "detail": f"Meal: '{meal_id}' of  user: '{username}' succesfully deleted",
            "data": None,
        },
        200,
    )

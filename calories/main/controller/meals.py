"""
This is the meals module and supports all the REST actions for the Meals data
"""

from flask import abort
from marshmallow import ValidationError

from calories.main import db, logger
from calories.main.controller.auth import is_allowed
from calories.main.controller.helpers import get_meal, get_daily_calories, update_meals, get_user
from calories.main.models.models import Meal, MealSchema, User, Role
from calories.main.util.external_apis import calories_from_nutritionix
from calories.main.util.filters import apply_filter


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
    r_user = get_user(username)

    meals = Meal.query.join(User, User.id == Meal.user_id).filter(User.username == r_user.username)
    meal_schema = MealSchema(many=True, exclude=['user'])
    meals, pagination = apply_filter(meals, filter, itemsPerPage, pageNumber)
    data = meal_schema.dump(meals)

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
    meal = get_meal(username, id)

    meal_schema = MealSchema(exclude=['user'])
    data = meal_schema.dump(meal)

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
    c_user = get_user(username)

    schema = MealSchema(exclude=['user'])
    try:
        new_meal = schema.load(body, session=db.session)
    except ValidationError as e:
        fields = ", ".join(f"'{f}'" for f in sorted(e.messages))
        logger.warning(f"User: '{user}' failed to create meal: '{body}' for  user: '{username}' because the following "
                       f"wrong fields: {fields}")
        new_meal = None
        abort(400, f'Field(s): {fields} have the wrong format')

    if not new_meal.calories:
        new_meal.calories = calories_from_nutritionix(new_meal.name)

    calories = get_daily_calories(c_user, new_meal.date)

    c_user.meals.append(new_meal)

    if c_user.daily_calories <= calories + new_meal.calories:
        new_meal.under_daily_total = False
        if calories < c_user.daily_calories:
            update_meals(c_user, new_meal.date, False)
    else:
        new_meal.under_daily_total = True

    db.session.commit()

    data = schema.dump(new_meal)

    logger.info(f"User: '{user}' created meal: '{new_meal.id}' for  user: '{username}'")

    return {'status': 201,
            'title': 'Success',
            'detail': f"Meal: '{new_meal.id}' of  user: '{username}' succesfully created",
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
    old_meal = get_meal(username, id)
    u_user = get_user(username)

    schema = MealSchema(exclude=['user'])
    try:
        new_meal = schema.load(body, session=db.session)
    except ValidationError as e:
        fields = ", ".join(f"'{f}'" for f in sorted(e.messages))
        new_meal = None
        logger.warning(f"User: '{user}' failed to create meal: '{body}' for  user: '{username}' because the following "
                       f"wrong fields: {fields}")
        abort(400, f'Field(s): {fields} have the wrong format')

    new_meal.user_id = old_meal.user_id
    new_meal.id = old_meal.id

    # Get calories from nutrtionix if the meal has changed but the user didn't provide its calories
    if new_meal.name and new_meal.name != old_meal.name and not new_meal.calories:
        new_meal.calories = calories_from_nutritionix(new_meal.name)

    if new_meal.date:  # Meal has changed date so we need to update under_daily_total for both dates
        # Update under_daily_limit for old date
        calories = get_daily_calories(u_user, old_meal.date)
        if calories >= u_user.daily_calories > calories - old_meal.calories:
            update_meals(u_user, old_meal.date, True)

        # Update under_daily_limit for new date
        new_calories = new_meal.calories or old_meal.calories
        calories_new_date = get_daily_calories(u_user, new_meal.date)
        if u_user.daily_calories <= calories_new_date + new_calories:  # New date is over daily limit
            new_meal.under_daily_total = False
            if calories < u_user.daily_calories:  # New date was under daily limit before
                update_meals(u_user, new_meal.date, False)
        else:  # New date will be still under daily limit
            new_meal.under_daily_total = True
    elif new_meal.calories and new_meal.calories != old_meal.calories:  # Calories have changed but its the same date
        difference = new_meal.calories - old_meal.calories
        calories = get_daily_calories(u_user, old_meal.date)
        # Change in calories made a difference
        if (u_user.daily_calories > calories) != (u_user.daily_calories > calories + difference):
            update_meals(u_user, new_meal.date, u_user.daily_calories > calories + difference)
            new_meal.under_daily_total = u_user.daily_calories > calories + difference

    db.session.merge(new_meal)
    db.session.commit()
    data = schema.dump(old_meal)

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
    d_user = get_user(username)
    meal = get_meal(username, id)

    # Update under_daily_total for the day if necessary
    calories = get_daily_calories(d_user, meal.date)
    if calories >= d_user.daily_calories > calories - meal.calories:
        update_meals(d_user, meal.date, True)

    db.session.delete(meal)
    db.session.commit()

    logger.info(f"User: '{user}' deleted meal: '{id}' for  user: '{username}'")

    return {'status': 200,
            'title': 'Success',
            'detail': f"Meal: '{id}' of  user: '{username}' succesfully deleted",
            'data': None
            }, 200

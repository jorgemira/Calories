"""
This is the people module and supports all the REST actions for the meals data
"""

from flask import make_response, abort, jsonify
from marshmallow import ValidationError

from calories.main import db
from calories.main.controller.auth import is_allowed
from calories.main.controller.helpers import get_meal, get_daily_calories, update_meals, get_user
from calories.main.models.models import Meal, MealSchema, User, Role
from calories.main.util.external_apis import calories_from_nutritionix
from calories.main.util.filters import apply_filter


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def read_meals(user, username, filter=None, itemsPerPage=None, pageNumber=None):
    """
    This function responds to a request for /api/users/{user_id}/meals
    with one matching user from users
    :param username:   Id of user to find
    :return:            user matching id
    """
    user = get_user(username)

    meals = Meal.query.join(User, User.id == Meal.user_id).filter(User.username == user.username)
    meal_schema = MealSchema(many=True)
    data = meal_schema.dump(apply_filter(meals, filter, itemsPerPage, pageNumber))
    return data, 200


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def read_one(user, username, id):
    """
    This function responds to a request for
    /api/people/{user_id}/meals/{user_id}
    with one matching meal for the associated user
    :param username:       Id of user the meal is related to
    :param id:         Id of the meal
    :return:                json string of meal contents
    """
    meal = get_meal(username, id)

    meal_schema = MealSchema()
    data = meal_schema.dump(meal)
    return data, 200


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def create(user, username, body):
    """
    This function creates a new meal related to the passed in user id.
    :param username:       Id of the user the meal is related to
    :param body:            The JSON containing the meal data
    :return:                201 on success
    """

    user = get_user(username)

    # Create a meal schema instance
    schema = MealSchema()
    try:
        new_meal = schema.load(body, session=db.session)
    except ValidationError as e:
        fields = ", ".join(f"'{f}'" for f in e.messages)
        abort(400, f'Field(s): {fields} have the wrong format')

    if not new_meal.calories:
        new_meal.calories = calories_from_nutritionix(new_meal.name)

    calories = get_daily_calories(user, new_meal.date)

    # Add the meal to the user and database
    user.meals.append(new_meal)

    if calories < user.daily_calories <= calories + new_meal.calories:
        new_meal.under_daily_total = False
        update_meals(user, new_meal.date, False)

    db.session.commit()

    # Serialize and return the newly created meal in the response
    data = schema.dump(new_meal)

    return data, 201


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def update(user, username, id, body):
    """
    This function updates an existing meal related to the passed in
    user id.
    :param username:       Id of the user the meal is related to
    :param id:         Id of the meal to update
    :param body:            The JSON containing the meal data
    :return:                200 on success
    """
    old_meal = get_meal(username, id)

    # turn the passed in meal into a db object
    schema = MealSchema(exclude=['user'])
    try:
        new_meal = schema.load(body, session=db.session)
    except ValidationError as e:
        fields = ", ".join(f"'{f}'" for f in e.messages)
        abort(400, f'Field(s): {fields} have the wrong format')

    new_meal.user_id = old_meal.user_id
    new_meal.id = old_meal.id

    if new_meal.name and new_meal.name != old_meal.name and not new_meal.calories:
        new_meal.calories = calories_from_nutritionix(new_meal.name)

    if new_meal.calories != old_meal.calories:
        difference = new_meal.calories - old_meal.calories
        calories = get_daily_calories(user, new_meal.date)
        if user.daily_calories > calories != user.daily_calories > calories + difference:
            update_meals(user, new_meal.date, user.daily_calories > calories + difference)
            new_meal.under_daily_total = user.daily_calories > calories + difference

    # merge the new object into the old and commit it to the db
    db.session.merge(new_meal)

    db.session.commit()

    # return updated meal in the response
    data = schema.dump(old_meal)

    return data, 200


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def delete(user, username, id):
    """
    This function deletes a meal from the meal structure
    :param username:   Id of the user the meal is related to
    :param id:     Id of the meal to delete
    :return:            200 on successful delete, 404 if not found
    """
    user = get_user(username)
    meal = get_meal(username, id)
    calories = get_daily_calories(user, meal.date)

    if calories >= user.daily_calories > calories - meal.calories:
        update_meals(user, meal.date, True)

    db.session.delete(meal)
    db.session.commit()
    return make_response(jsonify({'message': f"Meal '{id}' deleted", 'success': True}), 200)


"""
This is the people module and supports all the REST actions for the
people data
"""

from flask import make_response, abort, jsonify

from calories.main import db
from calories.main.controller.auth import is_allowed
from calories.main.controller.helpers import get_meal
from calories.main.models.models import Meal, MealSchema, User, Role
from calories.main.util.external_apis import calories_from_nutritionix
from calories.main.util.filters import apply_filter


@is_allowed(roles_allowed=[Role.USER])
def read_meals(user, username, filter=None, itemsPerPage=None, pageNumber=None):
    """
    This function responds to a request for /api/users/{user_id}/meals
    with one matching user from users
    :param username:   Id of user to find
    :return:            user matching id
    """
    user = User.query.filter(User.username == username).one_or_none()
    if user is None:
        abort(404, f"User '{username}' not found")

    meals = Meal.query.join(User, User.id == Meal.user_id).filter(User.username == username)
    meal_schema = MealSchema(many=True)
    data = meal_schema.dump(apply_filter(meals, filter, itemsPerPage, pageNumber))
    return data, 200


@is_allowed(roles_allowed=[Role.USER])
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


@is_allowed(roles_allowed=[Role.USER])
def create(user, username, body):
    """
    This function creates a new meal related to the passed in user id.
    :param username:       Id of the user the meal is related to
    :param body:            The JSON containing the meal data
    :return:                201 on success
    """

    user = User.query.filter(User.username == username).one_or_none()
    if user is None:
        abort(404, f"User '{username}' not found")

    # Create a meal schema instance
    schema = MealSchema()
    new_meal = schema.load(body, session=db.session)

    if not new_meal.calories:
        new_meal.calories = calories_from_nutritionix(new_meal.name)

    # Add the meal to the user and database
    user.meals.append(new_meal)
    update_meals(username, new_meal.date)

    db.session.commit()

    # Serialize and return the newly created meal in the response
    data = schema.dump(new_meal)

    return data, 201


@is_allowed(roles_allowed=[Role.USER])
def update(user, username, id, body):
    """
    This function updates an existing meal related to the passed in
    user id.
    :param username:       Id of the user the meal is related to
    :param id:         Id of the meal to update
    :param body:            The JSON containing the meal data
    :return:                200 on success
    """
    meal = get_meal(username, id)

    # turn the passed in meal into a db object
    schema = MealSchema(exclude=['user'])
    tmp = schema.load(body, session=db.session)

    tmp.user_id = meal.user_id
    tmp.id = meal.id

    if not tmp.calories:
        tmp.calories = calories_from_nutritionix(tmp.name)

    # merge the new object into the old and commit it to the db
    db.session.merge(tmp)
    update_meals(username, tmp.date)

    db.session.commit()

    # return updated meal in the response
    data = schema.dump(meal)

    return data, 200


@is_allowed(roles_allowed=[Role.USER])
def delete(user, username, id):
    """
    This function deletes a meal from the meal structure
    :param username:   Id of the user the meal is related to
    :param id:     Id of the meal to delete
    :return:            200 on successful delete, 404 if not found
    """
    meal = get_meal(username, id)
    db.session.delete(meal)
    update_meals(username, meal.date)
    db.session.commit()
    return make_response(jsonify({'message': f"Meal '{id}' deleted", 'success': True}), 200)


def update_meals(username, date):
    # FIXME: not working
    pass
    # meals = Meal.query.join(User, User.id == Meal.user_id).filter(User.username == username, Meal.date == date)

    # if user is None:
    #     abort(404, f"Person not found for Id: {username}")
    # calories = db.session.query(func.sum(Meal.calories)).filter(User.username == username, Meal.date == date).first()[0]
    # Meal.query.filter(User.username == user.name, Meal.date == date).update(
    #     {Meal.under_daily_total: calories >= user.daily_calories}, synchronize_session='fetch')


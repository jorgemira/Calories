"""
This is the people module and supports all the REST actions for the
people data
"""

from flask import make_response, abort
from sqlalchemy.sql import func

from auth import is_allowed
from config import db
from external_apis import calories_from_nutritionix
from filters import apply_filter
from models import User, Meal, MealSchema, Role


@is_allowed(roles_allowed=[Role.USER])
def read_all(user, filter=None, itemsPerPage=None, pageNumber=None):
    """
    This function responds to a request for /api/people/meals
    with the complete list of meals, sorted by meal timestamp
    :return:                json list of all meals for all people
    """
    # Query the database for all the meals
    meals = Meal.query.all()

    meals = apply_filter(meals, filter, itemsPerPage, pageNumber)

    # Serialize the list of meals from our data
    meal_schema = MealSchema(many=True, exclude=['user.id', 'user.password'])
    data = meal_schema.dump(meals)
    return data


@is_allowed(roles_allowed=[Role.USER])
def read_meals(user, username, filter=None, itemsPerPage=None, pageNumber=None):
    """
    This function responds to a request for /api/users/{user_id}/meals
    with one matching user from users
    :param username:   Id of user to find
    :return:            user matching id
    """
    user = User.query.filter(User.username == username).outerjoin(Meal).one_or_none()

    if user is not None:
        # Serialize the data for the response
        meal_schema = MealSchema(many=True, exclude=['user'])
        # TODO: this probably wont work
        data = meal_schema.dump(apply_filter(user.meals, filter, itemsPerPage, pageNumber))
        return data
    else:
        abort(404, f"User '{username}' not found")


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
    meal = (
        Meal.query.join(User, User.id == Meal.user_id).filter(User.username == username, Meal.id == id).one_or_none())

    if meal is not None:
        meal_schema = MealSchema(exclude=['user'])
        data = meal_schema.dump(meal)
        return data
    else:
        abort(404, f"Meal not found for Id: {id}")


@is_allowed(roles_allowed=[Role.USER])
def create(user, username, body):
    """
    This function creates a new meal related to the passed in user id.
    :param username:       Id of the user the meal is related to
    :param body:            The JSON containing the meal data
    :return:                201 on success
    """
    # get the parent user
    user = User.query.filter(User.username == username).one_or_none()

    # Was a user found?
    if user is None:
        abort(404, f"Person not found for Id: {username}")

    # Create a meal schema instance
    schema = MealSchema(exclude=['user'])
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
    update_meal = Meal.query.filter(User.username == username, Meal.id == id).one_or_none()

    # Did we find an existing meal?
    if update_meal is not None:

        # turn the passed in meal into a db object
        schema = MealSchema(exclude=['user'])
        tmp = schema.load(body, session=db.session)

        # Set the id's to the meal we want to update
        tmp.user_id = update_meal.user_id
        tmp.id = update_meal.id

        if not tmp.calories:
            tmp.calories = calories_from_nutritionix(tmp.name)

        # merge the new object into the old and commit it to the db
        db.session.merge(tmp)
        update_meals(username, tmp.date)

        db.session.commit()

        # return updated meal in the response
        data = schema.dump(update_meal)

        return data, 200

    # Otherwise, nope, didn't find that meal
    else:
        abort(404, f"Meal not found for Id: {id}")


@is_allowed(roles_allowed=[Role.USER])
def delete(user, username, id):
    """
    This function deletes a meal from the meal structure
    :param username:   Id of the user the meal is related to
    :param id:     Id of the meal to delete
    :return:            200 on successful delete, 404 if not found
    """
    # Get the meal requested
    meal = Meal.query.filter(User.username == username, Meal.id == id).one_or_none()

    # did we find a meal?
    if meal is not None:
        db.session.delete(meal)
        update_meals(username, meal.date)

        db.session.commit()

        return make_response(f"Meal {id} deleted", 200)

    # Otherwise, nope, didn't find that meal
    else:
        abort(404, f"Meal not found for Id: {id}")


def update_meals(username, date):
    user = User.query.filter(User.username == username).one_or_none()
    if user is None:
        abort(404, f"Person not found for Id: {username}")
    calories = db.session.query(func.sum(Meal.calories)).filter(User.username == username, Meal.date == date).first()[0]
    Meal.query.filter(User.username == user.name, Meal.date == date).update(
        {Meal.under_daily_total: calories >= user.daily_calories}, synchronize_session='fetch')

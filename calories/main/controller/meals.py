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
    user = get_user(username)

    meals = Meal.query.join(User, User.id == Meal.user_id).filter(User.username == user.username)
    meal_schema = MealSchema(many=True, exclude=['user'])
    data = meal_schema.dump(apply_filter(meals, filter, itemsPerPage, pageNumber))
    return data, 200


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def read_one(user, username, id):
    meal = get_meal(username, id)

    meal_schema = MealSchema(exclude=['user'])
    data = meal_schema.dump(meal)
    return data, 200


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def create(user, username, body):
    user = get_user(username)

    schema = MealSchema(exclude=['user'])
    try:
        new_meal = schema.load(body, session=db.session)
    except ValidationError as e:
        fields = ", ".join(f"'{f}'" for f in sorted(e.messages))
        abort(400, f'Field(s): {fields} have the wrong format')

    if not new_meal.calories:
        new_meal.calories = calories_from_nutritionix(new_meal.name)

    calories = get_daily_calories(user, new_meal.date)

    user.meals.append(new_meal)

    if user.daily_calories <= calories + new_meal.calories:
        new_meal.under_daily_total = False
        if calories < user.daily_calories:
            update_meals(user, new_meal.date, False)
    else:
        new_meal.under_daily_total = True

    db.session.commit()

    data = schema.dump(new_meal)

    return data, 201


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def update(user, username, id, body):
    old_meal = get_meal(username, id)
    user = get_user(username)

    schema = MealSchema(exclude=['user'])
    try:
        new_meal = schema.load(body, session=db.session)
    except ValidationError as e:
        fields = ", ".join(f"'{f}'" for f in sorted(e.messages))
        abort(400, f'Field(s): {fields} have the wrong format')

    new_meal.user_id = old_meal.user_id
    new_meal.id = old_meal.id

    if new_meal.name and new_meal.name != old_meal.name and not new_meal.calories:
        new_meal.calories = calories_from_nutritionix(new_meal.name)

    if new_meal.date:
        calories = get_daily_calories(user, old_meal.date)
        if calories >= user.daily_calories > calories - old_meal.calories:
            update_meals(user, old_meal.date, True)

        new_calories = new_meal.calories or old_meal.calories
        calories_new_date = get_daily_calories(user, new_meal.date)

        if user.daily_calories <= calories_new_date + new_calories:
            new_meal.under_daily_total = False
            if calories < user.daily_calories:
                update_meals(user, new_meal.date, False)
        else:
            new_meal.under_daily_total = True
    elif new_meal.calories and new_meal.calories != old_meal.calories:
        difference = new_meal.calories - old_meal.calories
        calories = get_daily_calories(user, old_meal.date)
        if (user.daily_calories > calories) != (user.daily_calories > calories + difference):
            update_meals(user, new_meal.date, user.daily_calories > calories + difference)
            new_meal.under_daily_total = user.daily_calories > calories + difference

    db.session.merge(new_meal)

    db.session.commit()

    data = schema.dump(old_meal)

    return data, 200


@is_allowed(roles_allowed=[Role.USER], only_allow_self=True)
def delete(user, username, id):
    user = get_user(username)
    meal = get_meal(username, id)
    calories = get_daily_calories(user, meal.date)

    if calories >= user.daily_calories > calories - meal.calories:
        update_meals(user, meal.date, True)

    db.session.delete(meal)
    db.session.commit()
    return make_response(jsonify({'message': f"Meal '{id}' deleted", 'success': True}), 200)


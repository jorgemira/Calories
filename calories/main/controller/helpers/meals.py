"""
This module contains helper functions to be used on the meals endpoints
"""
from marshmallow import ValidationError

from calories.main import db
from calories.main.controller.helpers import BadRequest, NotFound
from calories.main.controller.helpers.users import _get_user, get_daily_calories
from calories.main.models.models import Meal, User, MealSchema
from calories.main.util.external_apis import calories_from_nutritionix
from calories.main.util.filters import apply_filter

meal_schema = MealSchema(exclude=['user'])
meals_schema = MealSchema(many=True, exclude=['user'])


def get_meals(username, filter_str, items_per_page, page_number):
    """Get the list of meals for the specified user from the database

    :param username: Username of the user whose meals we need to get
    :type username: str
    :param filter_str: Filter string for the result
    :type filter_str: str
    :param items_per_page: Number of items per page
    :type items_per_page: int
    :param page_number: Page requested
    :type page_number: int
    :return: The list of the users filtered and paginated
    :rtype: list[User]
    """
    r_user = _get_user(username)

    meals = Meal.query.join(User, User.id == Meal.user_id).filter(User.username == r_user.username)
    meals, pagination = apply_filter(meals, filter_str, items_per_page, page_number)
    data = meals_schema.dump(meals)

    return data, pagination


def get_meal(username, meal_id):
    """Get the selected meal from the database

    :param username: Username of the user owner of the meal
    :type username: str
    :param meal_id: Id of the meal
    :type meal_id: int
    :return: The specified meal
    :rtype: Meal
    """
    return meal_schema.dump(_get_meal(username, meal_id))


def crt_meal(username, data):
    """Create a meal

    :param username: Username of the user owner of the meal
    :type username: str
    :param data: The data of the new meal
    :type data: dict
    :return: The newly created meal
    :rtype: Meal
    """
    user = _get_user(username)

    new_meal = _parse_meal(data)
    if not new_meal.calories:
        new_meal.calories = calories_from_nutritionix(new_meal.name)

    calories = get_daily_calories(user, new_meal.date)

    user.meals.append(new_meal)

    if user.daily_calories <= calories + new_meal.calories:
        new_meal.under_daily_total = False
        if calories < user.daily_calories:
            _update_meals(user, new_meal.date, False)
    else:
        new_meal.under_daily_total = True

    db.session.commit()

    return meal_schema.dump(new_meal)


def updt_meal(username, meal_id, data):
    """Update a meal

    :param username: Username of the user whose meal is going to be updated
    :type username: str
    :param meal_id: Id of the meal
    :type meal_id: int
    :param data: New data for the meal
    :type data: dict
    :return: The updated meal
    :rtype: Meal
    """
    old_meal = _get_meal(username, meal_id)
    user = _get_user(username)

    new_meal = _parse_meal(data)
    new_meal.user_id = old_meal.user_id
    new_meal.id = old_meal.id

    # Get calories from nutrtionix if the meal has changed but the user didn't provide its calories
    if new_meal.name and new_meal.name != old_meal.name and not new_meal.calories:
        new_meal.calories = calories_from_nutritionix(new_meal.name)

    if new_meal.date:  # Meal has changed date so we need to update under_daily_total for both dates
        # Update under_daily_limit for old date
        calories = get_daily_calories(user, old_meal.date)
        if calories >= user.daily_calories > calories - old_meal.calories:
            _update_meals(user, old_meal.date, True)

        # Update under_daily_limit for new date
        new_calories = new_meal.calories or old_meal.calories
        calories_new_date = get_daily_calories(user, new_meal.date)
        if user.daily_calories <= calories_new_date + new_calories:  # New date is over daily limit
            new_meal.under_daily_total = False
            if calories < user.daily_calories:  # New date was under daily limit before
                _update_meals(user, new_meal.date, False)
        else:  # New date will be still under daily limit
            new_meal.under_daily_total = True
    elif new_meal.calories and new_meal.calories != old_meal.calories:  # Calories have changed but its the same date
        difference = new_meal.calories - old_meal.calories
        calories = get_daily_calories(user, old_meal.date)
        # Change in calories made a difference
        if (user.daily_calories > calories) != (user.daily_calories > calories + difference):
            _update_meals(user, new_meal.date, user.daily_calories > calories + difference)
            new_meal.under_daily_total = user.daily_calories > calories + difference

    db.session.merge(new_meal)
    db.session.commit()

    return meal_schema.dump(old_meal)


def dlt_meals(username, meal_id):
    """Delete the selected meal from the database

    :param username: Username whose meal is going to be deleted
    :type username: str
    :param meal_id: Id of the meal that is going to be deleted
    :type meal_id: int
    :return: Nothing
    :rtype: None
    """
    d_user = _get_user(username)
    meal = _get_meal(username, meal_id)

    # Update under_daily_total for the day if necessary
    calories = get_daily_calories(d_user, meal.date)
    if calories >= d_user.daily_calories > calories - meal.calories:
        _update_meals(d_user, meal.date, True)

    db.session.delete(meal)
    db.session.commit()


def _get_meal(username, meal_id):
    """Get the specified meal from the database or abort with a 404 error if either the user or the meal don't exist

    :param username: Username that the meal belongs to
    :type username: str
    :param meal_id: Meal id
    :type meal_id: int
    :return: The database object for the meal
    :rtype: Meal
    :raises NotFound: If the user is not on the database
    """
    user = _get_user(username)
    meal = Meal.query.join(User, User.id == Meal.user_id).filter(User.username == user.username,
                                                                 Meal.id == meal_id).one_or_none()

    if meal is None:
        raise NotFound(f"Meal '{meal_id}' not found")

    return meal


def _update_meals(user, date, under_daily_total):
    """Update field under_daily_total of a given user on a givend day to the selected value. It does not commit changes to
    the database so everything can be part of the same transaction

    :param user: Username to update its meals
    :type user: User
    :param date: Date of the meals to be updated
    :type date: datetime.date
    :param under_daily_total: New value for under_daily_total
    :type under_daily_total: bool
    :return: Nothing
    """
    for meal in Meal.query.filter(User.username == user.username, Meal.date == date):
        meal.under_daily_total = under_daily_total


def _parse_meal(body):
    """Create a meal from a request body

    :param body:
    :return:
    :rtype: Meal
    """
    try:
        return meal_schema.load(body, session=db.session)
    except ValidationError as e:
        fields = ", ".join(f"'{f}'" for f in sorted(e.messages))
        raise BadRequest(f'Field(s): {fields} have the wrong format')

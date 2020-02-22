from datetime import date, time

from calories.main import db
from calories.main.models.models import User, Meal

ADMNIN_USER = {
    "username": "admin",
    "password": "admin1234",
    "name": "Administrator",
    "email": "admin@adminmail.com",
    "role": "ADMIN",
    "daily_calories": 0,
    "meals": []
}


def build_db():
    """This function recreates the database, drops any existing version, creates a new one and adds the default admin
    user

    :rtype: None
    """
    # Clean database
    db.drop_all()

    # Create the database
    db.create_all()
    # Create admin user
    db.session.add(User(**ADMNIN_USER))

    # Save changes to database
    db.session.commit()


def populate_db():
    """Populate the database using sample data

    :rtype: None
    """
    users = [
        {
            "username": "user1",
            "password": "pass_user1",
            "name": "User 1",
            "email": "user1@usermail.com",
            "role": "USER",
            "daily_calories": 2500,
            "meals": [
                {
                    "date": date(2020, 2, 11),
                    "time": time(15, 0, 3),
                    "name": "meal 1",
                    "grams": 100,
                    "description": "Meal 1 User 1",
                    "calories": 500,
                    "under_daily_total": False,
                },
                {
                    "date": date(2020, 2, 11),
                    "time": time(15, 10, 3),
                    "name": "meal 2",
                    "grams": 100,
                    "description": "Meal 2 User 1",
                    "calories": 2100,
                    "under_daily_total": False,
                }
            ]
        },
        {
            "username": "user2",
            "password": "pass_user2",
            "name": "User 2",
            "email": "user2@usemail.com",
            "role": "USER",
            "daily_calories": 3000,
            "meals": [
                {
                    "date": date(2020, 2, 11),
                    "time": time(15, 0, 3),
                    "name": "cheese",
                    "grams": 100,
                    "description": "Meal 3 User 2",
                    "calories": 500,
                    "under_daily_total": True,
                }
            ]
        },
        {
            "username": "manager1",
            "password": "pass_manager1",
            "name": "Manager 1",
            "email": "manager1@managermail.com",
            "role": "MANAGER",
            "daily_calories": 2000,
            "meals": []
        },
        {
            "username": "manager2",
            "password": "pass_manager2",
            "name": "Manager 2",
            "email": "manager2@managermail.com",
            "role": "MANAGER",
            "daily_calories": 4000,
            "meals": []
        },
    ]
    for user in users:
        u = User(username=user.get('username'),
                 password=user.get('password'),
                 name=user.get('name'),
                 email=user.get('email'),
                 role=user.get('role'),
                 daily_calories=user.get('daily_calories'))
        for meal in user.get('meals'):
            u.meals.append(Meal(user_id=meal.get(''),
                                date=meal.get('date'),
                                time=meal.get('time'),
                                name=meal.get('name'),
                                grams=meal.get('grams'),
                                description=meal.get('description'),
                                calories=meal.get('calories')))
        db.session.add(u)

    db.session.commit()


if __name__ == '__main__':
    build_db()

import os
from datetime import date, time

from config import db, basedir
from models import User, Meal

USERS = [
    {
        "username": "jmira",
        "password": "bollox",
        "name": "Jorge",
        "email": "jmira@gmail.com",
        "role": "ADMIN",
        "daily_calories": 2500,
        "meals": [
            {"id": 1,
             "user_id": 1,
             "date": date(2020, 2, 11),
             "time": time(15, 0, 3),
             "name": "cheese",
             "grams": 100,
             "description": "awesome stilton blue cheese",
             "calories": 500,
             "under_daily_total": True,
             }
        ]
    },
]

# Delete database file
db.drop_all()

# Create the database
db.create_all()

# iterate over the PEOPLE structure and populate the database
for user in USERS:
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

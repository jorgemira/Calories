from marshmallow import fields
from marshmallow_enum import EnumField

from calories.main import db, ma
from calories.main.models.user import Role


class Meal(db.Model):
    __tablename__ = "meal"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    name = db.Column(db.String(128))
    grams = db.Column(db.Integer, default=0)
    description = db.Column(db.String)
    calories = db.Column(db.Integer, default=0)
    under_daily_total = db.Column(db.Boolean, default=True)


class MealSchema(ma.ModelSchema):
    class Meta:
        model = Meal
        sqla_session = db.session

    user = fields.Nested('MealUserSchema', default=None)


class MealUserSchema(ma.ModelSchema):
    """
    This class exists to get around a recursion issue
    """
    id = fields.Integer()
    username = fields.String()
    password = fields.String()
    name = fields.String()
    email = fields.String()
    role = EnumField(Role)
    daily_calories = fields.Integer()

from enum import Enum

from marshmallow import fields
from marshmallow_enum import EnumField
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import generate_password_hash

from calories.main import db, ma


class Role(str, Enum):
    USER = 'USER'
    MANAGER = 'MANAGER'
    ADMIN = 'ADMIN'


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    _password = db.Column('password', db.String(128))
    name = db.Column(db.String(128))
    email = db.Column(db.String(128))
    role = db.Column(db.Enum(Role))
    daily_calories = db.Column(db.Integer)
    meals = db.relationship(
        "Meal",
        backref="user",
        cascade="all, delete, delete-orphan",
        single_parent=True,
    )

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, plaintext):
        self._password = generate_password_hash(plaintext)



class UserSchema(ma.ModelSchema):
    class Meta:
        model = User
        sqla_session = db.session

    meals = fields.Nested('UserMealSchema', default=[], many=True)


class UserMealSchema(ma.ModelSchema):
    """
    This class exists to get around a recursion issue
    """
    id = fields.Integer()
    user_id = fields.Integer()
    date = fields.Date()
    time = fields.Time()
    name = fields.String()
    grams = fields.Integer()
    description = fields.String()
    calories = fields.Integer()
    under_daily_total = fields.Boolean()
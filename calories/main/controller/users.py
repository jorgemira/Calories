"""
This is the users module and supports all the REST actions for the users data
"""

from flask import abort, make_response, jsonify
from marshmallow import INCLUDE

from calories.main import db
from calories.main.controller.auth import is_allowed
from calories.main.controller.helpers import get_user
from calories.main.models.models import User, UserSchema, Role
from calories.main.util.filters import apply_filter


@is_allowed(roles_allowed=[Role.MANAGER])
def read_all(user, filter='', itemsPerPage=None, pageNumber=None):
    users = User.query.order_by(User.username)

    users = apply_filter(users, filter, itemsPerPage, pageNumber)

    user_schema = UserSchema(many=True, exclude=('id', '_password', 'meals'))
    data = user_schema.dump(users)

    return data


@is_allowed(roles_allowed=[Role.MANAGER], allow_self=True)
def read_one(user, username):
    user = get_user(username)
    user_schema = UserSchema(exclude=('id', '_password', 'meals'))
    data = user_schema.dump(user)

    return data


@is_allowed(roles_allowed=[Role.MANAGER])
def create(user, body):
    username = body.get("username")
    existing_user = User.query.filter(User.username == username).one_or_none()

    if existing_user:
        abort(409, f"User '{username}' exists already")

    schema = UserSchema(exclude=('id', '_password', 'meals'), unknown=INCLUDE)
    new_user = schema.load(body, session=db.session)

    if get_user(user).role == Role.MANAGER and new_user.role != Role.USER:
        abort(401, f"User '{user}' can only create users with role USER")

    if not body['username'].isalnum():
        abort(400, f"Username must contain only alphanumeric characters")

    db.session.add(new_user)
    db.session.commit()

    data = schema.dump(new_user)

    return data, 201


@is_allowed(roles_allowed=[Role.MANAGER], allow_self=True)
def update(user, username, body):
    update_user = get_user(username)

    schema = UserSchema(exclude=('id', '_password', 'meals'), unknown=INCLUDE)
    updated = schema.load(body, session=db.session)

    if updated.role and updated.role != update_user.role and get_user(user).role != Role.ADMIN:
        abort(401, f"User '{user}' is not allowed to change Role")

    if not body.get('username', 'a').isalnum():
        abort(400, f"Username must contain only alphanumeric characters")

    updated.id = update_user.id

    db.session.merge(updated)
    db.session.commit()

    data = schema.dump(update_user)

    return data, 200


@is_allowed(roles_allowed=[Role.MANAGER], allow_self=True)
def delete(user, username):
    delete_user = get_user(username)

    if get_user(user).role == Role.MANAGER and delete_user.role != Role.USER:
        abort(401, f"User '{user}' can only delete users with role USER")

    db.session.delete(delete_user)
    db.session.commit()

    return make_response(jsonify({'message': f"User '{username}' deleted", 'success': True}), 200)

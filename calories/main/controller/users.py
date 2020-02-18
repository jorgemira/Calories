"""
This is the users module and supports all the REST actions for the
users data
"""

from flask import make_response, abort
from marshmallow import INCLUDE

from calories.main import db
from calories.main.controller.auth import is_allowed
from calories.main.util.filters import apply_filter
from calories.main.models.meal import Meal
from calories.main.models.user import User, UserSchema, Role


@is_allowed(roles_allowed=[Role.MANAGER])
def read_all(user, filter=None, itemsPerPage=None, pageNumber=None):
    """
    This function responds to a request for /api/users
    with the complete lists of users
    :return:        json string of list of users
    """
    users = User.query.all()
    users = apply_filter(users, filter, itemsPerPage, pageNumber)

    # Serialize the data for the response
    user_schema = UserSchema(many=True, exclude=('id', '_password'))
    data = user_schema.dump(users)
    return data


@is_allowed(roles_allowed=[Role.MANAGER])
def read_one(user, username):
    """
    This function responds to a request for /api/users/{user_id}
    with one matching user from users
    :param user_id:   Id of user to find
    :return:            user matching id
    """
    # Build the initial query
    user = User.query.filter(User.username == username).outerjoin(Meal).one_or_none()

    # Did we find a user?
    if user is not None:

        # Serialize the data for the response
        user_schema = UserSchema(exclude=('id', '_password'))
        data = user_schema.dump(user)
        return data

    # Otherwise, nope, didn't find that user
    else:
        abort(404, f"User '{username}' not found")


@is_allowed(roles_allowed=[Role.MANAGER])
def create(user, body):
    """
    This function creates a new user in the users structure
    based on the passed in user data
    :param body:  user to create in users structure
    :return:        201 on success, 406 on user exists
    """
    username = body.get("username")
    existing_user = User.query.filter(User.username == username).one_or_none()

    # Can we insert this user?
    if existing_user is None:

        # Create a user instance using the schema and the passed in user
        schema = UserSchema(exclude=('id', '_password', 'meals'), unknown=INCLUDE)
        new_user = schema.load(body, session=db.session)

        # Add the user to the database
        db.session.add(new_user)
        db.session.commit()

        # Serialize and return the newly created user in the response
        data = schema.dump(new_user)

        return data, 201

    # Otherwise, nope, user exists already
    else:
        abort(409, f"User {username} exists already")


@is_allowed(roles_allowed=[Role.MANAGER])
def update(user, username, body):
    """
    This function updates an existing user in the users structure
    :param username:   Id of the user to update in the users structure
    :param body:      user to update
    :return:            updated user structure
    """
    # Get the user requested from the db into session
    # TODO not allow to update username
    update_user = User.query.filter(User.username == username).one_or_none()

    if update_user is not None:

        # turn the passed in user into a db object
        schema = UserSchema(exclude=('id', '_password', 'meals'))
        updated = schema.load(body, session=db.session)

        # Set the id to the user we want to update
        updated.user_id = update_user.user_id

        # merge the new object into the old and commit it to the db
        db.session.merge(updated)
        db.session.commit()

        # return updated user in the response
        data = schema.dump(update_user)

        return data, 200
    else:
        abort(404, f"User {username} not found")


@is_allowed(roles_allowed=[Role.MANAGER])
def delete(user, username):
    """
    This function deletes a user from the users structure
    :param username:   Id of the user to delete
    :return:          200 on successful delete, 404 if not found
    """
    # Get the user requested
    delete_user = User.query.filter(User.username == username).one_or_none()

    if delete_user is not None:
        db.session.delete(delete_user)
        db.session.commit()
        return make_response(f"User '{username}' deleted", 200)
    else:
        abort(404, f"User '{username}' not found")

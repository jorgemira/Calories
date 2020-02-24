"""
This module contains helper functions to be used on the auth endpoints
"""
import time
from functools import wraps

from flask import abort
from jose import jwt
from werkzeug.security import check_password_hash

from calories.main import cfg, logger
from calories.main.controller.helpers import Unauthorized
from calories.main.controller.helpers.users import _get_user
from calories.main.models.models import Role

JWT_ALGORITHM = 'HS256'


def get_token(username, password):
    """Create a token

    :param username: Username of the user that requests the token
    :type username: str
    :param password: Password  of the user that requests the token
    :type password: str
    :return: The token
    :rtype: str
    :raises Unauthorized: If the password is wrong
    """
    user = _get_user(username)

    if not check_password_hash(user.password, password):
        raise Unauthorized(f"Wrong password for user '{username}'")

    return encode_token(user.username)


def encode_token(username):
    """Create a token for the user that requested it

    :param username: User to create the token for
    :type username: str
    :return: The already encoded token
    :rtype: str
    """
    timestamp = int(time.time())
    payload = {
        "iat": int(timestamp),
        "exp": int(timestamp + cfg.TOKEN_LIFETIME_SECONDS),
        "sub": username,
    }
    token = jwt.encode(payload, cfg.TOKEN_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return token


def is_allowed(roles_allowed=None, allow_self=False, only_allow_self=False):
    """Decorate a function to check if the user is allowed to perform the action

    :param roles_allowed: List of the roles allowed to make requests to the endpoint
    :type roles_allowed: list[str]
    :param allow_self: If set to True, the user can perform the action to himself even if it is not in roles_allowed
    :type allow_self: bool
    :param only_allow_self: If set to True, user needs to be in roles_allowed and he can only do the action to himself
    :type only_allow_self: bool
    :return: The endpoint that decorates or a 401 error if the user is not allowed
    """

    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            nonlocal roles_allowed
            if roles_allowed is None:
                roles_allowed = []

            user = _get_user(kwargs['user'])

            # Admin can do everything
            if user.role == Role.ADMIN:
                logger.info(f"User '{user.username}' with role '{user.role}' succesfully called '{func.__name__}' with "
                            f"args='{args}' and kwargs='{kwargs}'")
                return func(*args, **kwargs)

            if only_allow_self:
                if user.role not in roles_allowed:
                    abort(403, f"User '{kwargs['user']}' belongs to the role '{user.role}' and is not allowed to"
                               f" perform the action")
                if user.username != kwargs.get('username', user.username):
                    abort(403, f"User '{kwargs['user']}' cannot perform the action for other user")
                logger.info(f"User '{user.username}' with role '{user.role}' succesfully called '{func.__name__}' with "
                            f"args='{args}' and kwargs='{kwargs}'")
                return func(*args, **kwargs)

            if user.role in roles_allowed or (allow_self and user.username == kwargs.get('username', None)):
                logger.info(f"User '{user.username}' with role '{user.role}' succesfully called '{func.__name__}' with "
                            f"args='{args}' and kwargs='{kwargs}'")
                return func(*args, **kwargs)
            else:
                abort(403, f"User '{kwargs['user']}' belongs to the role '{user.role}' and is not allowed to"
                           f" perform the action")

        return wrapped

    return decorator

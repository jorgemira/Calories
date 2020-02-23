"""
This module supports all authentication actions
"""

import time
from functools import wraps

from flask import abort
from jose import JWTError, jwt
from werkzeug.security import check_password_hash

from calories.main import cfg, logger
from calories.main.controller.helpers import get_user
from calories.main.models.models import Role

JWT_ALGORITHM = 'HS256'


def login(body):
    """Login a user, if the credentials are right it returns a token for the user

    :param body: The request body, must contain username and password
    :type body: dict[str, str]
    :return: 201 Status if login was correct, 404 if user does not exists and 401 if the password is wrong
    """
    username = body.get('username')
    password = body.get('password')
    user = get_user(username)

    if not check_password_hash(user.password, password):
        logger.info(f"User '{username}' tried to log in with wrong password")
        abort(401, f"Wrong password for user '{username}'")

    logger.info(f"User '{username}' logged in correctly")

    token = encode_token(user.username)
    return {'status': 201,
            'title': 'Success',
            'detail': f"User '{username}' successfully logged in",
            'Authorization': token
            }, 201


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


def decode_token(token):
    """Decode the given token

    :param token:
    :type token: str
    :return:
    :rtype: dict[str, str]
    """
    try:
        return jwt.decode(token, cfg.TOKEN_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        logger.warning(f"Error decoding token: '{e}'")
        abort(401, "Invalid authentication token")


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

            user = get_user(kwargs['user'])

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

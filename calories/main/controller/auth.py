"""
Basic example of a resource server
"""
import logging
import time
from functools import wraps

from flask import abort
from jose import JWTError, jwt
from werkzeug.security import check_password_hash

from calories.main.controller.helpers import get_user
from calories.main.models.models import Role
from calories.main import cfg

JWT_ALGORITHM = 'HS256'

logger = logging.getLogger(__name__)


def login(body):
    username = body.get('username')
    password = body.get('password')
    user = get_user(username)

    if not check_password_hash(user.password, password):
        abort(401, f"Wrong password for user '{username}'")

    timestamp = _current_timestamp()
    payload = {
        "iat": int(timestamp),
        "exp": int(timestamp + cfg.TOKEN_LIFETIME_SECONDS),
        "sub": str(username),
    }

    response = {
        'status': 201,
        'title': 'Success',
        'detail': f"User '{username}' successfully logged in",
        'Authorization': jwt.encode(payload, cfg.TOKEN_SECRET_KEY, algorithm=JWT_ALGORITHM)
    }
    return response, 201


def decode_token(token):
    try:
        return jwt.decode(token, cfg.TOKEN_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        abort(401, "Invalid authentication token")


def _current_timestamp():
    return int(time.time())


def is_allowed(roles_allowed=None, allow_self=False, only_allow_self=False):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            nonlocal roles_allowed
            if roles_allowed is None:
                roles_allowed = []

            user = get_user(kwargs['user'])

            # Admin can do everything
            if user.role == Role.ADMIN:
                return func(*args, **kwargs)

            if only_allow_self:
                if user.role not in roles_allowed:
                    abort(401, f"User '{kwargs['user']}' belongs to the role '{user.role}' and is not allowed to"
                               f" perform the action")
                if user.username != kwargs.get('username', user.username):
                    abort(401, f"User '{kwargs['user']}' cannot perform the action for other user")
                return func(*args, **kwargs)

            if user.role in roles_allowed or (allow_self and user.username == kwargs.get('username', None)):
                return func(*args, **kwargs)
            else:
                abort(401, f"User '{kwargs['user']}' belongs to the role '{user.role}' and is not allowed to"
                           f" perform the action")

        return wrapped

    return decorator

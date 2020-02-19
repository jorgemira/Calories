"""
Basic example of a resource server
"""
import logging
import time
from functools import wraps

from flask import abort, jsonify, make_response
from jose import JWTError, jwt
from werkzeug.security import check_password_hash

from calories.main.models.models import Role, User

JWT_ISSUER = 'app.calories'
JWT_SECRET = '*&UbA>>D5nj6S_6KaIp*$5sppQS-B'
JWT_LIFETIME_SECONDS = 6000
JWT_ALGORITHM = 'HS256'

logger = logging.getLogger(__name__)


def login(body):
    username = body.get('username')
    password = body.get('password')
    user = User.query.filter(User.username == username).one_or_none()
    if not user:
        abort(401, f"User '{username}' not found")
    if not check_password_hash(user.password, password):
        abort(401, f"Wrong password for user '{username}'")

    timestamp = _current_timestamp()
    payload = {
        "iss": JWT_ISSUER,
        "iat": int(timestamp),
        "exp": int(timestamp + JWT_LIFETIME_SECONDS),
        "sub": str(username),
    }

    response = {
        'status': 201,
        'title': 'Success',
        'detail': f"User '{username}' successfully logged in",
        'Authorization': jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    }
    return response, 201


def decode_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        abort(401, "Invalid authentication token")


def _current_timestamp():
    return int(time.time())


def is_allowed(roles_allowed=None):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            nonlocal roles_allowed
            if roles_allowed is None:
                roles_allowed = []
            user = User.query.filter(User.username == kwargs['user']).one_or_none()
            if user is None:
                abort(401, f"Username '{kwargs['user']}' not found")
            elif user.role not in roles_allowed + [Role.ADMIN] and user.username != kwargs.get('username', None):
                abort(401, f"User '{kwargs['user']}' belongs to the role '{user.role}' and is not allowed to"
                           f" perform the action")
            else:
                return func(*args, **kwargs)
            return func(*args, **kwargs)

        return wrapped

    return decorator

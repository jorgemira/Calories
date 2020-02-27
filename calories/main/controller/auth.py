"""
This module supports all authentication actions
"""

from flask import abort
from jose import JWTError, jwt

from calories.main import cfg, logger
from calories.main.controller.helpers import RequestError
from calories.main.controller.helpers.auth import get_token

JWT_ALGORITHM = 'HS256'


def login(body):
    """Login a user, if the credentials are right it returns a token for the user

    :param body: The request body, must contain username and password
    :type body: dict[str, str]
    :return: 201 Status if login was correct, 404 if user does not exists and 401 if the password is wrong
    """
    username = body.get('username')
    password = body.get('password')

    try:
        token = get_token(username, password)
    except RequestError as e:
        token = None
        logger.warn(e.message)
        abort(e.code, e.message)

    logger.info(f"User '{username}' logged in correctly")

    return {'status': 200,
            'title': 'Success',
            'detail': f"User '{username}' successfully logged in",
            'Authorization': token
            }, 200


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

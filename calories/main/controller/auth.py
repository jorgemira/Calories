"""
This module supports all authentication actions
"""
from typing import Dict

from flask import abort
from jose import JWTError, jwt

from calories.main import cfg, logger
from calories.main.controller import RequestBodyType, ResponseType
from calories.main.controller.helpers import RequestError
from calories.main.controller.helpers.auth import get_token

JWT_ALGORITHM = "HS256"


def login(body: RequestBodyType) -> ResponseType:
    """Login a user, if the credentials are right it returns a token for the
    user

    :param body: The request body, must contain username and password
    :return: 201 Status if login was correct, 404 if user does not exists and
    401 if the password is wrong
    """
    username = body.get("username")
    password = body.get("password")

    try:
        token = get_token(username, password)
    except RequestError as e:
        token = None
        logger.warning(e.message)
        abort(e.code, e.message)

    logger.info(f"User '{username}' logged in correctly")

    return (
        {
            "status": 200,
            "title": "Success",
            "detail": f"User '{username}' successfully logged in",
            "Authorization": token,
        },
        200,
    )


def decode_token(token: str) -> Dict[str, str]:
    """Decode the given token"""
    try:
        return jwt.decode(token, cfg.TOKEN_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        logger.warning(f"Error decoding token: '{e}'")
        abort(401, "Invalid authentication token")

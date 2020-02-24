"""
Exceptions to be used by the helper functions
"""


class RequestError(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class BadRequest(RequestError):
    def __init__(self, message):
        super().__init__(message, 400)


class Unauthorized(RequestError):
    def __init__(self, message):
        super().__init__(message, 401)


class Forbidden(RequestError):
    def __init__(self, message):
        super().__init__(message, 403)


class NotFound(RequestError):
    def __init__(self, message):
        super().__init__(message, 404)


class Conflict(RequestError):
    def __init__(self, message):
        super().__init__(message, 409)

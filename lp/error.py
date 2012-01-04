#===============
#  Errors
#===============

class Error(Exception):
    """A general error."""

class ValidationError(Exception):
    """Raised when a value fails the validation of its format."""

class RequestError(Exception):
    """Raised when the request path is bad."""
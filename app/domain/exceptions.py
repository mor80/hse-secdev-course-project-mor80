class WishlistException(Exception):
    """Base exception for Wishlist application"""

    pass


class AuthenticationError(WishlistException):
    """Authentication related errors"""

    pass


class AuthorizationError(WishlistException):
    """Authorization related errors"""

    pass


class ValidationError(WishlistException):
    """Data validation errors"""

    pass


class NotFoundError(WishlistException):
    """Resource not found errors"""

    pass


class DuplicateError(WishlistException):
    """Duplicate resource errors"""

    pass

from http import HTTPStatus


class BusinessError(Exception):
    """Base class for business logic errors."""
    status_code: int = HTTPStatus.BAD_REQUEST
    detail: str = "Business logic error"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.detail
        super().__init__(self.detail)


class NotFoundError(BusinessError):
    status_code = HTTPStatus.NOT_FOUND
    detail = "Resource not found"


class ConflictError(BusinessError):
    status_code = HTTPStatus.CONFLICT
    detail = "Resource conflict"


class ValidationError(BusinessError):
    status_code = HTTPStatus.BAD_REQUEST
    detail = "Validation failed"
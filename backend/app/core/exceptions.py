from __future__ import annotations

from fastapi import HTTPException
from typing import Optional, Any


class BaseAPIException(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Any] = None,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details
        super().__init__(status_code=status_code, detail=self._format_error())

    def _format_error(self) -> dict:
        error = {
            "error": True,
            "message": self.message,
            "error_code": self.error_code,
        }
        if self.details:
            error["details"] = self.details
        return error


class NotFoundException(BaseAPIException):
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(status_code=404, message=message, error_code="NOT_FOUND", details=details)


class UnauthorizedException(BaseAPIException):
    def __init__(self, message: str = "Not authenticated", details: Optional[Any] = None):
        super().__init__(status_code=401, message=message, error_code="UNAUTHORIZED", details=details)


class ForbiddenException(BaseAPIException):
    def __init__(self, message: str = "Access denied", details: Optional[Any] = None):
        super().__init__(status_code=403, message=message, error_code="FORBIDDEN", details=details)


class BadRequestException(BaseAPIException):
    def __init__(self, message: str = "Bad request", details: Optional[Any] = None):
        super().__init__(status_code=400, message=message, error_code="BAD_REQUEST", details=details)


class ValidationException(BaseAPIException):
    def __init__(self, message: str = "Validation error", details: Optional[Any] = None):
        super().__init__(status_code=422, message=message, error_code="VALIDATION_ERROR", details=details)


class ConflictException(BaseAPIException):
    def __init__(self, message: str = "Resource conflict", details: Optional[Any] = None):
        super().__init__(status_code=409, message=message, error_code="CONFLICT", details=details)


class InternalServerError(BaseAPIException):
    def __init__(self, message: str = "Internal server error", details: Optional[Any] = None):
        super().__init__(status_code=500, message=message, error_code="INTERNAL_ERROR", details=details)


class ServiceUnavailableException(BaseAPIException):
    def __init__(self, message: str = "Service unavailable", details: Optional[Any] = None):
        super().__init__(status_code=503, message=message, error_code="SERVICE_UNAVAILABLE", details=details)

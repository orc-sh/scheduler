from http import HTTPStatus

from fastapi import HTTPException


class NotFoundException(HTTPException):
    def __init__(
        self,
        status_code: int = HTTPStatus.NOT_FOUND,
        detail: str = "Item not found",
        error_code: str = "",
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code

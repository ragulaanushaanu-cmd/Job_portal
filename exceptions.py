import logging

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    logger.warning(
        "Validation error on %s %s: %s",
        request.method,
        request.url.path,
        exc.errors(),
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "The request contains invalid data.",
            "details": jsonable_encoder(exc.errors()),
        },
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
):
    logger.exception(
        "Database error on %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Database Error",
            "message": "A database error occurred.",
        },
    )


async def general_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception(
        "Unhandled exception on %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred.",
        },
    )
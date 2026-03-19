import logging

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from backend.routers.health import router as health_router
from fastapi.middleware.cors import CORSMiddleware
from backend.database.init_db import init_db
from backend.routers.estimate import router as estimate_router
from backend.routers.profile import router as profile_router
from backend.routers.auth import router as auth_router
from backend.routers.chat import router as chat_router
from backend.routers.food_log import router as food_log_router
from backend.routers.insights import router as insights_router
from backend.services.estimate_service import create_estimate_validation_error_response

logger = logging.getLogger(__name__)

CORS_ORIGINS = ["http://localhost:3000", "http://100.64.164.2:3000"]

app = FastAPI()
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(health_router)
app.include_router(estimate_router)
app.include_router(profile_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(food_log_router)
app.include_router(insights_router)


def _cors_headers(request: Request | None = None) -> dict[str, str]:
    origin = request.headers.get("origin") if request else None
    if origin and origin in CORS_ORIGINS:
        return {"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Credentials": "true"}
    return {"Access-Control-Allow-Origin": CORS_ORIGINS[0], "Access-Control-Allow-Credentials": "true"}


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    request: Request,
    exc: RequestValidationError,
):
    if request.url.path == "/estimate":
        return create_estimate_validation_error_response(exc.errors())

    return await request_validation_exception_handler(request, exc)


@app.exception_handler(Exception)
async def handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试。"},
        headers=_cors_headers(request),
    )

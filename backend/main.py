from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from backend.routers.health import router as health_router
from fastapi.middleware.cors import CORSMiddleware
from backend.database.init_db import init_db
from backend.routers.estimate import router as estimate_router
from backend.routers.profile import router as profile_router
from backend.routers.auth import router as auth_router
from backend.routers.chat import router as chat_router
from backend.services.estimate_service import create_estimate_validation_error_response

app = FastAPI()
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000", "http://100.64.164.2:3000"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

app.include_router(health_router)
app.include_router(estimate_router)
app.include_router(profile_router)
app.include_router(auth_router)
app.include_router(chat_router)


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    request: Request,
    exc: RequestValidationError,
):
    if request.url.path == "/estimate":
        return create_estimate_validation_error_response(exc.errors())

    return await request_validation_exception_handler(request, exc)

from fastapi import FastAPI
from backend.routers.health import router as health_router
from fastapi.middleware.cors import CORSMiddleware
from backend.database.init_db import init_db
from backend.routers.profile import router as profile_router

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
app.include_router(profile_router)

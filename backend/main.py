from fastapi import FastAPI
from backend.routers.health import router as health_router
from fast.api.middleare.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000", "http://100.64.164.2:3000"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

app.include_router(health_router)

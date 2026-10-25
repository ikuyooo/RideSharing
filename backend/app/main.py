import logging

from fastapi import FastAPI

from app.api import health
from app.core.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    app = FastAPI(title="Ride-Sharing Platform API", version="0.0.1")
    app.include_router(health.router)
    return app


app = create_app()

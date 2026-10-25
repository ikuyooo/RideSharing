from fastapi import FastAPI

from app.api import health
from app.core.errors import install_error_handlers
from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.modules.driver import api as driver_api
from app.modules.identity import api as identity_api
from app.modules.trip import api as trip_api


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title="Ride-Sharing Platform API", version="0.1.0")
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(identity_api.router)
    app.include_router(driver_api.router)
    app.include_router(trip_api.router)
    return app


app = create_app()

from fastapi import FastAPI
from app.api.v1.health import health_router
from app.api.v1.auth import auth_router
from app.core.config import settings

def create_application() -> FastAPI:
    """Application factory for HITRAG Backend FastAPI service."""
    application = FastAPI(
        title=settings.APP_NAME,
        description="Institutional RAG Assistant API for Harare Institute of Technology",
        version="0.1.0",
        debug=settings.DEBUG,
    )

    # Register API routers
    application.include_router(health_router)
    application.include_router(auth_router)

    return application

app = create_application()

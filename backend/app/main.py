from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.health import health_router
from app.api.v1.auth import auth_router
from app.api.v1.debug import debug_router
from app.api.v1.conversations import conversations_router
from app.core.config import settings

def create_application() -> FastAPI:
    """Application factory for HITRAG Backend FastAPI service."""
    application = FastAPI(
        title=settings.APP_NAME,
        description="Institutional RAG Assistant API for Harare Institute of Technology",
        version="0.1.0",
        debug=settings.DEBUG,
    )

    # Configure CORS Middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(debug_router)
    application.include_router(conversations_router)

    return application

app = create_application()

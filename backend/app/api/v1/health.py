from fastapi import APIRouter

health_router = APIRouter(tags=["Health"])

@health_router.get("/health")
def health_check():
    """Diagnostic health check endpoint returning server status."""
    return {"status": "ok"}

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db

health_router = APIRouter(tags=["Health"])

@health_router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Diagnostic health check endpoint returning server and database connectivity status."""
    try:
        # Execute SELECT 1 to verify database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "connected"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "database": "disconnected",
                "message": str(e)
            }
        )

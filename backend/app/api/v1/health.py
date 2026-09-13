"""Health check API endpoint."""

from fastapi import APIRouter, status
from app.core.config import settings
from app.db.session import check_db_connection
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Returns the operational status of the service and database connectivity.",
)
def get_health() -> HealthResponse:
    """Return application health and database connection status."""
    db_connected = check_db_connection()
    return HealthResponse(
        status="ok",
        app=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database_connected=db_connected,
    )

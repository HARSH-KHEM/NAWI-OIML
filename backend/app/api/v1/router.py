"""API v1 master router registering all domain routers."""

from fastapi import APIRouter
from app.api.v1.attempts import router as attempts_router
from app.api.v1.evaluations import router as evaluations_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.health import router as health_router
from app.api.v1.instruments import router as instruments_router
from app.api.v1.observations import router as observations_router
from app.api.v1.tests import router as tests_router

api_v1_router = APIRouter()

# Register sub-routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(instruments_router)
api_v1_router.include_router(evaluations_router)
api_v1_router.include_router(tests_router)
api_v1_router.include_router(attempts_router)
api_v1_router.include_router(observations_router)
api_v1_router.include_router(evidence_router)

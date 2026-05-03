"""Health and readiness check endpoints."""

import os
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns 200 when the service is alive. Used by Cloud Run health checks.",
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "production"),
    )

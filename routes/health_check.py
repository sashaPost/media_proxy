from fastapi import APIRouter
from pydantic import BaseModel


health_router = APIRouter()


class HealthResponse(BaseModel):
    status: str


@health_router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy")

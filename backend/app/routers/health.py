"""Endpoint de saude: prova que o caminho frontend -> proxy -> backend esta ligado."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "weather-dashboard-backend"}

"""API layer — route registration."""

from fastapi import APIRouter

from app.api.v1 import analytics, auth, contents, knowledge, personas, publish, topics

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(personas.router)
api_router.include_router(contents.router)
api_router.include_router(topics.router)
api_router.include_router(publish.router)
api_router.include_router(knowledge.router)
api_router.include_router(analytics.router)
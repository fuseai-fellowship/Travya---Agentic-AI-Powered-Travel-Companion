from fastapi import APIRouter
from app.api.routes import items, login, private, users, utils, agents, agentic, simple_agentic, travel, ai_travel, documents, health, evaluation, monitoring, conversations, photo_gallery, map_parser
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(agents.router)
api_router.include_router(agentic.router)
api_router.include_router(simple_agentic.router)
api_router.include_router(travel.router)
api_router.include_router(ai_travel.router)
api_router.include_router(conversations.router)
api_router.include_router(photo_gallery.router)
api_router.include_router(map_parser.router, prefix="/map-parser", tags=["map-parser"])
api_router.include_router(documents.router)
api_router.include_router(health.router)
api_router.include_router(evaluation.router)
api_router.include_router(monitoring.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)

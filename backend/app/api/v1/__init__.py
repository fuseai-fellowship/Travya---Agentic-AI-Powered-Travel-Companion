from fastapi import APIRouter

from app.api.v1 import account, chat, explore, health, trips

router = APIRouter()
router.include_router(health.router)
router.include_router(account.router)
router.include_router(trips.router)
router.include_router(chat.router)
router.include_router(explore.router)

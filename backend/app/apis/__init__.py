from fastapi import APIRouter

from .eps import eps_router

rest_router = APIRouter()
rest_router.include_router(eps_router)

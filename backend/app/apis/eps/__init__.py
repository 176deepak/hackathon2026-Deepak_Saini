from fastapi import APIRouter

from app.apis.eps.audit import router as audit_router
from app.apis.eps.auth import router as auth_router
from app.apis.eps.dashboard import router as dashboard_router
from app.apis.eps.system import router as system_router
from app.apis.eps.tickets import router as tickets_router
from app.core.config import envs

eps_router = APIRouter(prefix=f"/api/v{envs.APP_APIS_VERSION}")
eps_router.include_router(tickets_router)
eps_router.include_router(auth_router)
eps_router.include_router(audit_router)
eps_router.include_router(dashboard_router)
eps_router.include_router(system_router)

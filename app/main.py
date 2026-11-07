from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

from app.core.csrf import OriginCheckMiddleware
from app.domains.accounts.auth.router import router as auth_router
from app.domains.accounts.invitations.router import router as invitations_router
from app.domains.accounts.users.router import router as users_router
from app.domains.members.athletes.router import router as athletes_router
from app.domains.members.races.router import public_router as public_races_router
from app.domains.members.races.router import router as races_router

# Caddy reenvía /api/* a esta app, así que todas as rutas levan o prefixo /api
app = FastAPI(title="Triatlón Rianxo API", docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)
app.add_middleware(OriginCheckMiddleware)
if get_settings().cors_list:
    # Desenvolvemento: a web (localhost:4321) chama directamente á API (localhost:8001)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_list,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

for r in (auth_router, invitations_router, users_router, athletes_router, races_router, public_races_router):
    app.include_router(r, prefix="/api")


@app.get("/api/health")
async def health():
    return {"ok": True}

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.proxy_headers import ProxyHeadersMiddleware

from app.routes.web import router as web_router

app = FastAPI(title="Car3D Files")

# ✅ Esto hace que FastAPI respete X-Forwarded-Proto (https) en Railway
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(web_router)
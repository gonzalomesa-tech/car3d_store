from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes.web import router as web_router

app = FastAPI(title="Car3D Files", version="0.1.0")

# Static files (CSS/JS/IMG/GLB)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Web routes
app.include_router(web_router)
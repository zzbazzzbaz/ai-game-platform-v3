from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.endpoints import games, maintenance
from app.lifespan import lifespan

app = FastAPI(title="AI 游戏平台 v3", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router)
app.include_router(maintenance.router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

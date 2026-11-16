from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import games as game_repo
from app.repositories.models import Game


async def create(session: AsyncSession, name: str) -> Game:
    game = await game_repo.create_game(session, name=name)
    await game_repo.ensure_sandbox_row(session, game.id)
    return game


async def list_all(session: AsyncSession) -> list[Game]:
    return await game_repo.list_games(session)


async def get(session: AsyncSession, game_id: uuid.UUID) -> Game | None:
    return await game_repo.get_game(session, game_id)

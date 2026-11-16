from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.models import Game, SandboxSession


async def create_game(session: AsyncSession, *, name: str) -> Game:
    game = Game(name=name)
    session.add(game)
    await session.commit()
    await session.refresh(game)
    return game


async def list_games(session: AsyncSession) -> list[Game]:
    return list((await session.scalars(select(Game).order_by(Game.created_at.desc()))).all())


async def get_game(session: AsyncSession, game_id: uuid.UUID) -> Game | None:
    return await session.get(Game, game_id)


async def delete_game(session: AsyncSession, game_id: uuid.UUID) -> bool:
    result = await session.execute(delete(Game).where(Game.id == game_id).returning(Game.id))
    await session.commit()
    return bool(result.scalars().all())


async def get_sandbox(session: AsyncSession, game_id: uuid.UUID) -> SandboxSession | None:
    return await session.scalar(
        select(SandboxSession).where(SandboxSession.game_id == game_id)
    )


async def ensure_sandbox_row(session: AsyncSession, game_id: uuid.UUID) -> SandboxSession:
    """取或建沙盒记录；并发插入时回退到已有记录。"""
    row = await get_sandbox(session, game_id)
    if row is not None:
        return row
    row = SandboxSession(game_id=game_id)
    session.add(row)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing = await get_sandbox(session, game_id)
        if existing is None:
            raise
        return existing
    await session.refresh(row)
    return row


async def update_sandbox(
    session: AsyncSession,
    game_id: uuid.UUID,
    **values: Any,
) -> SandboxSession | None:
    row = await get_sandbox(session, game_id)
    if row is None:
        return None
    for key, value in values.items():
        setattr(row, key, value)
    await session.commit()
    await session.refresh(row)
    return row

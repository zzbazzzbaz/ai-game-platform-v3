from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException

from app.dependencies import AgentFactoryDep, RegistryDep, SessionFactoryDep
from app.dto.games import (
    ArchiveOut,
    ChatIn,
    ChatOut,
    GameCreate,
    GameOut,
    OpenOut,
    SandboxStatusOut,
    TouchOut,
)
from app.errors import game_not_found, sandbox_unavailable, workspace_busy
from app.repositories import games as game_repo
from app.runtime.sandboxes.errors import LockBusy, SandboxUnavailable
from app.services import agent_service, game_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/games", tags=["games"])


@router.post("", response_model=GameOut, status_code=201)
async def create_game(
    payload: GameCreate,
    session_factory: SessionFactoryDep,
) -> GameOut:
    async with session_factory() as session:
        game = await game_service.create(session, payload.name)
        return GameOut.model_validate(game)


@router.get("", response_model=list[GameOut])
async def list_games(session_factory: SessionFactoryDep) -> list[GameOut]:
    async with session_factory() as session:
        games = await game_service.list_all(session)
        return [GameOut.model_validate(game) for game in games]


@router.get("/{game_id}", response_model=SandboxStatusOut)
async def get_game(
    game_id: uuid.UUID,
    registry: RegistryDep,
    session_factory: SessionFactoryDep,
) -> SandboxStatusOut:
    async with session_factory() as session:
        game = await game_repo.get_game(session, game_id)
    if game is None:
        raise game_not_found()
    return SandboxStatusOut(**await registry.status(game_id))


@router.post("/{game_id}/open", response_model=OpenOut)
async def open_game(
    game_id: uuid.UUID,
    registry: RegistryDep,
    session_factory: SessionFactoryDep,
) -> OpenOut:
    async with session_factory() as session:
        game = await game_repo.get_game(session, game_id)
    if game is None:
        raise game_not_found()
    try:
        handle, urls = await registry.open_game(game_id)
    except SandboxUnavailable:
        raise sandbox_unavailable() from None
    except LockBusy:
        raise workspace_busy() from None
    except Exception:
        logger.exception("打开游戏失败 game=%s", game_id)
        raise sandbox_unavailable() from None
    return OpenOut(
        game_id=game_id,
        sandbox_id=handle.sandbox_id,
        game_url=urls.game_url,
        novnc_url=urls.novnc_url,
    )


@router.post("/{game_id}/touch", response_model=TouchOut)
async def touch_game(
    game_id: uuid.UUID,
    registry: RegistryDep,
    session_factory: SessionFactoryDep,
) -> TouchOut:
    async with session_factory() as session:
        game = await game_repo.get_game(session, game_id)
    if game is None:
        raise game_not_found()
    try:
        handle = await registry.touch(game_id)
    except SandboxUnavailable:
        raise sandbox_unavailable() from None
    except LockBusy:
        raise workspace_busy() from None
    return TouchOut(game_id=game_id, sandbox_id=handle.sandbox_id)


@router.post("/{game_id}/archive", response_model=ArchiveOut)
async def archive_game(
    game_id: uuid.UUID,
    registry: RegistryDep,
    session_factory: SessionFactoryDep,
    force: bool = False,
) -> ArchiveOut:
    async with session_factory() as session:
        game = await game_repo.get_game(session, game_id)
    if game is None:
        raise game_not_found()
    try:
        result = await registry.archive(game_id, force=force)
    except SandboxUnavailable:
        raise sandbox_unavailable() from None
    except LockBusy:
        raise workspace_busy() from None
    return ArchiveOut(**result)


@router.post("/{game_id}/chat", response_model=ChatOut)
async def chat_game(
    game_id: uuid.UUID,
    payload: ChatIn,
    registry: RegistryDep,
    factory: AgentFactoryDep,
    session_factory: SessionFactoryDep,
) -> ChatOut:
    async with session_factory() as session:
        game = await game_repo.get_game(session, game_id)
    if game is None:
        raise game_not_found()
    try:
        output = await agent_service.chat(factory, registry, game_id, payload.prompt)
    except SandboxUnavailable:
        raise sandbox_unavailable() from None
    except LockBusy:
        raise workspace_busy() from None
    except HTTPException:
        raise
    except Exception:
        logger.exception("Agent run 失败 game=%s", game_id)
        raise sandbox_unavailable() from None
    return ChatOut(output=output)


@router.delete("/{game_id}", status_code=204)
async def delete_game(
    game_id: uuid.UUID,
    registry: RegistryDep,
    session_factory: SessionFactoryDep,
) -> None:
    async with session_factory() as session:
        game = await game_repo.get_game(session, game_id)
    if game is None:
        raise game_not_found()
    try:
        await registry.delete_game(game_id)
    except LockBusy:
        raise workspace_busy() from None

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.runtime.agent.factory import AgentFactory
from app.runtime.sandboxes.registry import SandboxRegistry
from app.runtime.sandboxes.snapshots import SnapshotStore


def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    return request.app.state.session_factory


def get_registry(request: Request) -> SandboxRegistry:
    return request.app.state.registry


def get_snapshots(request: Request) -> SnapshotStore:
    return request.app.state.snapshots


def get_agent_factory(request: Request) -> AgentFactory:
    return request.app.state.agent_factory


SessionFactoryDep = Annotated[
    async_sessionmaker[AsyncSession], Depends(get_session_factory)
]
RegistryDep = Annotated[SandboxRegistry, Depends(get_registry)]
SnapshotsDep = Annotated[SnapshotStore, Depends(get_snapshots)]
AgentFactoryDep = Annotated[AgentFactory, Depends(get_agent_factory)]

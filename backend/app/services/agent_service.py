from __future__ import annotations

import uuid

from app.config import settings
from app.runtime.agent.factory import AgentFactory
from app.runtime.sandboxes.heartbeat import keep_sandbox_alive
from app.runtime.sandboxes.registry import SandboxRegistry


async def chat(
    factory: AgentFactory,
    registry: SandboxRegistry,
    game_id: uuid.UUID,
    prompt: str,
) -> str:
    handle = await registry.ensure(game_id)
    agent = factory.build()
    async with keep_sandbox_alive(
        registry, game_id, settings.sandbox_heartbeat_seconds
    ):
        result = await agent.run(prompt, workspace=handle.ref)
    return result.output

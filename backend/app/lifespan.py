from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import logfire
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from app.config import settings
from app.database import dispose_engine, session_factory
from app.runtime.agent.factory import AgentFactory
from app.runtime.agent.model import build_model
from app.runtime.sandboxes.registry import SandboxRegistry, create_e2b_client
from app.runtime.sandboxes.scan import run_archive_scan
from app.runtime.sandboxes.snapshots import SnapshotStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    if settings.logfire_token:
        logfire.configure(
            token=settings.logfire_token,
            environment=settings.logfire_environment,
        )
    else:
        logfire.configure(
            send_to_logfire=False,
            environment=settings.logfire_environment,
        )
    logfire.instrument_pydantic_ai()

    client = create_e2b_client()
    snapshots = SnapshotStore()
    registry = SandboxRegistry(client, snapshots, session_factory)
    agent_factory = AgentFactory(
        build_model(),
        e2b_client=client,
        template=settings.e2b_template or None,
        sandbox_timeout=settings.sandbox_timeout,
    )

    app.state.session_factory = session_factory
    app.state.client = client
    app.state.snapshots = snapshots
    app.state.registry = registry
    app.state.agent_factory = agent_factory

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        run_archive_scan,
        "interval",
        seconds=settings.sandbox_archive_scan_seconds,
        args=[registry],
        id="sandbox-archive",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
        replace_existing=True,
        next_run_time=datetime.now(UTC),
    )
    scheduler.start()
    logger.info("沙箱归档任务已启动，间隔 %s 秒", settings.sandbox_archive_scan_seconds)

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        await dispose_engine()

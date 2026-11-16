from __future__ import annotations

from fastapi import APIRouter

from app.dependencies import RegistryDep, SnapshotsDep
from app.runtime.sandboxes.scan import run_archive_scan

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


@router.post("/archive-scan")
async def archive_scan(registry: RegistryDep) -> dict[str, int]:
    return await run_archive_scan(registry)


@router.get("/oss")
async def oss_info(snapshots: SnapshotsDep) -> dict[str, str]:
    return await snapshots.describe()

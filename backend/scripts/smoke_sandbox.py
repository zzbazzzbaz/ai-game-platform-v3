from __future__ import annotations

import sys

import httpx

from app.runtime.sandboxes.registry import create_e2b_client

BASE = "http://127.0.0.1:8001"


def main() -> None:
    game_id: str | None = None
    client = create_e2b_client()
    api = httpx.Client(base_url=BASE, timeout=120)
    try:
        response = api.post("/api/games", json={"name": "sandbox-smoke"})
        response.raise_for_status()
        game_id = response.json()["id"]
        print("game", game_id)

        response = api.post(f"/api/games/{game_id}/open")
        response.raise_for_status()
        opened = response.json()
        sandbox_id = opened["sandbox_id"]
        print("open", sandbox_id)
        print("game_url", opened["game_url"])

        sandbox = client.AsyncSandbox
        # 用同步 SDK 写文件，验证工作区在真实沙盒内。
        async def write() -> None:
            handle = await sandbox.connect(sandbox_id, timeout=600)
            await handle.files.write("/home/user/workspace/smoke.txt", b"hello-archive")

        import asyncio

        asyncio.run(write())
        print("wrote smoke.txt")

        response = api.post(f"/api/games/{game_id}/archive", params={"force": "true"})
        response.raise_for_status()
        print("archive", response.json())

        status = api.get(f"/api/games/{game_id}").json()
        print("status after archive", status)
        assert status["lifecycle_state"] == "archived", status
        assert status["sandbox_id"] is None, status
        assert status["snapshot_key"], status

        response = api.post(f"/api/games/{game_id}/open")
        response.raise_for_status()
        reopened = response.json()
        print("reopen", reopened["sandbox_id"])
        assert reopened["sandbox_id"] != sandbox_id

        async def read() -> str:
            handle = await sandbox.connect(reopened["sandbox_id"], timeout=600)
            data = await handle.files.read("/home/user/workspace/smoke.txt", format="text")
            return str(data)

        content = asyncio.run(read())
        print("restored smoke.txt", content)
        assert content == "hello-archive", content
        print("SMOKE OK")
    finally:
        if game_id:
            try:
                api.delete(f"/api/games/{game_id}")
                print("deleted game", game_id)
            except Exception as error:  # noqa: BLE001
                print("cleanup failed", error, file=sys.stderr)


if __name__ == "__main__":
    main()

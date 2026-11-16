from __future__ import annotations

import sys

import httpx

BASE = "http://127.0.0.1:8001"


def main() -> None:
    game_id: str | None = None
    api = httpx.Client(base_url=BASE, timeout=600)
    try:
        response = api.post("/api/games", json={"name": "agent-smoke"})
        response.raise_for_status()
        game_id = response.json()["id"]
        print("game", game_id)

        response = api.post(
            f"/api/games/{game_id}/chat",
            json={
                "prompt": (
                    "先列出 /home/user/workspace 下的文件，然后读取 package.json，"
                    "告诉我 name 字段。不要修改任何文件。"
                )
            },
        )
        response.raise_for_status()
        print(response.json()["output"])
        print("AGENT SMOKE OK")
    finally:
        if game_id:
            try:
                api.delete(f"/api/games/{game_id}")
                print("deleted game", game_id)
            except Exception as error:  # noqa: BLE001
                print("cleanup failed", error, file=sys.stderr)


if __name__ == "__main__":
    main()

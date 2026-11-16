from __future__ import annotations

import os
import time
from datetime import UTC, datetime

from e2b import Template

from app.config import settings


def main() -> None:
    image = os.environ.get("SANDBOX_IMAGE", "").strip()
    if not image:
        raise SystemExit("请设置 SANDBOX_IMAGE，例如 docker.io/15688463267/ai-game-platform-sandbox:v1")
    name = os.environ.get("SANDBOX_TEMPLATE_NAME", "").strip()
    if not name:
        name = f"ai-game-platform-sandbox-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

    print(f"构建模板：{name}")
    print(f"镜像：{image}")
    print("规格：1 vCPU / 1024 MB")

    builder = (
        Template()
        .from_image(image)
        .set_start_cmd(
            "/bin/bash -lc /opt/sandbox/start-services.sh",
            "/bin/bash -lc /opt/sandbox/ready.sh",
        )
    )

    last = 0.0

    def on_log(entry):  # type: ignore[no-untyped-def]
        nonlocal last
        now = time.monotonic()
        if now - last < 0.5:
            return
        last = now
        message = getattr(entry, "message", str(entry))
        print(message)

    info = Template.build(
        builder,
        name=name,
        cpu_count=1,
        memory_mb=1024,
        api_key=settings.e2b_api_key,
        api_url=settings.e2b_api_url,
        domain=settings.e2b_domain,
        on_build_logs=on_log,
    )
    print("模板构建完成")
    print(f"TEMPLATE_ID={info.template_id}")
    print(f"BUILD_ID={info.build_id}")
    print("把 TEMPLATE_ID 写入 .env 的 E2B_TEMPLATE。")


if __name__ == "__main__":
    main()

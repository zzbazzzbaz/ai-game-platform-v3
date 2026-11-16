from __future__ import annotations

import e2b
from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai_harness.coder import Coder
from pydantic_ai_harness.e2b_sandbox import E2BSandbox

INSTRUCTIONS = """
你是 AI 游戏平台的全栈游戏开发助手。

工作区固定为 /home/user/workspace，里面是一个 Phaser 4 + Express 的游戏工程：
- src/ 和 shared/ 是你要修改的游戏代码
- server/index.js 是平台维护文件，不要修改
- 依赖已经安装在 /opt/game-template/node_modules，工作区通过 node_modules 软链接使用

工作方式：
- 先读代码再修改，改动尽量小
- 修改后用 npm run build 或 curl 本地服务验证
- 不要删除 .runtime、node_modules 软链接和平台文件
- 不要执行破坏性命令
""".strip()


class AgentFactory:
    def __init__(
        self,
        model: Model,
        *,
        e2b_client: e2b.E2B,
        template: str | None,
        sandbox_timeout: int,
    ) -> None:
        self._model = model
        self._e2b_client = e2b_client
        self._template = template
        self._sandbox_timeout = sandbox_timeout

    def build(self) -> Agent[None, str]:
        return Agent(
            self._model,
            output_type=str,
            instructions=INSTRUCTIONS,
            capabilities=[
                E2BSandbox(
                    client=self._e2b_client,
                    template=self._template,
                    sandbox_timeout=self._sandbox_timeout,
                    working_dir="/home/user/workspace",
                ),
                Coder(),
            ],
        )

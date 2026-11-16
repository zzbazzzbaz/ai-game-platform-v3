from __future__ import annotations

import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def game_not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="游戏不存在。")


def sandbox_unavailable() -> HTTPException:
    return HTTPException(status_code=503, detail="沙盒暂时不可用，请稍后重试。")


def workspace_busy() -> HTTPException:
    return HTTPException(status_code=409, detail="工作区正在处理中，请稍后重试。")

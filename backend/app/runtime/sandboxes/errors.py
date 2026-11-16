from __future__ import annotations


class SandboxUnavailable(Exception):
    """沙盒不可用；接口层统一返回 503，细节只写日志。"""


class LockBusy(Exception):
    """工作区锁被其他操作占用。"""

# AI 游戏平台 v3

按 game 管理阿里云 Agent Sandbox 的沙盒生命周期：创建、续签、暂停、归档到阿里云 OSS、从 OSS 恢复。

## 结构

```text
backend/
  app/
    endpoints/           games、maintenance
    repositories/        games、sandbox_sessions
    runtime/
      agent/             DeepSeek + Pydantic AI
      sandboxes/         注册表、锁、心跳、OSS 快照、归档扫描
  migrations/            Alembic
  scripts/               模板构建、smoke、OSS STS 刷新
sandbox/
  Dockerfile             基于阿里云官方 MicroVM base
  start-services.sh      Xvfb / x11vnc / noVNC / Chromium
  prepare-workspace.sh   工作区播种与 node_modules 软链
  game-template/         Phaser 4 + Express 游戏模板
  assets/skills/         Phaser 技能库
.github/workflows/       Docker Hub 镜像构建
```

## 沙盒内路径

| 路径 | 用途 |
| --- | --- |
| `/home/user/workspace` | 游戏工作区，归档对象 |
| `/home/user/input` | 素材目录，不进入快照 |
| `/opt/game-template` | 镜像内游戏模板与依赖 |
| `/opt/skills` | Phaser 技能库 |
| `3000` | 游戏 HTTP 服务 |
| `9000` | noVNC 预览 |
| `49983` | envd（平台） |

## 本地启动

```bash
cp .env.example .env
# 填写 DEEPSEEK_API_KEY、E2B_API_KEY、OSS 凭证
make up
make install
make migrate
make run-api
```

后端监听 `http://127.0.0.1:8001`。

## 沙盒镜像

GitHub Actions 在 tag `sandbox-v*` 或手动触发时构建 `linux/amd64` 镜像并推送到 Docker Hub：

```text
docker.io/<DOCKERHUB_USERNAME>/ai-game-platform-sandbox:<tag>
```

需要在 GitHub 仓库配置：

```text
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
```

本地构建：

```bash
make build-image
```

## 阿里云模板

Docker Hub 镜像是构建产物，由 GitHub Actions 推送。阿里云第二代运行时（支持暂停/恢复）的自定义模板只接受官方公共镜像或 ACR EE，不能直接把 Docker Hub 镜像作为模板源；因此模板使用官方 `runtime-v2/base`，在构建步骤中安装 Playwright、noVNC 和游戏模板。

前置条件：

- 本机已登录阿里云 CLI（`aliyun configure list` 显示有效 profile）
- `.env` 已填写 `FCSANDBOX_TEAM_ID` 和 `ALIYUN_REGION`
- OSS 凭证可写 `ai-game-platform-oss`

执行：

```bash
make template
```

脚本会：

1. 把 `sandbox/game-template`、`sandbox/assets/skills`、`sandbox/*.sh` 上传到 OSS
2. 调用 `aliyun fcsandbox CreateTemplate`，规格 1 vCPU / 1024 MB / 15 GiB
3. 轮询到 `ready`
4. 输出 `TEMPLATE_ID`

把输出的 `TEMPLATE_ID` 写入 `.env`：

```env
E2B_TEMPLATE=<template_id>
```

一代 runtime 不支持暂停/恢复，因此不作为模板方案。Docker Hub 镜像保留为可复现的构建产物，也方便后续迁移到 ACR EE。

## OSS

Bucket：`ai-game-platform-oss`，地域 `cn-hangzhou`，本地冗余。

创建：

```bash
aliyun oss mb oss://ai-game-platform-oss --redundancy-type LRS
```

如果使用阿里云 CLI 的 OAuth/STS 凭证，先刷新 `.env`：

```bash
cd backend
uv run python scripts/refresh_oss_token.py
```

当前 `.env` 使用的是 CLI OAuth 的临时 STS 凭证，过期后重新执行上面的命令并重启后端；也可以直接在 `.env` 填永久 AK/SK，并清空 `OSS_SECURITY_TOKEN`。本机访问 OSS 需要代理时设置 `OSS_PROXY`，生产环境留空。

快照路径：

```text
ai-game-platform/games/<game_id>/workspace/<timestamp>.tar.gz
```

## 生命周期

```text
最后一次 envd 操作
  → 600 秒无操作，阿里云暂停
  → 暂停满 2 小时，APScheduler 扫描
  → connect 恢复、停游戏服务、tar、上传 OSS、kill
  → 下次 open：创建新沙盒、从 OSS 下载解包、起游戏服务、connect(600)
```

- `SANDBOX_TIMEOUT=600`：创建和每次 `connect` 都续到 600 秒。
- `SANDBOX_HEARTBEAT_SECONDS=240`：agent run 期间心跳，避免长思考/长命令中途暂停。
- `SANDBOX_ARCHIVE_AFTER_SECONDS=7200`：暂停满 2 小时归档。
- `SANDBOX_ARCHIVE_SCAN_SECONDS=300`：归档扫描间隔。

## API

```bash
# 创建游戏
curl -X POST http://127.0.0.1:8001/api/games -H 'content-type: application/json' \
  -d '{"name":"demo"}'

# 打开沙盒（创建/恢复 + 启动游戏服务 + 返回预览地址）
curl -X POST http://127.0.0.1:8001/api/games/<game_id>/open

# 续签（预览页心跳）
curl -X POST http://127.0.0.1:8001/api/games/<game_id>/touch

# 查看状态
curl http://127.0.0.1:8001/api/games/<game_id>

# 手动归档（force=true 会先暂停再归档，便于测试）
curl -X POST 'http://127.0.0.1:8001/api/games/<game_id>/archive?force=true'

# Agent
curl -X POST http://127.0.0.1:8001/api/games/<game_id>/chat \
  -H 'content-type: application/json' \
  -d '{"prompt":"列出工作区文件"}'

# 触发一次归档扫描
curl -X POST http://127.0.0.1:8001/api/maintenance/archive-scan
```

## 验证

```bash
# 真实沙盒：创建 → 写文件 → 归档 → 恢复 → 校验文件
make smoke

# 真实 DeepSeek + 真实沙盒
make agent-smoke
```

# syntax=docker/dockerfile:1.7
# 阿里云 Agent Sandbox 自定义镜像：在官方 MicroVM base 上叠加游戏运行环境。
# 1C1G 运行时请使用 ai-game-platform-sandbox 模板；镜像本身不限制规格。
FROM fc-e2b-registry.cn-hangzhou.cr.aliyuncs.com/runtime-v2/base:v0.0.53

USER root

ARG NPM_REGISTRY=https://registry.npmjs.org
ARG PLAYWRIGHT_VERSION=1.60.0

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    DISPLAY=:0 \
    PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright \
    PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# 浏览器栈 + 基础工具。novnc/websockify 提供 9000 端口的预览页面。
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl git less procps psmisc tar unzip xz-utils \
      xvfb x11vnc novnc websockify \
      fonts-noto-cjk fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Chromium 只装一份，Node 与 Playwright 共用。
RUN npm config set registry "${NPM_REGISTRY}" \
    && npm install -g playwright@${PLAYWRIGHT_VERSION} \
    && playwright install --with-deps chromium \
    && npm cache clean --force \
    && rm -rf /var/lib/apt/lists/*

# 游戏模板依赖烘焙进镜像，运行时工作区只软链 node_modules，不把依赖放进 OSS。
COPY game-template/ /opt/game-template/
RUN cd /opt/game-template \
    && npm ci --no-audit --no-fund \
    && npm cache clean --force

COPY assets/skills/ /opt/skills/

COPY start-services.sh prepare-workspace.sh browser-kiosk.sh ready.sh /opt/sandbox/
RUN chmod +x /opt/sandbox/*.sh \
    && mkdir -p /home/user/workspace /home/user/input /home/user/.cache \
    && chown -R user:user /home/user/workspace /home/user/input /home/user/.cache \
    && ln -sfn /opt/ms-playwright /home/user/.cache/ms-playwright

EXPOSE 3000 9000 49983

# 不覆盖官方 ENTRYPOINT：envd / gateway 由平台启动。

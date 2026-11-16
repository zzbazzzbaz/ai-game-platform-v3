.PHONY: up down install migrate run-api check build-image push-image template smoke agent-smoke

up:
	docker compose up -d --wait

down:
	docker compose down

install:
	cd backend && uv sync

migrate:
	cd backend && uv run alembic upgrade head

run-api:
	cd backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8001

check:
	cd backend && uv run ruff check
	cd backend && uv run ty check

build-image:
	docker buildx build --platform linux/amd64 -f sandbox/Dockerfile -t $${DOCKER_IMAGE:-ai-game-platform-sandbox:local} sandbox

push-image:
	docker buildx build --platform linux/amd64 --push -f sandbox/Dockerfile -t $${DOCKER_IMAGE:?set DOCKER_IMAGE} sandbox

template:
	cd backend && uv run python scripts/create_template.py

smoke:
	cd backend && uv run python scripts/smoke_sandbox.py

agent-smoke:
	cd backend && uv run python scripts/smoke_agent.py

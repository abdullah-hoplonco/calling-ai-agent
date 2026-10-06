# Omar's voice worker, for LiveKit Cloud agent hosting (`lk agent deploy`).
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY core core
COPY voice voice
COPY .scratch/calling-agent/assets/agency-knowledge.md assets/agency-knowledge.md
ENV KNOWLEDGE_PATH=/app/assets/agency-knowledge.md

RUN uv sync --frozen --no-dev
RUN uv run python -m livekit.agents download-files

CMD ["uv", "run", "--no-dev", "omar-agent", "start"]

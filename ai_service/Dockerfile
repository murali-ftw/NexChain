# P2.5/P2.10 — FastAPI AI service. Build context MUST be the repo root
# (docker-compose.yml sets context: . / dockerfile: ai_service/Dockerfile)
# because this service imports the sibling `ai` package (LangGraph pipeline)
# directly, not just its own `ai_service` package.
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ai ai
COPY ai_service ai_service

ENV PYTHONPATH=/app
# ai/chroma_db is gitignored (local dev artifact) and excluded from this
# build's context (.dockerignore) — without this, the image ships with an
# empty knowledge base and every KB-sourced answer silently comes back with
# zero citations. Baked in at build time since ai/knowledge_base/*.md is
# static, versioned content, not something that changes per-deploy.
RUN python -m ai.rag.ingest

EXPOSE 8001
# httpx is already a dependency (requirements.txt) — no extra package needed
# just to probe the service's own /health endpoint.
HEALTHCHECK --interval=5s --timeout=3s --start-period=15s --retries=5 \
    CMD python -c "import httpx; httpx.get('http://localhost:8001/health').raise_for_status()" || exit 1
CMD ["uvicorn", "ai_service.main:app", "--host", "0.0.0.0", "--port", "8001"]

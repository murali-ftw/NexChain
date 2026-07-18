# P2.7/P2.8 — MCP tool server. Build context MUST be the repo root
# (docker-compose.yml sets context: . / dockerfile: mcp_server/Dockerfile)
# because this service imports the sibling `ai` and `ai_service` packages
# (ai_service/tools/* is the actual tool-execution code — see server.py's
# module docstring: "the same code path is exercised whether you go through
# MCP or import the tool layer directly").
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ai ai
COPY ai_service ai_service
COPY mcp_server mcp_server

ENV PYTHONPATH=/app
# Containerized (network) mode — the CLI default is stdio, meant for a
# locally-spawned MCP client, not a service other containers connect to.
ENV MCP_TRANSPORT=streamable-http
# FastMCP's own default (127.0.0.1) is unreachable through Docker's port
# mapping, which forwards to the container's external interface, not its
# loopback (see server.py's MCP_HOST comment).
ENV MCP_HOST=0.0.0.0
EXPOSE 8002
CMD ["python", "-m", "mcp_server.server"]

# P2.4 — mock ERP/shipment/inventory APIs. Build context MUST be the repo
# root (docker-compose.yml sets context: . / dockerfile: mock_apis/Dockerfile)
# because this service imports the sibling `ai` package (ai.contracts, for
# the OrderStatus/ShipmentStatus/InventoryRecord response shapes).
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ai ai
COPY mock_apis mock_apis

ENV PYTHONPATH=/app
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=5 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1
CMD ["uvicorn", "mock_apis.main:app", "--host", "0.0.0.0", "--port", "8000"]

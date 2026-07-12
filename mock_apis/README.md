# Mock Enterprise APIs (P2.4, Day 4)

Simulates the three external operational systems the AI layer will call —
ERP, shipment tracking (TMS/carrier), and inventory (WMS). This is **not**
the FastAPI AI service; that's P2.5 (Day 5), a separate app on its own port.

## Endpoints

Paths are fixed by `docs/problem_statement.md` §12 and
`docs/03_implementation_plan.md` Phase 3.

| Endpoint | Backs MCP tool (P2.8) | Response model |
|---|---|---|
| `GET /api/order/{orderNumber}` | `get_order_status` | `OrderStatus` |
| `GET /api/shipment/status/{trackingNumber}` | `get_shipment_status` | `ShipmentStatus` |
| `GET /api/inventory/{sku}` | `get_inventory` | `InventoryRecord` |
| `GET /health` | — | `{status, service}` |

Response bodies are exactly the frozen models in `ai/contracts.py`, imported
directly rather than re-declared — the P2.8 MCP tools are then thin
passthroughs instead of another layer that can drift from the contract.

Unknown order / tracking number / SKU returns a clean `404` with a
`{"detail": "..."}` body; an unreachable database returns `503`. The API
Status Agent must handle non-200s gracefully (tech-req §7), so those paths
are part of the contract, not an afterthought.

## Design decision: reads the seeded database, no hardcoded fixtures

The P2.4 spec requires responses to be "deterministic per seed data". Rather
than keep a second copy of the scenario data in Python (which would drift from
`db/seed_data.sql` the moment either changed), these endpoints read the same
seeded Postgres the rest of the system uses.

They connect as **`copilot_readonly`** (`db/migrations/002_roles.sh`), so a
simulated external system physically cannot write to the system of record —
Postgres refuses it, not just application code. `test_mock_apis.py` asserts
that.

## Running

```bash
cp mock_apis/.env.example mock_apis/.env    # set the copilot_readonly password
psql -v ON_ERROR_STOP=1 -d nexchain -f db/seed_data.sql   # if not already seeded

.venv/bin/uvicorn mock_apis.main:app --port 8000 --reload
# interactive docs: http://localhost:8000/docs
```

## Completion gate

"All endpoints return correct responses for predefined scenarios"
(`docs/team_plan.md` P2.4):

```bash
.venv/bin/python -m pytest mock_apis/ -v
```

17 tests, covering the flagship customs-hold scenario (`SO-45892` /
`TRK-45892-1`), on-time, cancelled, carrier-delay, warehouse-delay, and
inventory-shortage cases, plus the 404 paths and conformance to the frozen
response shapes. These are the same scenarios `db/verify_scenarios.sql`
proves at the SQL level; this suite proves they survive the HTTP boundary.

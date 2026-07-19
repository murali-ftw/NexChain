"""Day 12 release-hardening: a lightweight concurrency/load probe for
POST /api/chat end-to-end (Angular's real HTTP entry point -> Spring Boot ->
FastAPI -> LangGraph -> MCP -> Postgres/mock_apis).

Not a correctness suite — ApplicationSmokeTests already covers concurrent
history/audit writes for correctness (backend-api/src/test/java/.../
ApplicationSmokeTests.java). This is for latency/error-rate under concurrent
load, the thing Day 12's "Performance Testing" asks for and nothing else in
the repo measures. Stdlib-only (urllib + concurrent.futures) so it needs
nothing beyond the interpreter itself.

Run against a live stack (docker compose up, or backend-api + ai_service +
mcp_server + mock_apis + Postgres running locally):

    python scripts/load_test.py
    python scripts/load_test.py --base-url http://localhost:8080 --concurrency 20 --requests 100
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

QUERIES = [
    "Where is customer order SO-45892? Why is it delayed and what action should we take?",
    "Show delayed shipments from Chennai.",
    "Which orders violate SLA?",
    "What inventory requires replenishment?",
    "What is our SLA policy for customs holds?",
]


@dataclass
class Result:
    status: int | None
    latency_s: float
    error: str | None = None


def _post_json(url: str, body: dict, token: str | None = None, timeout: float = 60.0) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, {}


def login(base_url: str, email: str, password: str) -> str:
    status, body = _post_json(
        f"{base_url}/api/auth/login", {"email": email, "password": password}
    )
    if status != 200:
        raise SystemExit(f"login failed: HTTP {status}")
    return body["accessToken"]


def one_chat_call(base_url: str, token: str, query: str) -> Result:
    started = time.perf_counter()
    try:
        status, body = _post_json(f"{base_url}/api/chat", {"query": query}, token=token)
    except Exception as exc:  # noqa: BLE001 - report every failure mode, don't crash the run
        return Result(status=None, latency_s=time.perf_counter() - started, error=str(exc))
    elapsed = time.perf_counter() - started
    if status != 200:
        return Result(status=status, latency_s=elapsed, error=json.dumps(body)[:200])
    return Result(status=status, latency_s=elapsed)


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(int(len(ordered) * pct), len(ordered) - 1)
    return ordered[index]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--requests", type=int, default=50)
    parser.add_argument("--email", default="user@example.com")
    parser.add_argument("--password", default="password")
    args = parser.parse_args()

    token = login(args.base_url, args.email, args.password)
    print(f"Logged in. Firing {args.requests} requests at concurrency {args.concurrency}...")

    results: list[Result] = []
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [
            pool.submit(one_chat_call, args.base_url, token, QUERIES[i % len(QUERIES)])
            for i in range(args.requests)
        ]
        for future in as_completed(futures):
            results.append(future.result())
    wall_time = time.perf_counter() - started

    ok = [r for r in results if r.status == 200]
    failed = [r for r in results if r.status != 200]
    latencies = [r.latency_s for r in ok]

    print()
    print(f"Total: {len(results)}  OK: {len(ok)}  Failed: {len(failed)}")
    print(f"Wall time: {wall_time:.2f}s  Throughput: {len(results) / wall_time:.2f} req/s")
    if latencies:
        print(
            f"Latency (OK only) — min: {min(latencies):.2f}s  "
            f"p50: {percentile(latencies, 0.50):.2f}s  "
            f"p95: {percentile(latencies, 0.95):.2f}s  "
            f"max: {max(latencies):.2f}s"
        )
    if failed:
        print("\nFailures (first 5):")
        for r in failed[:5]:
            print(f"  status={r.status} error={r.error}")


if __name__ == "__main__":
    main()

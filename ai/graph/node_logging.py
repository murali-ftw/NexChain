"""Start/complete/failure timing for every LangGraph node.

The graph (ai/graph/graph.py) is the one place every agent execution —
knowledge base, text-to-sql, api-status, business-rule, final-response,
error-handler, and the intent-classifier supervisor — funnels through, so
wrapping node functions here gives every agent invocation the same
start/complete/duration/outcome logging without copy-pasting it into each
node body (and without logging inside per-node internal loops, which would
violate the "no noisy per-loop logs" rule this stack otherwise holds to).
"""

from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable

from ai.graph.state import CoPilotState, CoPilotStateUpdate

logger = logging.getLogger(__name__)

NodeFn = Callable[[CoPilotState], CoPilotStateUpdate]


def log_node_execution(node_name: str) -> Callable[[NodeFn], NodeFn]:
    """Wrap a LangGraph node function with start/complete/failure logging.

    A per-branch "error" key in the node's return value (the established
    degrade-in-place convention — see ai/graph/nodes.py) is logged as a WARN
    "degraded" outcome, not a failure: the node itself didn't raise, it
    correctly reported a tool/LLM failure for retry.py/routing.py to act on.
    An actual exception escaping the node is the only ERROR-level case, since
    every node in this graph is meant to catch and record failures, not raise.
    """

    def decorator(fn: NodeFn) -> NodeFn:
        @functools.wraps(fn)
        def wrapper(state: CoPilotState) -> CoPilotStateUpdate:
            session_id = state.get("session_id", "-")
            logger.info(
                "agent_node node=%s event=start session_id=%s", node_name, session_id
            )
            started = time.perf_counter()
            try:
                result = fn(state)
            except Exception:
                duration_ms = (time.perf_counter() - started) * 1000
                logger.exception(
                    "agent_node node=%s event=failed session_id=%s duration_ms=%.1f",
                    node_name,
                    session_id,
                    duration_ms,
                )
                raise
            duration_ms = (time.perf_counter() - started) * 1000
            error = result.get("error") if isinstance(result, dict) else None
            if error:
                logger.warning(
                    "agent_node node=%s event=completed session_id=%s duration_ms=%.1f "
                    "outcome=degraded error=%s",
                    node_name,
                    session_id,
                    duration_ms,
                    error,
                )
            else:
                logger.info(
                    "agent_node node=%s event=completed session_id=%s duration_ms=%.1f outcome=success",
                    node_name,
                    session_id,
                    duration_ms,
                )
            return result

        return wrapper

    return decorator

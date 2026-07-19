"""P3.8 graph state — the frozen CoPilotState (ai/contracts.py), unchanged.

Node functions in ai/graph/ read CoPilotState and return CoPilotStateUpdate
(same fields, all optional — the partial-update shape LangGraph actually
merges). No fields are added or renamed here — CoPilotState (P3.1) is the
single source of truth; this module exists only so graph code has one
place to import both from.
"""

from __future__ import annotations

from ai.contracts import CoPilotState, CoPilotStateUpdate

__all__ = ["CoPilotState", "CoPilotStateUpdate"]

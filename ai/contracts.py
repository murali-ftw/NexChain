"""NexChain AI layer — frozen shared contracts (P3.1, End of Day 1).

Interface-only: enums, typed models, and constants that Person 1 and
Person 2 depend on. No agent logic, no RAG, no SQL generation, no
LangGraph graph, no MCP client code.

Source of truth: docs/02_technical_requirements.md,
docs/06_backend_schema.md, docs/team_plan.md, docs/problem_statement.md.
Where this file and those docs disagree, the docs win — fix this file.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import TypedDict

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 1. Routing categories — team_plan.md P3.7
# ---------------------------------------------------------------------------


class RoutingCategory(str, Enum):
    """The four categories the LangGraph supervisor branches on. # team_plan P3.7"""

    KNOWLEDGE_QUERY = "KNOWLEDGE_QUERY"
    DATABASE_QUERY = "DATABASE_QUERY"
    API_QUERY = "API_QUERY"
    MULTI_TOOL_QUERY = "MULTI_TOOL_QUERY"


# ---------------------------------------------------------------------------
# 2. Business intents — tech-req §3.1 examples + team_plan P3.7
# ---------------------------------------------------------------------------


class BusinessIntent(str, Enum):
    """Finer-grained intent used in CoPilotState.intent and audit_log.detected_intent. # tech-req §3.1"""

    ORDER_STATUS = "order_status"
    SHIPMENT_STATUS = "shipment_status"
    INVENTORY = "inventory"
    SOP_LOOKUP = "sop_lookup"
    SLA_CHECK = "sla_check"
    REPORT = "report"
    DELAY_ANALYSIS = "delay_analysis"


# Maps each business intent to the routing category the supervisor uses
# for single-source dispatch. delay_analysis and sla_check are
# MULTI_TOOL_QUERY because business_rule_agent needs DB + API results
# (tech-req §3.2) plus, for delay questions, KB guidance (problem_statement §6).
# See ai/CONTRACTS.md §2 for the worked reasoning and examples per intent.
INTENT_TO_ROUTING: dict[BusinessIntent, RoutingCategory] = {
    BusinessIntent.SOP_LOOKUP: RoutingCategory.KNOWLEDGE_QUERY,
    BusinessIntent.ORDER_STATUS: RoutingCategory.DATABASE_QUERY,
    BusinessIntent.INVENTORY: RoutingCategory.DATABASE_QUERY,
    BusinessIntent.REPORT: RoutingCategory.DATABASE_QUERY,
    BusinessIntent.SHIPMENT_STATUS: RoutingCategory.API_QUERY,
    BusinessIntent.SLA_CHECK: RoutingCategory.MULTI_TOOL_QUERY,
    BusinessIntent.DELAY_ANALYSIS: RoutingCategory.MULTI_TOOL_QUERY,
}


# ---------------------------------------------------------------------------
# 3. Agent / node names — tech-req §3.2 (exact names, do not rename)
# ---------------------------------------------------------------------------


class AgentNode(str, Enum):
    """The seven LangGraph nodes, all owned by Person 3. # tech-req §3.2"""

    INTENT_CLASSIFIER = "intent_classifier"
    KNOWLEDGE_BASE_AGENT = "knowledge_base_agent"
    TEXT_TO_SQL_AGENT = "text_to_sql_agent"
    API_STATUS_AGENT = "api_status_agent"
    BUSINESS_RULE_AGENT = "business_rule_agent"
    FINAL_RESPONSE_AGENT = "final_response_agent"
    ERROR_HANDLER = "error_handler"


# ---------------------------------------------------------------------------
# 4. LangGraph state — tech-req §3.1 (verbatim shape)
# ---------------------------------------------------------------------------


class CoPilotState(TypedDict):
    """LangGraph graph state. Internal only — never returned directly over the wire. # tech-req §3.1"""

    session_id: str
    user_id: str
    raw_query: str
    intent: str  # primary intent, e.g. "order_status"
    sub_intents: list[str]  # multiple agents may be required
    kb_result: dict | None
    sql_result: dict | None
    api_result: dict | None
    rule_result: dict | None
    retry_count: dict[str, int]
    final_response: str | None
    error: str | None


class CoPilotStateUpdate(TypedDict, total=False):
    """Same fields as CoPilotState, all optional — the shape every LangGraph
    node function actually returns (a partial update the graph merges into
    CoPilotState), as opposed to CoPilotState itself, which types the full
    state read at node entry. Added so node return annotations can be
    precise without weakening CoPilotState's own required-keys guarantee
    for full-state readers (e.g. the initial state built in ai_service/main.py)."""

    session_id: str
    user_id: str
    raw_query: str
    intent: str
    sub_intents: list[str]
    kb_result: dict | None
    sql_result: dict | None
    api_result: dict | None
    rule_result: dict | None
    retry_count: dict[str, int]
    final_response: str | None
    error: str | None


# ---------------------------------------------------------------------------
# 5. MCP tool interface stubs — tech-req §4.1 (exact names, owned by Person 2)
# ---------------------------------------------------------------------------


class KBHit(BaseModel):
    """One result item from kb_search. # tech-req §4.1"""

    content: str
    source_doc: str
    score: float


class DBResult(BaseModel):
    """Result of db_query: pre-validated SELECT executed via MCP. # tech-req §4.1"""

    rows: list[dict]


class OrderStatus(BaseModel):
    """Result of get_order_status. # tech-req §4.1"""

    order_no: str
    status: str
    promised_delivery_date: str | None = None
    revised_delivery_date: str | None = None


class ShipmentStatus(BaseModel):
    """Result of get_shipment_status. # tech-req §4.1"""

    tracking_no: str
    shipment_status: str
    current_location: str | None = None
    delay_reason: str | None = None


class InventoryRecord(BaseModel):
    """Result of get_inventory. # tech-req §4.1"""

    sku: str
    quantity_on_hand: int
    quantity_reserved: int


def kb_search(query: str, top_k: int) -> list[KBHit]:
    """MCP tool stub. Owned by Person 2 via MCP. # tech-req §4.1"""
    raise NotImplementedError("Owned by Person 2 via MCP")


def db_query(sql: str) -> DBResult:
    """MCP tool stub. `sql` must already be validated (see §6 below). Owned by Person 2 via MCP. # tech-req §4.1"""
    raise NotImplementedError("Owned by Person 2 via MCP")


def get_order_status(order_no: str) -> OrderStatus:
    """MCP tool stub. Owned by Person 2 via MCP. # tech-req §4.1"""
    raise NotImplementedError("Owned by Person 2 via MCP")


def get_shipment_status(tracking_no: str) -> ShipmentStatus:
    """MCP tool stub. Owned by Person 2 via MCP. # tech-req §4.1"""
    raise NotImplementedError("Owned by Person 2 via MCP")


def get_inventory(sku: str) -> InventoryRecord:
    """MCP tool stub. Owned by Person 2 via MCP. # tech-req §4.1"""
    raise NotImplementedError("Owned by Person 2 via MCP")


# ---------------------------------------------------------------------------
# 6. Text-to-SQL constants — tech-req §5 + backend_schema §4
# ---------------------------------------------------------------------------

# Shared contract: Person 2 owns this list and the copilot_readonly role it
# maps to; Person 3 owns the validator enforcing it. Neither may change it
# unilaterally (docs/team_plan.md, "shared contracts may not be changed silently").
SQL_TABLE_ALLOWLIST: frozenset[str] = frozenset(
    {
        "customers",
        "sales_orders",
        "order_items",
        "inventory",
        "warehouse",
        "shipment",
        "invoice",
        "payment",
        "carrier_tracking",
        "sla_rules",
    }
)

SQL_DENIED_KEYWORDS: frozenset[str] = frozenset(
    {
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        # RC stabilization: explicit backstop keywords, on top of the AST-level
        # exp.Select/exp.Insert/exp.Update/exp.Delete/exp.Merge checks in
        # ai/agents/text_to_sql_agent/validator.py — belt-and-suspenders so a
        # future validator change can't silently reopen these by keyword alone.
        "CREATE",
        "GRANT",
        "REVOKE",
        "CALL",
        "COPY",
        "MERGE",
        "VACUUM",
    }
)

SQL_ROW_LIMIT = 200


# ---------------------------------------------------------------------------
# 7. Retry / fallback policy — tech-req §3.4
# ---------------------------------------------------------------------------

MAX_RETRIES_PER_NODE = 1


# ---------------------------------------------------------------------------
# 8. Sources, SLA status, and the wire response schema
# ---------------------------------------------------------------------------


class Source(BaseModel):
    """A citation surfaced to the user, derived from a kb_search KBHit."""

    document_name: str
    snippet: str | None = None
    doc_id: int | None = None
    score: float | None = None


class SLAStatus(str, Enum):
    """Matches backend_schema §6 sla_result wording."""

    ON_TIME = "On Time"
    AT_RISK = "At Risk"
    BREACHED = "Breached"
    NOT_APPLICABLE = "N/A"


class CoPilotResponse(BaseModel):
    """Wire/structured response: FastAPI -> Spring Boot -> Angular (P1.9).

    Proposed clarification (open question, needs P1 + P2 sign-off — see
    ai/CONTRACTS.md §8): CoPilotState.final_response stays a plain
    str | None internally, matching tech-req §3.1. This model is the
    separate structured envelope returned over the wire; answer_text
    mirrors final_response as the prose summary field.
    """

    answer_text: str
    intent: RoutingCategory
    order_status: str | None = None
    shipment_status: str | None = None
    current_location: str | None = None
    delay_reason: str | None = None
    delay_days: int | None = None
    sla_status: SLAStatus
    recommended_actions: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    partial: bool = False  # set when a data source was unavailable after 1 retry (§7)
    error: str | None = None
    # Amended Day 11 (Person 3 decision, ai/CONTRACTS.md §8 changelog): folded in from
    # Person 1's provisional AiQueryResponse subclass (ai_service/schemas.py).
    promised_delivery_date: date | None = None
    revised_delivery_date: date | None = None
    # Amended post-Day-11 audit: audit_log.agents_invoked / generated_sql
    # (backend_schema §2.14) were always empty at record time because nothing
    # upstream of Spring Boot's ChatResponse carried them, even though the
    # graph always knows both. Populated by response_mapper.state_to_fields.
    agents_invoked: list[str] = Field(default_factory=list)
    generated_sql: str | None = None

# Intent Classifier (P3.7, Day 7)

## Status (as of commit)

Live eval: **20/20** questions routed to the correct `RoutingCategory`
(`test_questions.py`) — clears the P3.7 gate (`docs/team_plan.md`,
>= 18/20). 16/20 resolved by the zero-cost rule fast-path; the
remaining 4 (one per category, deliberately ambiguous) correctly fell
through to the LLM fallback, proving that path works too, not just the
rules. Total cost: **4 API calls**. The flagship SO-45892 question
routes to `MULTI_TOOL_QUERY` via the rule fast-path (0 calls).

Classifies a natural-language question into one of the four frozen
`RoutingCategory` values (`ai/contracts.py`). Does **not** build the
LangGraph graph (P3.8) — `classify()` is a standalone function that
decides the route; it doesn't invoke `knowledge_base_agent`,
`text_to_sql_agent`, or `api_status_agent`, and doesn't touch
`CoPilotState`.

## Pipeline

1. **Rule fast-path** (`rules.py`) — deterministic keyword/pattern
   matching against a query, checked in priority order (multi-tool
   signals first, since a query can look single-source while actually
   needing DB+API+KB together). Zero API calls. Returns a
   `BusinessIntent` or `None` (ambiguous → fall through).
2. **LLM fallback** (`prompts.py` + `ai/llm_client.py`) — only called
   when the rules return `None`. Given the 4 category definitions plus
   a 4-shot example set, returns exactly one `RoutingCategory` value
   (validated against the enum before being trusted).
3. **Routing derivation** (`classifier.py`) — the `RoutingCategory` is
   never independently guessed; it's always looked up via the existing
   frozen `INTENT_TO_ROUTING` dict from the resolved `BusinessIntent`,
   so it's structurally impossible to emit a category inconsistent
   with that mapping. Abstains explicitly (`routing_category=None`,
   `error` set) rather than guessing if the LLM call fails or returns
   something outside the enum — same "fail honestly" convention as the
   KB and SQL agents.

## Running the eval (completion gate)

```bash
# from repo root, with deps from requirements.txt installed
python -m ai.agents.intent_classifier.eval
python -m ai.agents.intent_classifier.eval --ids 4,10,14,20   # targeted re-run
```

Gate (`docs/team_plan.md` P3.7): **>= 18 of the 20 curated questions**
must route to the correct `RoutingCategory`. Grades the actual routing
decision, and reports how many questions were resolved by rules
(free) vs the LLM (billed) — the hybrid design's whole point is
keeping that second number small.

## LLM provider

Shared `ai/llm_client.py` (Gemini-only) — same provider/config as the
KB and SQL agents. No second LLM path was added; the fallback reuses
`generate()` directly.

## Files

| File | Responsibility |
|---|---|
| `rules.py` | Zero-cost deterministic keyword/pattern fast-path |
| `prompts.py` | LLM fallback prompt (category definitions + few-shot) |
| `classifier.py` | Orchestration: rules -> LLM fallback -> `IntentResult`, routing always derived via `INTENT_TO_ROUTING` |
| `test_questions.py` | 20 questions, 5 per category, 4 deliberately ambiguous |
| `eval.py` | Runs the question set, reports pass/fail + rules-vs-LLM split |

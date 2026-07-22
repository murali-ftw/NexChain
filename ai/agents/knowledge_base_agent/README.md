# Knowledge Base Agent (P3.4, Day 4)

## Status (as of commit)

Retrieval, context assembly, and source metadata are verified working
across all 13 questions in `eval_questions.py` (correct source
document matched every time, including the flagship customs/HS-code
question). The completion gate — **>=10 questions with a graded,
LLM-generated answer** — is **MET**: 13/13 passed (live run, Day 6)
with `ai/llm_client.py` configured for `LLM_PRIMARY_MODEL=gemini-flash-latest`.
The flagship customs/HS-code answer was independently checked against
`ai/knowledge_base/03_customs_hold_sop.md` and reproduces all 7
resolution steps and every specific fact (escalation timing, default
revised-ETA, notification window) with no hallucination.

Answers natural-language policy questions from `ai/knowledge_base/`,
grounded strictly in retrieved context, with sources preserved. Sits on
top of the P3.3 RAG pipeline (`ai/rag/`). Does **not** build the
LangGraph node or graph (P3.8) — it returns a plain result object a
future node can drop into `CoPilotState.kb_result`.

## Pipeline

1. **Semantic retrieval** (`retrieval.py`) — top-k (default 4, per
   tech-req §6.3) similarity search via `ai/rag/vector_store.search()`.
2. **Context assembly** (`agent.py: assemble_context`) — merges/dedupes
   chunks from the same document, sorts by score, and enforces a
   ~1800-token budget (word-count approximation, same convention as
   `ai/rag/chunker.py`), keeping the highest-scoring documents and
   truncating the last one that would overflow the budget.
3. **Source metadata** — every non-abstained answer carries
   `list[Source]` (`ai/contracts.py`): `document_name`, a `snippet` of
   the cited chunk, and `score`. `doc_id` isn't populated because
   `vector_store.search()` / `KBHit` don't carry it (only `content`,
   `source_doc`, `score`) — it stays `None`, which the `Source` model
   already allows.
4. **Answer generation** (`prompts.py` + `ai/llm_client.py`) — a
   provider-agnostic plain-text prompt instructs the model to answer
   only from the assembled context and to say so plainly if the
   context doesn't support an answer, rather than guessing.

If retrieval returns nothing, the agent **abstains explicitly**
(`NO_EVIDENCE_ANSWER`) with an empty source list instead of calling the
LLM at all — that's the only case an empty source list is allowed; any
other empty-sources result is a bug, not a valid answer.

## Running the eval (completion gate)

```bash
# from repo root, with deps from requirements.txt installed
python -m ai.agents.knowledge_base_agent.eval
```

Gate: **>= 10 of the 13 curated questions** (`eval_questions.py`) must
return a relevant answer with a correctly-matching source. The
flagship question ("...HS code mismatch...") must cite the Customs
Hold SOP.

If retrieval/assembly succeeds for a question but the LLM call fails
(most commonly: no key configured), the eval reports that question as
`SKIPPED` and still prints the retrieval/assembly diagnostics — it
proves the non-LLM half of the pipeline independently of provider
availability.

## LLM provider

`ai/llm_client.py` is Gemini-only (see its module docstring), shared
across Person 3's agents — there is currently no second-provider
fallback; a failed call raises `LLMProviderError` directly. It reads
config from the environment (see `ai/.env.example`):

```
LLM_PRIMARY_PROVIDER=gemini
LLM_PRIMARY_MODEL=
LLM_PRIMARY_API_KEY=
```

Copy `ai/.env.example` to `ai/.env` (gitignored) and fill in real
values to run the eval end-to-end. `LLM_PRIMARY_MODEL` defaults to
`gemini-flash-latest` if left blank — pin it to a dated model instead
once one is chosen for production, since `-latest` aliases can move
model versions out from under the agent. Note this is a different
layer from the LangGraph `MAX_RETRIES_PER_NODE` policy
(`ai/contracts.py`), which retries a whole graph node rather than
swapping LLM backends within one call. No keys are hardcoded anywhere.

## Swap point for Person 2's `kb_search`

`retrieval.py: retrieve()` is the only place that talks to the vector
store. It already returns `list[KBHit]` — the exact shape
`kb_search` is contracted to return
(`docs/02_technical_requirements.md` §4.1,
`ai/contracts.py: KBHit`). When Person 2's MCP `kb_search` tool is
live, replace this function's body with an MCP client call; nothing in
`agent.py`, `prompts.py`, or `eval.py` needs to change.

## Files

| File | Responsibility |
|---|---|
| `retrieval.py` | Thin boundary over `ai/rag/vector_store` — the `kb_search` swap point |
| `prompts.py` | Provider-agnostic grounded-answer prompt + abstention text |
| `agent.py` | Context assembly + the `answer_policy_question()` entrypoint |
| `eval_questions.py` | 13 curated policy questions covering all 12 KB documents |
| `eval.py` | Runs the question set, reports pass/fail against the completion gate |

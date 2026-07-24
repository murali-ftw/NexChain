"""Grounded-answer prompt template for the Knowledge Base Agent.

Provider-agnostic by design: plain text prompt in, plain text answer
out. Gemini and Grok differ in function-calling / structured-output
conventions, so this agent never relies on either — it parses free-form
prose instead of a structured response.
"""

from __future__ import annotations

NO_EVIDENCE_ANSWER = (
    "I cannot find supporting policy for this question in the knowledge base."
)

_SYSTEM_INSTRUCTIONS = """You are the Knowledge Base Agent for NexChain.
Answer the question using ONLY the policy context provided below.

Rules:
- Do not use outside knowledge or make assumptions beyond the context.
- If the context does not contain enough information to answer, say so plainly instead of guessing.
- Be concise and operational: state the relevant rule, threshold, or procedure step directly.
- Do not fabricate document names, numbers, or thresholds that are not present in the context."""


def build_prompt(question: str, context: str) -> str:
    return (
        f"{_SYSTEM_INSTRUCTIONS}\n\n"
        f"--- POLICY CONTEXT ---\n{context}\n--- END CONTEXT ---\n\n"
        f"Question: {question}\n"
        f"Answer:"
    )

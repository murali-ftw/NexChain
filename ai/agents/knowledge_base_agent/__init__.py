"""P3.4 Knowledge Base Agent: retrieval -> context assembly -> sourced,
grounded answer generation. See README.md in this package for usage."""

from ai.agents.knowledge_base_agent.agent import (
    KnowledgeBaseResult,
    answer_policy_question,
)

__all__ = ["KnowledgeBaseResult", "answer_policy_question"]

"""Prompt assembly (SPEC section 9).

Keeps the system prompt and the context-assembly logic in one place,
separate from the pipeline orchestration and the LLM client.
"""

from __future__ import annotations

from app.models.chat import QueryType
from app.models.source import Chunk

SYSTEM_PROMPT = """You are RecordChat, a domain-specific AI assistant for IATA ONE Record.

You help users understand:
- ONE Record concepts
- ONE Record data model
- JSON-LD structures
- API flows
- logistics object relationships
- implementation patterns

Rules:
1. Use the retrieved context as the primary source of truth.
2. If the answer is not supported by the retrieved context, say so clearly.
3. Distinguish official ONE Record concepts from your own implementation suggestions.
4. When generating JSON-LD examples, mark them as illustrative unless directly copied from official documentation.
5. Prefer concise, developer-friendly answers.
6. Always include relevant sources when available.

Structure your answer as:
Answer:
...

Related concepts:
...

Implementation note:
...

Sources:
...
"""

# Extra steering per query type.
_TYPE_HINTS = {
    QueryType.jsonld_generation: (
        "The user wants a JSON-LD example. A structured example is provided "
        "separately by the system; explain its fields rather than re-emitting it."
    ),
    QueryType.relationship_question: (
        "Focus on how the ONE Record entities relate to each other."
    ),
    QueryType.api_question: (
        "Explain the conceptual flow and, when relevant, the endpoint sequence."
    ),
    QueryType.ontology_question: (
        "Focus on ontology structure. Prefer class definitions, subclass "
        "relationships, object properties, domains, and ranges from the "
        "retrieved ontology chunks."
    ),
    QueryType.implementation_question: (
        "Focus on practical implementation guidance. Prefer NE:ONE setup, "
        "deployment, config, and troubleshooting details when they are present "
        "in the retrieved context, and distinguish them from official ONE Record "
        "standard behavior."
    ),
}


def _format_context(chunks: list[Chunk]) -> str:
    blocks = []
    for c in chunks:
        src = c.metadata.source_name
        section = c.metadata.section_title or ""
        header = f"[{src}{' — ' + section if section else ''}]"
        blocks.append(f"{header}\n{c.content}")
    return "\n---\n".join(blocks)


def build_user_prompt(query: str, chunks: list[Chunk], query_type: QueryType) -> str:
    hint = _TYPE_HINTS.get(query_type, "")
    context = _format_context(chunks)
    parts = []
    if hint:
        parts.append(f"GUIDANCE: {hint}")
    parts.append(f"CONTEXT:\n{context}")
    parts.append(f"QUESTION: {query}")
    return "\n\n".join(parts)

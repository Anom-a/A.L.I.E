"""CritiqueEvidenceUseCase — evaluate if retrieved evidence answers a sub-question.

This use case uses an LLM to judge the sufficiency of evidence. It is called
only on the primary evidence retrieved for a sub-question. If the evidence is
empty, it immediately returns an unsatisfied result without calling the LLM.

The LLM is prompted for a structured response, which is rigorously validated
before returning a domain-friendly `CritiqueResult`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from domain.entities.evidence import Evidence
from domain.entities.sub_question import SubQuestion
from domain.ports.llm_port import LLMPort


@dataclass(frozen=True, slots=True)
class CritiqueResult:
    """The structured evaluation of retrieved evidence.

    Attributes:
        satisfied: Whether the evidence sufficiently answers the sub-question.
        reason: An explanation of why the evidence is or is not sufficient.
        missing_aspects: Specific aspects of the question left unanswered.
    """

    satisfied: bool
    reason: str
    missing_aspects: list[str]


class CritiqueError(Exception):
    """Raised when the LLM critique fails or returns malformed output.
    
    A failure to critique is treated distinctly from an unsatisfied result.
    """


# Schema keys
_SATISFIED_KEY = "satisfied"
_REASON_KEY = "reason"
_MISSING_ASPECTS_KEY = "missing_aspects"

#: Framework-agnostic description of the critique response.
CRITIQUE_SCHEMA: Mapping[str, Any] = {
    "title": "evidence_critique",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        _SATISFIED_KEY: {"type": "boolean"},
        _REASON_KEY: {"type": "string"},
        _MISSING_ASPECTS_KEY: {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [_SATISFIED_KEY, _REASON_KEY, _MISSING_ASPECTS_KEY],
}

_PROMPT_TEMPLATE = """You are an evidence critic. Your task is to evaluate whether \
the provided evidence is sufficient to fully answer the sub-question.

Sub-Question: {question}

Evidence:
{evidence_text}

Instructions:
- Evaluate relevance and sufficiency, not the quality of the writing.
- Do not invent facts not present in the evidence.
- Acknowledge that the evidence may be spread across multiple excerpts.
- If the evidence does not fully answer the question, specify exactly what is missing.
- Return ONLY a JSON object shaped exactly like this:
{{
  "satisfied": true,
  "reason": "explanation...",
  "missing_aspects": ["aspect 1", "aspect 2"]
}}
"""


class CritiqueEvidenceUseCase:
    """Evaluate whether retrieved evidence satisfies a SubQuestion."""

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    def execute(
        self, sub_question: SubQuestion, evidence: list[Evidence]
    ) -> CritiqueResult:
        """Evaluate the evidence against the sub-question.

        Args:
            sub_question: The question being researched.
            evidence: The gathered evidence.

        Returns:
            A structured CritiqueResult.

        Raises:
            CritiqueError: If the LLM fails or produces malformed output.
        """
        if not evidence:
            return CritiqueResult(
                satisfied=False,
                reason="No evidence was retrieved.",
                missing_aspects=["All aspects missing due to lack of evidence."],
            )

        evidence_text = "\n\n".join(
            f"--- Source: {e.citation.source_name} ---\n{e.content}"
            for e in evidence
        )

        prompt = _PROMPT_TEMPLATE.format(
            question=sub_question.text,
            evidence_text=evidence_text,
        )

        try:
            response = self._llm.complete_structured(prompt, CRITIQUE_SCHEMA)
        except Exception as exc:
            raise CritiqueError(
                f"critic LLM call failed: {type(exc).__name__}: {exc}"
            ) from exc

        return _validate_response(response)


def _validate_response(response: Any) -> CritiqueResult:
    """Validate and parse the structured response mapping."""
    if not isinstance(response, Mapping):
        raise CritiqueError(f"response must be a mapping, got {type(response).__name__}")

    # Unwrap if the LLM nested the response under the schema title
    if _SATISFIED_KEY not in response and "evidence_critique" in response:
        if isinstance(response["evidence_critique"], Mapping):
            response = response["evidence_critique"]

    # Validate satisfied
    if _SATISFIED_KEY not in response:
        raise CritiqueError(f"missing key: {_SATISFIED_KEY}")
    satisfied = response[_SATISFIED_KEY]
    if not isinstance(satisfied, bool):
        raise CritiqueError(f"{_SATISFIED_KEY} must be a bool, got {type(satisfied).__name__}")

    # Validate reason
    if _REASON_KEY not in response:
        raise CritiqueError(f"missing key: {_REASON_KEY}")
    reason = response[_REASON_KEY]
    if not isinstance(reason, str) or not reason.strip():
        raise CritiqueError(f"{_REASON_KEY} must be a non-empty string")

    # Validate missing aspects
    if _MISSING_ASPECTS_KEY not in response:
        raise CritiqueError(f"missing key: {_MISSING_ASPECTS_KEY}")
    missing_aspects_raw = response[_MISSING_ASPECTS_KEY]
    if not isinstance(missing_aspects_raw, list):
        raise CritiqueError(
            f"{_MISSING_ASPECTS_KEY} must be a list, got {type(missing_aspects_raw).__name__}"
        )

    missing_aspects: list[str] = []
    for i, item in enumerate(missing_aspects_raw):
        if not isinstance(item, str) or not item.strip():
            raise CritiqueError(f"{_MISSING_ASPECTS_KEY}[{i}] must be a non-empty string")
        missing_aspects.append(item.strip())

    return CritiqueResult(
        satisfied=satisfied,
        reason=reason.strip(),
        missing_aspects=missing_aspects,
    )

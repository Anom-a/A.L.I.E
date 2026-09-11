"""SynthesizeReportUseCase — builds the final Report from gathered evidence.

This use case combines the original ResearchQuery, SubQuestions, and retrieved Evidence
to generate a coherent, fully cited Report using an LLM.

It rigorously enforces citation provenance by assigning stable short identifiers
(e.g., [CIT-1]) before calling the LLM, and ensuring that any citation returned
by the LLM maps exactly to one of those known sources.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Optional

from domain.entities.citation import Citation
from domain.entities.evidence import Evidence
from domain.entities.report import Report, ReportSection
from domain.entities.research_query import ResearchQuery
from domain.entities.sub_question import SubQuestion
from domain.ports.llm_port import LLMPort


class SynthesisError(Exception):
    """Raised when synthesis fails due to invalid inputs or LLM errors."""


# ---------------------------------------------------------------------------
# Structured Output Schema
# ---------------------------------------------------------------------------

_TITLE_KEY = "title"
_SECTIONS_KEY = "sections"
_SEC_TITLE_KEY = "title"
_SEC_CONTENT_KEY = "content"
_SEC_CITATIONS_KEY = "citation_ids"

SYNTHESIS_SCHEMA: Mapping[str, Any] = {
    "title": "report_synthesis",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        _TITLE_KEY: {"type": "string"},
        _SECTIONS_KEY: {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    _SEC_TITLE_KEY: {"type": "string"},
                    _SEC_CONTENT_KEY: {"type": "string"},
                    _SEC_CITATIONS_KEY: {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [_SEC_TITLE_KEY, _SEC_CONTENT_KEY, _SEC_CITATIONS_KEY],
            },
        },
    },
    "required": [_TITLE_KEY, _SECTIONS_KEY],
}


_PROMPT_TEMPLATE = """You are an expert research synthesizer. Your task is to write \
a coherent, well-structured report answering the original research topic based ONLY \
on the provided evidence.

Original Research Topic:
{topic}

Sub-Questions Explored:
{sub_questions_text}

Available Evidence:
{evidence_text}

{gaps_text}

Instructions:
- Synthesize the evidence into a logical report with multiple sections.
- Answer the original research topic directly.
- Cite your claims using ONLY the provided [CIT-N] identifiers.
- Do NOT invent facts or hallucinate external information.
- Do NOT invent or fabricate citations. Every citation must be a provided [CIT-N].
- Do NOT create source URLs.
- If there are unresolved gaps, you may acknowledge them, but do not invent evidence for them.
- Return ONLY a JSON object matching the requested schema.
"""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SynthesizeReportUseCase:
    """Synthesize a fully cited report from retrieved evidence."""

    def __init__(
        self,
        llm: LLMPort,
        *,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        """Initialise the synthesizer.

        Args:
            llm: The LLM adapter used to generate the report structure.
            clock: Source of timestamps for the generated Report.
        """
        self._llm = llm
        self._clock = clock if clock is not None else _utc_now

    def execute(
        self,
        research_query: ResearchQuery,
        sub_questions: list[SubQuestion],
        evidence: list[Evidence],
    ) -> Report:
        """Synthesize the final report.

        Args:
            research_query: The original overarching query.
            sub_questions: The broken-down questions.
            evidence: The gathered evidence to support the report.

        Returns:
            A constructed domain Report.

        Raises:
            SynthesisError: If zero evidence is provided, inputs are invalid,
                or the LLM produces a malformed or improperly cited structure.
        """
        if not evidence:
            raise SynthesisError("Cannot synthesize a report because no evidence was retrieved.")

        # 1. Input Validation & ID mapping
        # Create a stable mapping of Citation -> CIT-N
        citation_map: dict[str, Citation] = {}
        cit_counter = 1
        
        # Deduplicate citations by source_url_or_id
        for ev in evidence:
            cid = ev.citation.source_url_or_id
            if cid not in [c.source_url_or_id for c in citation_map.values()]:
                cit_id = f"CIT-{cit_counter:03d}"
                citation_map[cit_id] = ev.citation
                cit_counter += 1
                
        # 2. Identify unresolved gaps
        evidence_sq_ids = {ev.sub_question_id for ev in evidence}
        unresolved_sqs = [sq for sq in sub_questions if sq.id not in evidence_sq_ids]

        # 3. Format prompt
        sub_questions_text = "\n".join(f"- {sq.text}" for sq in sub_questions)
        
        evidence_blocks = []
        for ev in evidence:
            # Find the assigned CIT identifier
            cit_id = next(k for k, v in citation_map.items() if v.source_url_or_id == ev.citation.source_url_or_id)
            block = f"[{cit_id}]\nSource: {ev.citation.source_name}\nExcerpt:\n{ev.content}\n"
            evidence_blocks.append(block)
            
        evidence_text = "\n".join(evidence_blocks)

        gaps_text = ""
        if unresolved_sqs:
            gaps_list = "\n".join(f"- {sq.text}" for sq in unresolved_sqs)
            gaps_text = f"Unresolved Gaps (No evidence retrieved):\n{gaps_list}\n"

        prompt = _PROMPT_TEMPLATE.format(
            topic=research_query.topic,
            sub_questions_text=sub_questions_text,
            evidence_text=evidence_text,
            gaps_text=gaps_text,
        )

        # 4. LLM Call
        try:
            response = self._llm.complete_structured(prompt, SYNTHESIS_SCHEMA)
        except Exception as exc:
            raise SynthesisError(f"LLM synthesis failed: {type(exc).__name__}: {exc}") from exc

        # 5. Validation and Report Construction
        return self._build_report(research_query.id, response, citation_map)

    def _build_report(
        self,
        query_id: Any,
        response: Mapping[str, Any],
        citation_map: dict[str, Citation],
    ) -> Report:
        """Validate LLM output and construct domain Report."""
        if not isinstance(response, Mapping):
            raise SynthesisError(f"response must be a mapping, got {type(response).__name__}")
            
        if _TITLE_KEY not in response:
            raise SynthesisError(f"missing key: {_TITLE_KEY}")
        title = response[_TITLE_KEY]
        if not isinstance(title, str) or not title.strip():
            raise SynthesisError(f"{_TITLE_KEY} must be a non-empty string")
            
        if _SECTIONS_KEY not in response:
            raise SynthesisError(f"missing key: {_SECTIONS_KEY}")
        sections_raw = response[_SECTIONS_KEY]
        if not isinstance(sections_raw, list):
            raise SynthesisError(f"{_SECTIONS_KEY} must be a list")

        report_sections: list[ReportSection] = []
        used_citation_ids: set[str] = set()

        for i, sec in enumerate(sections_raw):
            if not isinstance(sec, Mapping):
                raise SynthesisError(f"section {i} must be a mapping")
                
            sec_title = sec.get(_SEC_TITLE_KEY)
            if not isinstance(sec_title, str) or not sec_title.strip():
                raise SynthesisError(f"section {i} {_SEC_TITLE_KEY} must be a non-empty string")
                
            sec_content = sec.get(_SEC_CONTENT_KEY)
            if not isinstance(sec_content, str) or not sec_content.strip():
                raise SynthesisError(f"section {i} {_SEC_CONTENT_KEY} must be a non-empty string")
                
            cit_ids = sec.get(_SEC_CITATIONS_KEY)
            if not isinstance(cit_ids, list):
                raise SynthesisError(f"section {i} {_SEC_CITATIONS_KEY} must be a list")
                
            domain_citation_ids: list[str] = []
            for cid in cit_ids:
                if not isinstance(cid, str):
                    raise SynthesisError(f"citation ID '{cid}' must be a string")
                cid = cid.strip()
                if cid not in citation_map:
                    raise SynthesisError(f"Unknown citation ID generated: {cid}")
                
                real_citation = citation_map[cid]
                domain_citation_ids.append(real_citation.source_url_or_id)
                used_citation_ids.add(cid)
                
            report_sections.append(
                ReportSection(
                    title=sec_title.strip(),
                    content=sec_content.strip(),
                    citation_ids=tuple(domain_citation_ids),
                )
            )

        # Build final used citations tuple
        report_citations = tuple(citation_map[cid] for cid in used_citation_ids)
        
        try:
            return Report(
                query_id=query_id,
                sections=tuple(report_sections),
                citations=report_citations,
                generated_at=self._clock(),
            )
        except Exception as exc:
            raise SynthesisError(f"Domain report construction failed: {exc}") from exc

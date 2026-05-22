"""Deterministic scorers.

Three kinds in Phase 1:
  - regex:       output matches the given regular expression
  - json_schema: output is valid JSON and conforms to the given JSON Schema
  - contains:    output contains the given substring

Deterministic scorers return a binary score (0.0 or 1.0). Use them whenever a check
can be expressed mechanically. Reach for LLM-as-judge only when no rule can describe
quality.
"""

from __future__ import annotations

import json
import re
from typing import Any

import jsonschema

from ..models import ScoreResult


def score_regex(output: str, params: dict[str, Any]) -> ScoreResult:
    pattern = params["pattern"]
    flags = re.MULTILINE | re.DOTALL if params.get("multiline") else 0
    if params.get("ignore_case"):
        flags |= re.IGNORECASE
    match = re.search(pattern, output, flags=flags)
    return ScoreResult(
        scorer="regex",
        passed=match is not None,
        score=1.0 if match else 0.0,
        reason=None if match else f"output did not match /{pattern}/",
    )


def score_contains(output: str, params: dict[str, Any]) -> ScoreResult:
    substring = params["substring"]
    case_sensitive = params.get("case_sensitive", True)
    haystack = output if case_sensitive else output.lower()
    needle = substring if case_sensitive else substring.lower()
    hit = needle in haystack
    return ScoreResult(
        scorer="contains",
        passed=hit,
        score=1.0 if hit else 0.0,
        reason=None if hit else f"output did not contain '{substring}'",
    )


def score_json_schema(output: str, params: dict[str, Any]) -> ScoreResult:
    """Pass when output is valid JSON AND conforms to the given schema.

    Two failure modes, reported distinctly:
      1. Output is not valid JSON at all.
      2. Output is valid JSON but violates the schema.
    """
    schema = params["schema"]
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError as exc:
        return ScoreResult(
            scorer="json_schema",
            passed=False,
            score=0.0,
            reason=f"output is not valid JSON: {exc.msg}",
        )

    try:
        jsonschema.validate(instance=parsed, schema=schema)
    except jsonschema.ValidationError as exc:
        return ScoreResult(
            scorer="json_schema",
            passed=False,
            score=0.0,
            reason=f"JSON did not match schema: {exc.message}",
        )

    return ScoreResult(scorer="json_schema", passed=True, score=1.0)

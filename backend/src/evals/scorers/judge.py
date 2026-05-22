"""LLM-as-judge scorer.

Use this when quality cannot be expressed as a rule. The judge model reads the
candidate output, applies a written rubric, and returns a structured verdict.

Defaults:
  - Judge model: claude-sonnet-4-6
  - Pass threshold: 0.7

The judge prompt is intentionally short and opinionated. A long judge prompt drifts;
a short one with a clear rubric stays on rails.
"""

from __future__ import annotations

import json
from typing import Any

from ...providers.claude import ClaudeProvider
from ..models import ScoreResult

DEFAULT_JUDGE_MODEL = "claude-sonnet-4-6"
DEFAULT_PASS_THRESHOLD = 0.7

JUDGE_SYSTEM_PROMPT = """\
You are a strict, fair evaluator scoring a candidate response against a rubric.

You must:
1. Read the rubric carefully.
2. Read the candidate response.
3. Score the response on a 0.0 to 1.0 scale.
4. Output ONLY a JSON object with two keys: "score" (float) and "reason" (one short sentence).

Do not include any text outside the JSON object. Do not be charitable. If the
response misses any part of the rubric, deduct.
"""

JUDGE_USER_TEMPLATE = """\
RUBRIC:
{rubric}

CANDIDATE RESPONSE:
{output}

Return JSON only.\
"""


async def score_judge(
    output: str,
    params: dict[str, Any],
    *,
    provider: ClaudeProvider | None = None,
) -> ScoreResult:
    rubric = params["rubric"]
    judge_model = params.get("judge_model", DEFAULT_JUDGE_MODEL)
    pass_threshold = float(params.get("pass_threshold", DEFAULT_PASS_THRESHOLD))

    judge = provider or ClaudeProvider()
    resp = await judge.complete(
        model=judge_model,
        system=JUDGE_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": JUDGE_USER_TEMPLATE.format(rubric=rubric, output=output),
            }
        ],
        max_tokens=256,
    )

    try:
        verdict = json.loads(resp.content)
        score = float(verdict["score"])
        reason = str(verdict.get("reason", "")) or None
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return ScoreResult(
            scorer="judge",
            passed=False,
            score=0.0,
            reason=f"judge returned unparseable verdict: {exc}",
        )

    score = max(0.0, min(1.0, score))
    return ScoreResult(
        scorer="judge",
        passed=score >= pass_threshold,
        score=score,
        reason=reason,
    )

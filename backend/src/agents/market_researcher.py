"""Market Researcher dogfood agent.

Demonstrates: tool use, multi-step agentic loop, cost attribution via trace capture.
Phase 1 uses a mocked web search tool so the agent works without external API keys.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from ..providers.claude import ClaudeProvider
from ..traces.capture import capture_trace

AGENT_NAME = "market_researcher"
DEFAULT_MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """\
You are an expert market researcher. When given a topic, use the search_web tool to
gather relevant information, then synthesize a structured report.

Your final response MUST be a JSON object with these exact keys:
- topic (string)
- key_players (list of strings)
- market_size_estimate (string, e.g. "$4.2B by 2027")
- main_trends (list of strings, 3-5 items)
- risks (list of strings, 2-4 items)
- summary (string, 2-3 sentences)

Return ONLY the JSON object, no markdown fences.
"""

TOOLS = [
    {
        "name": "search_web",
        "description": "Search the web for information on a topic. Returns a list of relevant snippets.",
        "input_schema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)",
                    "default": 5,
                },
            },
        },
    }
]

# Phase 1: stub search returns plausible-looking synthetic results.
_STUB_SNIPPETS = [
    "The market is projected to grow at a CAGR of 18% through 2028.",
    "Key players include established incumbents and well-funded startups.",
    "AI and automation are reshaping the competitive landscape.",
    "Regulatory pressure is increasing in major markets.",
    "Enterprise adoption is accelerating, driven by cost savings.",
    "Open-source alternatives are commoditizing previously proprietary solutions.",
    "Geographic expansion into APAC represents a major growth vector.",
]


def _mock_search(query: str, num_results: int = 5) -> list[str]:
    return _STUB_SNIPPETS[:num_results]


async def run(topic: str, *, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    """Run the market researcher agent. Returns the structured report dict."""
    provider = ClaudeProvider()
    run_id = str(uuid.uuid4())
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": f"Research this market: {topic}"}
    ]

    while True:
        resp = await provider.complete(
            model=model,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=TOOLS,
            max_tokens=2048,
        )

        capture_trace(
            resp,
            system_prompt=SYSTEM_PROMPT,
            input_messages=messages,
            agent_name=AGENT_NAME,
            run_id=run_id,
        )

        if not resp.tool_calls:
            # Final answer
            try:
                return json.loads(resp.content)
            except json.JSONDecodeError:
                return {"raw": resp.content, "topic": topic, "error": "non-json final response"}

        # Execute tool calls and loop
        messages.append({"role": "assistant", "content": resp.content or ""})
        tool_results = []
        for tc in resp.tool_calls:
            if tc.name == "search_web":
                query = tc.arguments.get("query", topic)
                num = tc.arguments.get("num_results", 5)
                snippets = _mock_search(query, num)
                result_text = "\n".join(f"- {s}" for s in snippets)
            else:
                result_text = f"Unknown tool: {tc.name}"

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result_text,
                }
            )

        messages.append({"role": "user", "content": tool_results})

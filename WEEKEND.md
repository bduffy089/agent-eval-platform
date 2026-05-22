# Weekend Pickup: Hand-Write Exercise

Britney, when you come back to this, here is exactly where you left off and what to do.

## What happened

We bootstrapped the repo (commit `b9f276e`) which included `providers/base.py` written by Claude.
You agreed to do Option 1 of the absorption protocol: hand-write the foundational files yourself
so you can defend them in interviews.

We started the Socratic walkthrough on `base.py`. You got the *contents* right but the *purpose*
explanation was still pattern-matched from CLAUDE.md. We did not finish the walkthrough.

For speed today, we restored `base.py` from the reference. The reference version is preserved
at git tag `v0-bootstrap-reference` so you can always diff your hand-written version against it.

## The five hand-write files (from the discipline plan)

| Order | File | Status | Why this one |
|---|---|---|---|
| 1 | `backend/src/providers/base.py` | Restored from reference. Re-do as exercise. | "Walk me through your provider abstraction" is question 1 in any API design screen. |
| 2 | `backend/src/traces/cost.py` | Not yet created (cost math lives inside each provider today). Create + own. | "How do you compute cost?" must answer cold. |
| 3 | `backend/src/evals/scorers/json_schema.py` (or similar) | Not yet created. | Writing one scorer means you can talk about all of them. |
| 4 | Cache_control block in `claude.py` | Already written. Re-derive later from Anthropic caching docs. | Anthropic Enterprise's whole pitch is prompt caching. Be fluent in 30 seconds. |
| 5 | LLM-as-judge prompt + rubric (lives in `backend/src/evals/judge.py` or similar) | Not yet created. | Your prompt is the IP. Write it yourself. |

## The absorption protocol (do not skip)

1. **Open the target file blank.** Do NOT peek at the reference. Write a comment block in
   plain English describing what each function should do, then fill it in. Let it be bad.
2. **Run the tests.** Tests live in `backend/tests/test_providers.py`. If they pass, your
   version works.
3. **Diff against the reference.** `git diff v0-bootstrap-reference -- backend/src/providers/base.py`
4. **Five-minute teach-back.** Open voice memo. Pretend you are explaining this file to
   Angela. If you stall or hand-wave, you do not understand it yet. Go back.
5. **Add one line to `WHY.md`** for any non-obvious choice you made.

## How to start `base.py` next time

Before you touch the file, answer this in one sentence in your own words (no jargon, no
lifting from CLAUDE.md):

> What is this file FOR, and what would break if it did not exist?

Hint: it is not about cost tracking. Cost tracking is something it enables. The actual job
is one level more abstract. Think wall outlet: the wall does not care if a lamp or a toaster
plugs in, as long as the plug fits the shape.

When you can say that out loud in your own words, you are ready to write the file.

## Quick orientation when you come back

```bash
cd /Users/Agents/Documents/agent-eval-platform
git log --oneline                              # see where we left off
git show v0-bootstrap-reference -- backend/src/providers/base.py  # peek at reference only AFTER your first pass
```

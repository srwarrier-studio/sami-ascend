# Laya knowledge base

Reference notes on Laya, the decision model intent-api may use to classify a manager's question. Written from the official documentation so we do not have to go back to the site for every question.

Source: https://nandhakishorm.github.io/laya/ (read 2026-11-01, package version seen in our test environment: laya 0.4.19). Licence: Apache 2.0, Convai Innovations. Code: https://github.com/NandhaKishorM/laya

These are summaries, not copies. Where the site is vague or inconsistent the note says so. When behaviour matters for a decision, check the site or run a test; the library moves quickly.

| File | What is in it |
|---|---|
| [01-concepts.md](01-concepts.md) | What Laya is, the three question types, what comes back, confidence |
| [02-decide-and-schema.md](02-decide-and-schema.md) | `decide()` with a JSON schema or pydantic model, supported subset, errors, limits |
| [03-agent-and-router.md](03-agent-and-router.md) | `load`, `Agent`, `Router`, `system_one`, batch, long text, shortlist, routing rules |
| [04-hooks.md](04-hooks.md) | Prediction hooks: events, context, errors, patterns |
| [05-accuracy-calibration-limits.md](05-accuracy-calibration-limits.md) | Benchmarks, known limits, calibration, guardrail limits |
| [06-serving-and-deployment.md](06-serving-and-deployment.md) | HTTP API, CLI, MCP, Docker, checkpoint integrity, fast backends |
| [07-evaluation-finetuning-adoption.md](07-evaluation-finetuning-adoption.md) | Evaluation harness, fine-tuning, staged adoption |
| [08-integrations.md](08-integrations.md) | LangChain, LlamaIndex, CrewAI, Agno, tool selection, TypeScript client |
| [09-intent-api-notes.md](09-intent-api-notes.md) | Our own test results and what the docs mean for intent-api |

Read 09 first if you only have five minutes.

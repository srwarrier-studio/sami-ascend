# decide(): schema-driven decisions

`decide()` turns a JSON schema or pydantic model into Laya questions and returns typed values. Each property is one question, all answered in one pass.

```python
import laya
schema = {"type": "object", "properties": {
    "department": {"type": "string", "enum": ["billing", "support", "sales"],
                   "description": "Which team should handle this?"},
    "urgency": {"type": "integer", "minimum": 0, "maximum": 2},
    "needs_human": {"type": "boolean"}}}
agent = laya.load("convaiinnovations/laya")
agent.decide("I was charged twice, refund me.", schema=schema)
```

Pydantic (needs `laya[structured]`): `Literal[...]` becomes an enum, `Optional[...]` becomes `anyOf` with null, an `Enum` class becomes a `$ref`.

## Key facts
- The `description` is the question wording, and the only lever. `title` is ignored. "A good description is what makes the decision accurate. Be explicit about what each option means."
- Projection is exact: `enum: [1, 2, 3]` returns the integer `2`. A boolean is `noul >= 0.5`.
- Optional (`anyOf` with `null`): the null branch is dropped before planning. The question is identical to the plain enum. A field with no answer is absent from the result, so check for the key. Note: this does not make the model say "none of these" by itself; in our test it never did (see 09).
- Pass exactly one of `schema` or `questions`. With `questions`, `decide` returns raw answers.
- Extra keyword arguments go to `predict`: `model=`, `task=`, `hooks=`, token budgets.

## Supported subset
| Property | Question | Value |
|---|---|---|
| `enum` of strings | choice | chosen value (original type kept) |
| `const` | choice | that value |
| `boolean` | noul | true/false |
| integer with `minimum`/`maximum` | score | highest-probability level as integer |
| number with integer bounds | score | level as integer |
| `anyOf` enum + `null` | choice | as enum; absent if no answer |
| `oneOf` boolean + `null` | noul | as boolean |
| local `$ref` into `$defs` | choice | as the named enum |
| `allOf` with one item | choice | as enum (pydantic v1 wrapper) |

Limits: `MAX_PROPERTIES = 32`, `MAX_OPTIONS = 32`, `MAX_SCORE_LEVELS = 10`.

## Rejections (`laya.structured.SchemaError`, a `ValueError`)
Free string; array; nested object; unresolved or recursive `$ref`; duplicate enum labels (`[1, "1"]`); empty enum; non-array enum; number without bounds; `maximum` below `minimum`; more than 10 score levels; `anyOf` with two non-null branches; multiple non-null `type`s; `format` such as date; non-object property; empty `properties`; more than 32 properties or 32 options. Messages name the path, for example `properties.name: a free string cannot be a fixed option set; use 'enum' or a boolean`.

## API
| Function | Purpose |
|---|---|
| `agent.decide(state, schema, *, questions, return_details, min_confidence, **predict_kwargs)` | One state. Also on `Router`, and free function `laya.decide(runner, ...)` |
| `agent.decide_batch(states, schema, ...)` | Plans the schema once, one batched call, results in input order |
| `questions_from_json_schema`, `questions_from_pydantic` | Schema to Laya questions |
| `answers_to_json`, `answer_to_pydantic` | Raw answers to values |
| `plan_from_json_schema` | Validated field plan (advanced) |

`decide_batch` routing keys: call-level (`batch_size`, `hooks`, `sort_by_length`) go to `predict_batch`; routing pins and budgets (`model`, `task`, `lang`, `lang_guess`, `max_len`, `head_max_len`) are copied to each request. A runner without `predict_batch` raises `TypeError`. Batching can shift borderline argmaxes.

## Details with `return_details=True`
```python
r = agent.decide(state, schema=Ticket, return_details=True)
r.values["department"]             # "billing"
r.answer_confidence["department"]  # max(p): gate on this
r.confidence["department"]         # entropy-based for choice
r.probabilities["department"]      # {"billing": 0.94, "support": 0.06, ...}
r.usage                            # input_tokens, state_tokens, state_tokens_dropped, truncated, ...
r.routing                          # Router decision when a Router answered
```
`usage.output_tokens` is always 0. `options` appears only when option labels share a token span (a sign the head budget is too small).

Gating example from the docs:
```python
if result.answer_confidence["department"] < 0.6:
    result.values["department"] = "human-review"
```
(This writes a value outside the enum, so downstream code must handle it.)

# Concepts

## What Laya is
A multilingual, non-autoregressive "System 1" decision engine. It reads a `state` (any text or JSON) and answers typed questions about it in one forward pass. Nothing is generated: no tokens, no JSON repair. Built on ModernBERT-large (English) and mmBERT-base (multilingual). It runs on your own hardware, CPU or GPU, in-process or as an HTTP service. 100+ languages.

It is for classification, gating and routing. It is not for generation, translation or open-ended answers.

Checkpoints: `english`, `multilingual` (default since 0.4.0), `typed-decisions` (fine-tuned on a typed-decisions benchmark; not chosen automatically). All three live in one bundle repo `convaiinnovations/laya` as subfolders.

## The three question types
A question set is a dict `{question_id: {...}}`. All questions are answered against the same state in one pass.

| Type | You give | You get |
|---|---|---|
| `choice` | `instructions` and `criteria`: ordered `{label: description}` | `choice` (the label), `probabilities` per label, `confidence`, `answer_confidence` |
| `noul` | `instructions`, optional `criteria` and `labels` | `noul`: probability the answer is yes (a number, not a boolean; you pick the threshold) |
| `score` | `instructions`, `criteria`: ordered list of levels | `score`: an expected value (not the likeliest level); use argmax of `probabilities` or the `legend` for a label |

```python
questions = {
  "domain": {"type": "choice", "instructions": "Which domain is this question about?",
             "criteria": {"sales": "money from customers", "purchases": "money spent with vendors"}},
  "needs_compare": {"type": "noul", "instructions": "Does the user want a comparison?"},
}
result = agent.system_one("sales today vs yesterday", questions)
result["answers"]["domain"]["choice"]
```

Rules worth remembering:
- `choice` order is positional. The same labels in another order are a different question and can give a different answer.
- Descriptions matter: the model reads the rendered question text, so make each option self-contained, with the distinguishing fact first.
- `noul` is its own head, not a two-option choice. `labels` can rename the two sides, but the polarity stays, and labels can pull the answer toward their wording. Validate relabelling on your data.
- `score` rounding: do not round the expected value and treat it as the label.
- Probabilities are rounded to four decimals independently, so they may not sum to exactly 1.
- `action.act_probability` is a separate head score ("should an agent act on this"); the library does not threshold it.

## Confidence: three different numbers
- `answer_confidence` = `max(p)`. Probability on the reported answer. This is what `min_confidence` gates on and what temperature scaling fits. Gate on this.
- `confidence`: for `choice` and `score` it is normalised entropy, `1 - H(p)/log(k)` (scale changes with the number of options); for `noul` it is `max(p_true, 1 - p_true)`. Example: a two-option answer of 0.90 gives `noul` confidence 0.90 but `choice` confidence 0.53.
- `x_jev_confidence`: the TypeSafe Jev formula, `choice` and `score` only (HTTP API).

Do not use one threshold across types without measuring each. A field with no usable confidence is `None`, which is not the same as `0.0`.

Shipped checkpoints are over-confident and uncalibrated (see 05). A high probability is not proof of a right answer.

## Abstention
- Pass `min_confidence` (a number in [0, 1], or a per-bucket map such as `{"choice:3-5": 0.9, "default": 0.4}`) to `system_one`, `predict_batch` or `decide`.
- Answers below it get `low_confidence: true` and `abstention: "abstained"`; answers are kept, not removed. States: `passed`, `abstained`, `unevaluated`.
- In `decide`, an optional field (`anyOf` with `null`) that has no answer is simply missing from the values.

## Presets
Five ready-made question sets, to inspect and validate before use as policy: `triage_questions`, `email_questions`, `guard_questions`, `moderation_questions`, `router_questions`. `render_options` shows exactly what text is sent (it takes the internal `{"t": ..., "crit": ...}` form; the public `type`/`criteria` form raises `KeyError: 't'`).

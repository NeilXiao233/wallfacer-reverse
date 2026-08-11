# Breakthrough Protocol

Use this protocol after a route fails or returns an ambiguous observation.

1. Record the exact observation, command/input, environment, and artifact hash.
2. State the hypothesis that the observation weakens. Do not state that the objective is impossible.
3. Create a route matrix with at least one materially different layer, such as package data, cache/backup, runtime observation, or provider response.
4. Select the smallest test that distinguishes the leading hypotheses. Change one relevant condition at a time.
5. Record the result in `attempt-ledger.json`, including what remains unblocked and the next route.
6. Mark `blocked` only when the missing prerequisite is objective and the ledger contains a concrete reopening condition.

Each restriction is a conditional object, never a permanent prohibition:

```json
{
  "condition": "the observed condition",
  "effect": "what it prevents",
  "does_not_block": ["independent action"],
  "next_actions": ["route that can remove or bypass it"],
  "source": ["evidence/locator"]
}
```

The protocol carries the core breakthrough discipline from 思想钢印: failed paths are evidence about paths, not proof against the objective; no facts are fabricated; data is preserved; and progress ends only at verified delivery or a named, evidenced boundary.

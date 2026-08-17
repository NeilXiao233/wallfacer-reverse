# Breakthrough Protocol

Use this protocol after a target-specific route fails or returns an ambiguous observation. It is a reasoning discipline, not a requirement to create a second state ledger.

1. Record the exact observation, command/input, environment, and artifact hash in the project's existing evidence location.
2. State the hypothesis that the observation weakens. Do not state that the objective is impossible.
3. Propose at least one materially different layer, such as package data, cache/backup, runtime observation, or provider response.
4. Select the smallest test that distinguishes the leading hypotheses. Change one relevant condition at a time.
5. Record what remains unblocked and the next route alongside the project evidence or task card.
6. Mark `blocked` only when the prerequisite is objective and the project record names a concrete reopening condition.

Skill maintenance, reference-corpus audits, template migration, state validation, and handoff formatting are operational work. They do not count as target attempts and cannot trigger a capability escalation.

Each restriction is conditional, never a permanent prohibition:

```json
{
  "condition": "the observed condition",
  "effect": "what it prevents",
  "does_not_block": ["independent action"],
  "next_actions": ["route that can remove or bypass it"],
  "source": ["project evidence locator"]
}
```

Failed paths are evidence about paths, not proof against the objective. Do not fabricate facts, preserve data, and stop only at verified delivery or a named, evidenced boundary.

# Model routing

Choose models by task shape and current runtime capability. Provider analogies
are user intent, not evidence of equal quality, price, latency, or context.

## Codex preference ladder

1. **Coordinator and critical verifier:** prefer `gpt-5.6-sol` with `high`
   reasoning when the current tool schema exposes that slug. Use it for
   ambiguous, high-value, architectural, or adversarial work.
2. **Clear, repeatable worker:** prefer `gpt-5.6-luna` with `xhigh` when Luna
   is callable. This matches the desired PBES worker role for extraction,
   classification, transformation, and structured summaries.
3. **Current fallback:** when Luna is documented but not callable, use
   `gpt-5.6-terra`. Start at `medium`; raise to `high` or `xhigh` only when the
   bounded assignment genuinely needs deeper reasoning.
4. **No explicit override:** omit model fields and inherit the parent when the
   runtime does not expose a valid preferred slug or when full history is
   required.

Promote an ambiguous or load-bearing worker to Sol instead of compensating
indefinitely with higher effort on a throughput-oriented model.

## Claude preference ladder

Preserve the packaged Claude worker model while the runtime accepts it. Treat
the historical "frontier coordinator + Sonnet workers" wording as a routing
strategy, not a portable benchmark.

## Cost and benchmark guardrails

- Higher reasoning effort increases latency and token use.
- Do not claim the Claude reference run's cost or speed ratios for Codex.
- Record actual task-level observations before changing defaults.
- Centralize routing here; do not scatter model slugs through briefs or core
  doctrine.

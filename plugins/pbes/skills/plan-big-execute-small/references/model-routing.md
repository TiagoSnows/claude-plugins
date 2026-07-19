# Model routing

Choose models by task shape and current runtime capability. Provider analogies
are user intent, not evidence of equal quality, price, latency, or context.

## Preference ladder

1. **Coordinator and critical verifier:** prefer `gpt-5.6-sol` with `high`
   reasoning when the current tool schema exposes that slug. Use it for
   ambiguous, high-value, architectural, or adversarial work.
2. **Clear, repeatable worker:** prefer `gpt-5.6-luna` with `xhigh` when Luna
   is callable. This matches the desired worker role for extraction,
   classification, transformation, and structured summaries.
3. **Current fallback:** when Luna is documented but not callable, use
   `gpt-5.6-terra`. Start at `medium`; raise to `high` or `xhigh` only when the
   bounded assignment genuinely needs deeper reasoning.
4. **No explicit override:** omit model fields and inherit the parent when the
   runtime does not expose a valid preferred slug or full history is required.

Promote ambiguous or load-bearing work to Sol instead of compensating
indefinitely with higher effort on a throughput-oriented model.

## Cost and benchmark guardrails

- Higher reasoning effort increases latency and token use.
- Do not claim Claude reference-run cost or speed ratios for Codex.
- Record task-level observations before changing defaults.
- Centralize routing here; do not scatter model slugs through briefs.

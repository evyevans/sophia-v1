# Architecture

Python standard library only; no runtime dependencies. The core is deterministic and accepts an explicit evaluation time. File IO belongs to the CLI/report layer. There are no SQL migrations, remote endpoint defaults, service keys, wallet libraries, order methods or messaging transports.

```text
local snapshot JSON
  -> bounded structure, exact decimals, identity and timestamp validation
  -> source payload hashes and declared upstream eligibility
  -> spot book, quote risk, constraints and closed UTC-bar gates
  -> five category-aware evidence reviews + market/technical lenses
  -> immutable research result / hard-coded execution and dispatch false
  -> escaped local HTML + complete JSON
```

## File responsibilities

- `floatglass/live.py`: opt-in fixed public BTC/USD GET capture, separated from the offline evaluator.
- `floatglass/contracts.py`: bounded JSON parsing, exact numeric and time primitives, canonical hashes and asset identity.
- `floatglass/core.py`: fixed versioned policy, evidence eligibility, disjoint lineage, market and candle validation, final qualification.
- `floatglass/lenses.py`: five neutral domain reviews and derived supply context. No person names, votes or consensus scoring.
- `floatglass/report.py`: local HTML and JSON with per-file atomic replacement. No JavaScript, remote assets or active source navigation.
- `floatglass/demo.py`: three clearly synthetic scenarios; never a fallback branch in evaluation.
- `floatglass/__main__.py`: CLI, explicit historical evaluation, current UTC default, bounded error messages.
- `source-registry.json`: dated human reading references and candidate integration status. It is **not loaded by the scoring engine**.
- `input.schema.json`: structural documentation; semantic validation remains executable Python.
- `agent/`, `skills/`, `ops/routines/`: community Grok Bot workflow source. No installed routines or inherited permissions.
- `tools/release.py`: explicit file list, hash verification, privacy pattern/link checks and deterministic ZIP creation.

## Boundaries adapted from the references

REA's inspected [upstream runtime evidence contract](https://github.com/morluto/rea/blob/main/docs/mcp-contracts.md) distinguishes normalized results, coverage, limitations and unknowns. Floatglass uses that evidence-first approach, including explicit unknowns and hash scope. It does not embed REA, register an MCP server, invoke a decompiler or claim REA analysis was performed. The source was already available, so direct read-only source inspection was appropriate.

The attached first-principles framing method informed the decision to build a research evidence product with a useful first run. A narrative score alone cannot establish a credible trading system. The legacy research workflow supplies the useful pattern of explicit gates, but the implementation here is newly authored around crypto contracts; no private runtime, history, deployment configuration, investor personas or report assets were copied into this release.

## Extension order

First validate an operator-supplied real snapshot and complete Grok Bot acceptance. A future collector must separately enforce allowlisted read-only public endpoints, authentication/terms, timeouts, rate limits, source identity and immutable capture. A future simulator needs a reconciled persistent ledger and realistic fills/costs/restart semantics. Neither is represented by the current checklists. Do not add a live switch to this research core.

# Limitations and threat model

## What the release establishes

It checks supplied local evidence consistently and explains explicit uncertainty. A malicious or mistaken operator can provide fabricated facts, fake upstream names, mislabeled assets, incorrect market constraints and hashes of invented payloads. Passing the validator is not independent verification or financial due diligence. Operator-controlled `controls_reviewed` booleans are required attestations, not a security audit. Prompt text is not a permission system.

The engine can reject structural identity mismatches; it cannot prove that a venue symbol maps to the declared chain, that a contract is authentic, or that decimals match deployed bytecode. Case/spelling must be canonicalized by the operator. Lifecycle changes require a new reviewed snapshot; historical accounting is absent. No RPC finality or chain-reorg recovery is implemented.

## Technical boundaries

- The Python runtime never fetches URLs, calls a model, opens a socket, sends email, signs transactions or submits orders. Notes and source content stay inert; reports escape HTML and use a restrictive CSP. Tests exercise the actual evaluator/report path while forbidding socket/subprocess creation.
- The CLI accepts a **trusted operator-selected local input/output path**. It has normal filesystem permissions, not a filesystem sandbox. Do not expose it as a public file-processing service without an additional sandbox. Output symlink/concurrent-writer behavior and transactional durability across the two report files are not guaranteed.
- Size/nesting limits bound routine malformed data. They do not establish resistance to every memory/CPU denial of service or a formally audited parser. Do not run untrusted Python from a release you have not inspected.
- Provider URLs are descriptive metadata, not fetched or active hyperlinks in the report. The registry's reference links lead to third-party content with its own trust and terms.
- The surrounding Grok Bot can have tools and permissions unrelated to this core. A hostile web page, post, PDF or repository instruction can still attack that agent. The workflow tells it to ignore embedded instructions; actual tool containment must be enforced and tested by the host. No end-to-end prompt-injection immunity is claimed.

## Market and methodology limits

There is no account, live collection, financial ledger, trade manager, position sizing, next-bar fill, fee/spread/impact execution model, tax accounting, portfolio cap enforcement or drawdown kill switch. Restart tests establish repeatable local reports, not exactly-once trade accounting. Missing market constraints block research qualification; a constraint record does not imply that hypothetical orders can be filled.

Liquidity is a supplied book snapshot within 1% of midpoint. Orders can disappear, venues can fail, reported volume can be washed, and quotes can diverge. Stablecoins retain issuer/redemption/custodian risks even near USD 1. The supplied quote conversion and reserve review are not independently verified.

The category models are evidence checklists. Monetary assets and stablecoins abstain from corporate-style cash-flow valuation; network/DeFi/infrastructure tokens require explicit protocol versus holder economics. Token holders do not automatically own treasury assets, fees or protocol revenue. TVL is not revenue. Staking yield can come from dilution; protocol adoption need not accrue value to a token. Supply estimates, vesting schedules and holder concentration can be wrong. No yield, slashing, lockup, gas, MEV, bridge loss or LP impermanent-loss simulation is included.

Seven lenses do not vote and are not calibrated alpha signals. Thresholds are authored research policy assumptions without empirical evidence of return prediction. A documented review can still describe poor economics; qualification only establishes declared evidence completeness and specified risk checks. Opposing prose is preserved for a human, not classified by sentiment. A bearish view is not automatically resolved by a positive label.

## Performance and benchmarks

No financial backtest, audited returns, win rate, outperformance or original investment discovery is claimed. No benchmark returns are produced. Unit tests test software behavior, not investment performance.

A future simulator/backtest must compare point-in-time BTC and ETH buy-and-hold plus appropriate cash/quote exposure, with aligned timestamps, fees, drawdown, volatility, turnover and currency risk. It needs next-bar timing, realistic depth/impact, delistings, survivorship/look-ahead control, immutable availability timestamps, negative results and out-of-sample/walk-forward evaluation. Stops cannot guarantee a maximum loss. These are requirements for a future project, not capabilities of this release.

## Unverified launch conditions

Grok Bot skill saving/cloud execution/routines, real provider collection, real-market snapshots and hosted CI have not been tested. Source registry identities and docs were checked as references; X posts were not ingested and no personal track record was audited. No public repository exists for this release yet. Read [RELEASE.md](RELEASE.md) before publication.

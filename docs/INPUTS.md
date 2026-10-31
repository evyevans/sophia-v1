# Input contract v1

The executable validator is [contracts.py](../sophia/contracts.py) plus [core.py](../sophia/core.py). [input.schema.json](../input.schema.json) describes the structural contract; semantic checks (time, prices, lineage and risk) run in Python. The [synthetic example](../examples/synthetic.json) is the complete working shape. The evaluator does not collect or authenticate source data; the optional BTC collector is described in [LIVE.md](LIVE.md).

## Root and identity

Only `schema_version` (integer 1), `synthetic` (boolean), `asset`, `sources` and optional `notes` are accepted at the root. Monetary/quantity/ratio values use **plain decimal strings**, up to 30 integer and 18 fractional digits. Exponent notation, NaN, infinities, JSON floats, booleans pretending to be numbers and nonpositive prices are invalid. Counts such as decimals are bounded integers. CLI limit: 8 MB; bounded nesting and arrays; at most 40 source records. Duplicate JSON keys and duplicate source IDs are rejected.

`asset` requires `chain_id` (`namespace:reference`), `asset_id` (`native:ID`, `erc20:CONTRACT` or `token:ID`), `symbol`, `decimals`, `representation`, `category` and nonempty `provider_ids`. EVM ERC-20 contract IDs require a 40-hex address after `0x`. Identity is the exact chain ID + `/` + asset ID; provider mappings must be supplied and are not authenticated. Use a canonical address spelling consistently. A market matches this identity, decimals and representation exactly. The symbol is display-only.

Supported category strings: `monetary`, `l1_l2`, `defi`, `infrastructure`, `stablecoin`. Stablecoins qualify only as `COMPARISON_ONLY`. Other categories (including meme/microcap) block. Native/canonical representations may qualify; wrapped/bridged/liquid-staked representations explicitly block in this release, since their additional controls are not modeled. An ERC-20 token being accepted structurally does not mean its identity or code is safe.

## Every source

Required fields: `id`, `role` (`market` or `review`), `publisher`, `upstreams` (nonempty string array), `url`, `observed_at`, `published_at`, `available_at`, `retrieved_at`, `verification`, `units`, `coverage`, `redistribution`, `method_version`, `payload`, `content_sha256`.

All timestamps need explicit timezones and normalize to UTC. `observed_at <= available_at <= retrieved_at <= evaluation time`; `published_at <= available_at`, with no future timestamp. Publication dates are mandatory for evidence observations; use the time the original evidence became public, never the report generation date. Do not backdate availability.

`content_sha256` is SHA-256 over the UTF-8 encoding of Python's `json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)`. It covers the normalized payload, not the original HTTP response or a publisher signature. Preserve the original externally if needed; the program does not authenticate it. Metadata is also included in the result's full input hash.

Source URLs must be public HTTPS without credentials, queries, fragments or nonstandard ports. IP literals and local hostnames are rejected. The program does not fetch URLs, render them as active links, or follow redirects. Synthetic sources use `verification: synthetic`; real-mode sources must use `operator_attested`. `.invalid`/`.test` sources and demo identities cannot be relabeled as real. Operator metadata can still lie; no local string test establishes authenticity.

Market evidence must be at most **120 seconds old**; reviews at most **86,400 seconds old**. Evidence windows are authored policy assumptions, not validated investment thresholds. Eligible venue observations must be within **30 seconds** of one another. Two eligible venues must have **disjoint lineage sets including publisher, venue and every upstream**, compared case-insensitively. Naming another observation's publisher or venue as an upstream is dependence. This is a check on assertions, not independent proof of venue ownership or upstream independence.

## Market payload

Required: `asset_key`, `decimals`, `representation`, `venue`, `instrument: spot`, `status: online`, `quote`, `constraints`, `bids`, `asks`, `bars`.

`quote` requires its own `asset_key`, `symbol`, `kind` (`fiat` or `stablecoin`), `usd_rate`, `depeg` boolean and `issuer_risk_reviewed` boolean. Fiat must be exactly `fiat:USD`, `USD`, rate `1`. A stablecoin requires a distinct chain/asset identity and an explicit risk review. A declared depeg or more than 1% deviation from USD blocks. Quote risk remains in the report. Quote conversion is a supplied observation, not an FX or redemption guarantee.

`constraints` requires positive strings `price_tick`, `lot_step`, `min_notional`, from the actual venue/product. Missing constraints block. Lot steps and book quantities must be integer multiples of the asset base unit. Book prices/quantities must also align to the stated venue increments. Minimum notional is retained but no order or hypothetical fill is created, so no order size is tested against it.

`bids` and `asks` are nonempty arrays of `[price, base_quantity]` decimal strings, unique and sorted best-first. Crossed/locked books block. Spread must not exceed 50 bps of midpoint. Each side needs at least USD 10,000 of supplied depth **within 100 bps of midpoint**. Deep, distant orders do not count. Midpoints are compared in USD; disagreement over 100 bps relative to the lower midpoint blocks. This is displayed depth, not reliable executable liquidity, volume authenticity, or a model of fees/impact.

Each daily bar requires `open_at`, `close_at`, `available_at`, `complete`, `o`, `h`, `l`, `c`, `v`. Bars must cover consecutive UTC midnight-to-midnight days, including weekends; close/availability cannot exceed evaluation time or the containing source's retrieval time. Missing days, duplicate/out-of-order bars, inconsistent OHLC or incomplete candles block. At least 30 bars are required for SMA30. The latest close may be at most one day plus 300 seconds old. Annualized volatility is unavailable unless 366 consecutive closes establish 365 daily returns; that calculation uses sample standard deviation × sqrt(365). No annualization is inferred from an irregular sample. Trend context is not a timing strategy. Bars are supplied by the operator, not cross-verified here.

## Five review payloads

One eligible review per `economics`, `supply`, `security`, `adoption`, `macro` is required. Multiple eligible reviews for one lens block until explicitly reconciled. Every review has `asset_key`, `lens`, `assessment: documented`, a nonempty `method`, an array of `opposing_evidence`, and `facts`. Unknown/adverse assessment blocks. Opposing evidence is preserved for human interpretation; prose sentiment is not automatically parsed.

- Economics: `token_holder_rights`, `value_capture`, `protocol_fees_usd`, `protocol_revenue_usd`, `holder_revenue_usd`. The three amounts can be null for monetary/stablecoin categories; other categories require separate nonnegative values and holder revenue <= protocol revenue <= user fees. Supply and revenue do not establish ownership rights. Stablecoins also require `peg_usd`, `reserve_reviewed: true`, `redemption_controls`; >1% asset peg deviation blocks. Stablecoin comparison does not simulate reserve redemption.
- Supply: `circulating`, `total`, optional/null `max_supply`, `unlocks_30d`, `emissions_30d`, `burn_30d`, `insider_fraction` (0–1), `treasury_controls`, `vesting_controls`. Circulating cannot exceed total or total exceed a stated max. FDV is max supply × supplied USD midpoint when available; net issuance is emissions minus burns, separate from unlocks. No undisclosed unlocks or ownership concentration are inferred.
- Security: booleans `controls_reviewed`, `active_exploit`, `suspended`, `reorg_alert`; `lifecycle_status: active`; explicit `upgrade_controls`, `oracle_dependencies`, `bridge_dependencies`, `sequencer_dependencies`, `finality`, `counterparty_concentration`. Unknown critical controls block; an active exploit, reorg alert or suspension vetoes. Migration, fork, redenomination or delisting requires a new reviewed identity snapshot. No automatic historical reconciliation is included.
- Adoption: `adjustment_method`, nonnegative `adjusted_activity`, `wash_activity_reviewed: true`, `sybil_reviewed: true`. The adjustment is declared and must be reviewed; it is **not independently rerun**. Raw address counts are not proof of users.
- Macro: `regime`, `cycle_risks`, `quote_custody_reviewed: true`. Missing context blocks. The core does not infer a regime or forecast macro conditions.

The monetary checklist can abstain from revenue valuation; network/infrastructure/DeFi checklists require explicitly separated economics. This is category-specific evidence validation, not a complete valuation model for every protocol. Staking slashing/lockups, MEV, LP impermanent loss, gas and sequencer downtime need discussion where relevant; there are no position or cash-flow simulations for them.

## Output

JSON includes `status`, `mode`, `evidence_status`, `independently_verified: false`, `execution_enabled: false`, `dispatch_enabled: false`, UTC `as_of`, identity, original source payloads, input/policy hashes, explicit policy, markets, seven lenses, reason-coded `gates` and limitations. `QUALIFIED_RESEARCH` only means supplied inputs passed rules. `BLOCKED` includes unknown evidence and hard vetoes. `COMPARISON_ONLY` is restricted stablecoin exposure.

Top-level unknown fields such as an execution toggle are invalid. Free-text data cannot invoke tools. HTML escapes all source/notes content and does not load scripts. Input payload extensions are retained as data for evidence review; they are not instructions or extra features. The surrounding Bot is outside this enforcement boundary.

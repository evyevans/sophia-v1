# Floatglass Research

**Make crypto research evidence inspectable before trusting the narrative.**

Floatglass turns a local crypto snapshot into seven deterministic research lenses, explicit risk blockers, and an HTML/JSON evidence report. Built for a Grok Bot research workflow, with a Python core that runs independently of any model.

**Status: 0.2.0, local research edition.** No orders, wallets, leverage, simulated fills, portfolio ledger or financial performance claims. Opt-in BTC/USD public data collection is available; messaging adapters are absent. Real-mode evidence is **operator attested**, not independently verified.

## One useful first run

Requires Python 3.11 or newer. No packages, account, API key or network are needed. From this directory:

```sh
python3 -m floatglass demo
```

Open `demo-output/report.html`; inspect the complete evidence in `demo-output/results.json`.

```text
QUALIFIED_RESEARCH | SYNTHETIC | GLASS | execution disabled
BLOCKED            | SYNTHETIC | GLASS | execution disabled
BLOCKED            | SYNTHETIC | GLASS | execution disabled
```

The fixed scenarios demonstrate qualified research, stale evidence, and an active-exploit veto. The fictional asset, venues, prices and reviews are authored examples evaluated at **2026-10-25 00:01 UTC**. They are not observed market data or investment recommendations.

## What makes the checks useful

- Match assets by chain and native/contract ID, representation and decimals; never by ticker alone.
- Check declared source lineage, timestamps, payload hashes, venue spread, near-midpoint book depth and market constraints.
- Keep token-holder rights, supply dilution, security controls, adjusted adoption and macro context separate.
- Treat missing evidence as unknown or blocked; a model cannot vote away a hard veto.
- Retain opposing evidence, input and policy hashes, and source metadata in every result.
- Render untrusted notes as escaped text in a script-free local report.

The seven lenses are economics/value capture, supply/dilution, market structure, security/governance, adjusted adoption, macro/cycle risk, and technical context. They are checklists with applicability rules, **not simulated investors, forecasts, probability scores or audited strategies**.

The [investor research candidate review](docs/INVESTOR_RESEARCH.md) connects selected institutional methods to these lenses and identifies unverified claims. It does not rank traders or copy their positions.

## Evaluate supplied evidence

```sh
python3 -m floatglass evaluate examples/synthetic.json --as-of 2026-10-25T00:01:00Z
```

Omit `--as-of` to use current UTC. Historical evaluation only checks the supplied snapshot; it does not reconstruct point-in-time history. A completed evaluation exits 0 even when its result is BLOCKED; malformed input or IO failure exits 2. No failure silently falls back to synthetic data.

For real-mode inputs, start with [the input contract](docs/INPUTS.md). You must supply current evidence, correctly mapped venue assets, source lineage, book constraints, and all five dated review records. The evaluator does not fetch or authenticate them. The optional collector supplies market observations only; all five reviews remain operator responsibilities. A hash is an integrity check, not evidence that a publisher signed or endorsed the content. No current real-market qualification has been established in this release.

## Read-only real market run

```sh
python3 -B -m floatglass collect-btc --output live-output
```

This explicitly opts into six public GET requests for native BTC/USD metadata, daily bars and books. No credentials are used. A market-only run remains BLOCKED until the five required research reviews are supplied. See [live collection, saved receipts and observed validation](docs/LIVE.md).

## Use with Grok Bot

Follow [SETUP.md](SETUP.md), the [profile](agent/PROFILE.md) and the [skill source](skills/floatglass-research/SKILL.md). The workflow is designed around the official [skills and routines model](https://docs.x.ai/grok-bot/skills-routines-and-automations). It is a community workflow pack; no official affiliation, marketplace listing or completed Grok Bot acceptance run is claimed.

The core is offline. Real evidence gathering and Grok Bot access may require accounts, paid plans and separate permissions. [Source registry](docs/SOURCES.md) lists checked documentation, verified identity references and disabled integrations. X ingestion is disabled.

## Scope and limitations

Supported category checklists: monetary assets, L1/L2 networks, DeFi tokens, infrastructure tokens and stablecoin comparison exposure. Stablecoins never receive a growth-asset qualification. Wrapped, bridged and liquid-staked assets, meme/microcap categories and unknown categories are excluded in v0.1. This release does not estimate intrinsic token value or implement a general-purpose chain indexer.

Qualification means the supplied evidence passed explicit rules. It establishes no investment quality, audited security, reliable adoption adjustment, independent feed identity or executable liquidity. There is no trading simulator, backtest, alpha estimate, benchmark return or order route. [Limitations and threat model](docs/LIMITATIONS.md) describe what remains outside the technical boundary.

## Develop and inspect the release

```sh
python3 -m unittest discover -s tests -v
python3 tools/release.py check
```

[Architecture](docs/ARCHITECTURE.md) · [Migration decisions](docs/MIGRATION.md) · [Validation](docs/VALIDATION.md) · [Release checklist](docs/RELEASE.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [MIT license](LICENSE)

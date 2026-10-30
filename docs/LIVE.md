# Read-only BTC market collection — 0.2.0

This opt-in feature supersedes v0.1 statements that all data adapters are absent. The deterministic evaluator remains offline; only `collect-btc` performs network reads. There are no credentials, wallet functions, private API routes, orders, messaging or publishing.

```sh
python3 -B -m floatglass collect-btc --output live-output
```

Requires Internet access and HTTPS access to Coinbase Exchange and Kraken public APIs. No account/key or runtime packages are needed for these endpoints. Public access remains subject to provider terms, limits and regional availability; it does not grant permission to redistribute market datasets. The captured data stays in the selected local output directory and is excluded from release archives. No commercial analytics or X access is used.

The fixed six-URL allowlist covers product metadata, daily candles and L2 books for native BTC/USD on the two venues. The caller cannot choose a URL or product. Requests use GET, a research User-Agent, no authorization/cookies, no environment proxies, 15-second timeouts, a 4 MB response cap and no redirects. Failures are recorded without substituting synthetic data. There are no background retries or scheduled polling. HTTP Date is used as a conservative response observation timestamp; cache delay is checked by existing freshness gates. It is not an exchange-signed book timestamp or proof that every resting order is recent.

Coinbase `BTC-USD` and Kraken `XXBTZUSD` metadata must identify the expected base/quote. The mapping is restricted to native Bitcoin (genesis chain reference), eight decimals, fiat USD. No token, wrapped BTC, stablecoin, derivatives or arbitrary ticker mapping is supported. Quote convention assumes USD cash denomination; it does not eliminate venue custody risk.

Each book retains the best 100 levels per side for evaluation; full raw responses are saved in `capture.json` with endpoint, HTTP timestamp, retrieval timestamp and raw SHA-256. `snapshot.json` contains the normalized evidence; `results.json` and `report.html` contain the research result. Raw hashes and normalized payload hashes have distinct scopes. Decimal JSON strings are retained; unfinished daily candles are excluded. Candle availability is conservatively recorded at retrieval rather than inventing historical publication times. Missing venue constraints still block.

All collected sources remain labeled `operator_attested`: HTTPS fetching and response hashing do not independently authenticate chain mappings, liquidity quality or source truth. The collector does not fabricate the five required protocol/risk reviews. A market-only capture therefore returns BLOCKED, even when both markets pass. To evaluate complete research, separately prepare genuinely sourced, dated reviews under the input contract; do not fill unknown facts with positive defaults.

## Observed end-to-end run

On 2026-10-30 at **17:58:44 UTC (13:58:44 America/Toronto)**, the command captured all six responses with no acquisition failures, normalized both markets, evaluated the snapshot and wrote the HTML/JSON artifacts. The recorded run originally passed market gates; final review removed an unsupported automatic custody-review assertion, so the corrected replay includes QUOTE_RISK for both venues. Captured midpoints were Coinbase **USD 76,999.995** and Kraken **USD 77,014.95**. These are dated observations, not current prices or executable fills.

Final status: **BLOCKED / OPERATOR_ATTESTED**, for unreviewed USD custody exposure and five missing reviews: economics, supply, security, adjusted adoption and macro. Execution and dispatch were false. The first sandbox attempt had no network access; the authorized public GET run succeeded after network access was permitted. The first real capture exposed an oversized Coinbase book; limiting and explicitly labeling normalized coverage fixed that boundary without loosening the core limit.

Re-evaluate a retained snapshot at its saved `as_of` for reproducibility; current-time evaluation should block it once stale. Never reuse its old pass as a current market claim. No protocol qualification, investment recommendation or live trading capability was established.

Official references checked: [Coinbase book](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-book), [Kraken book](https://docs.kraken.com/api-reference/market-data/get-order-book), [Kraken candles](https://docs.kraken.com/api-reference/market-data/get-ohlc-data). Provider rights review remains required before any redistribution or commercial deployment.

## Final collector review

All metadata, candle and book receipt timestamps are now checked for ordering and a 120-second age bound at capture. The combined source uses the oldest component observation and retains component hashes/times; candle availability uses its own retrieval time. Malformed response shapes are contained as per-venue failures, preserving receipts without fallback. USD denomination no longer asserts issuer/custody review: the collector explicitly leaves that attestation false. The six original raw responses were replayed through the corrected adapter without new network access; the corrected report is BLOCKED with QUOTE_RISK for both venues, MISSING_MARKETS (fewer than two fully eligible markets), and five REVIEW_MISSING gates. This is an honest incomplete research run, not a fully qualified asset.

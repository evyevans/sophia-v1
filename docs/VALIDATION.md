# Validation

Run `python3 -B -m unittest discover -s tests -v` and `python3 -B tools/release.py check` from the project root. The tests cover asset identity, evidence timing and lineage, book depth, risk gates, local reports and release integrity. Tests do not establish investment performance or independently authenticate supplied facts.

The offline demo uses fictional evidence and writes local HTML and JSON. The optional BTC/USD collector uses public Coinbase and Kraken endpoints. Its documented historical run remains blocked because custody and research reviews are missing. See [LIVE.md](LIVE.md).

Grok Bot end-to-end acceptance and hosted CI remain unverified. Provider data rights and the security reporting channel require review before broader deployment.

# Contributing

Start with Python 3.11+ and `python3 -m unittest discover -s tests -v`. The runtime has no external packages. Run the demo and inspect its HTML and JSON. Before a release, run `python3 tools/release.py check`.

For a behavioral change, add a failing regression that demonstrates its user-visible consequence, implement the smallest supported fix, and run the full suite. Review identity, data availability, Decimal precision and fail-closed gates carefully. Include negative/unknown examples, not just an all-pass fixture.

Keep evidence collection separate from deterministic evaluation. Do not introduce provider datasets, scraped posts, credentials, personal information or historical private state. A future adapter needs explicit read-only endpoints, terms/license review, source identity, rate limits, timeouts and no synthetic fallback. Any execution simulator is a separate project with a ledger and financial-model validation.

Keep marketing and methodology claims within observed evidence. Do not add named-investor impersonation, fake endorsements, passing hosted-CI badges before hosted results, fabricated performance, follower rankings or growth promises. Changes to the allowlist require explicit file review and new hashes.

No public repository or contribution endpoint has been created for this release yet. After publication, use its actual issue/PR URLs. Until then, review locally with the person who supplied this artifact.

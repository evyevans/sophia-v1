# Release and publication boundary

Only this separate release folder or its allowlisted ZIP is a publication candidate. Do not publish the parent workspace, private audit files, reference project, source history or previous release archives.

## Reproduce the package

From this release root:

```sh
python3 -B -m unittest discover -s tests -v
python3 -B tools/release.py check
python3 -B tools/release.py archive --archive ../floatglass-research-0.1.0.zip
```

`ALLOWLIST.json` is the explicit list of reviewed distribution files. `RELEASE_FILES.json` hashes every other file, including the allowlist; its own bytes are covered by the ZIP checksum. After intentional content changes, inspect them, run `python3 -B tools/release.py manifest`, then rerun checks. A manifest proves byte identity, not that content is safe or correct.

The archive has fixed member timestamps and contains no metadata/history or generated reports. The archive and checksum must be outside the source tree so packaging cannot overwrite an approved input. The tool prints a SHA-256 and writes an adjacent `.zip.sha256` file. Extract into a fresh directory, repeat tests/demo/checks, and compare member names and hashes before distribution.

The built-in pattern checker detects selected credential formats, emails, local paths, private project endpoints, relationship terms, UTF-8/binary violations and broken local Markdown links. It is not an exhaustive secret detector. The release audit also uses a separate private exact-term list kept **outside** the artifact; do not commit that list or logs containing private values. A dedicated scanner must run on the exact extracted artifact. See [observed validation](VALIDATION.md).

## Publication gates

1. Complete a real Grok Bot one-time run, save the skill, inspect actual host permissions, and verify failure behavior. Routines remain opt-in and separately tested. No acceptance success is inferred from local unit tests.
2. Create a fresh repository only when the owner explicitly authorizes publication. Do not import private `.git` history or remotes. Enable and test private vulnerability reporting, then put its actual advisory URL in SECURITY.md.
3. Run hosted CI on the real repository and record actual results. The workflow uses read-only contents permission, disables checkout credential persistence, uses immutable action commits and has no deploy step or secrets. A local pass is not hosted CI evidence.
4. For real-data use, review provider terms, endpoint costs/limits, venue identity/constraints and dataset rights, then validate a fresh operator snapshot. Only the opt-in native BTC/USD collector is included; captured data is not redistributed. Kraken data-rights acceptance and all optional integration entitlements are unresolved; X ingestion remains disabled.
5. Review the exact final artifact after any new change. The source-reference registry expires and needs renewed identity/terms review. Name searches are a limited obvious-collision check, not domain reservation or trademark clearance.

There is no production-readiness, investment-performance or audit-certification claim. No push, publication, repository visibility change, announcement, recipient contact, wallet connection or financial action is part of this release preparation. [Announcement drafts](ANNOUNCEMENT.md) are unsent and must use the actual verified launch status.

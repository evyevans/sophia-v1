# Security reporting

This is a local research tool, not a trading or custody system. Never provide private keys, seed phrases, exchange write credentials, recipient lists or client data in snapshots or bug reports. Reports reproduce supplied evidence, so inspect them before sharing.

No public repository or security contact has been established for this release. A real private reporting channel is a **publication gate**: once a repository exists, the maintainer must enable GitHub private vulnerability reporting, verify that it works and replace this paragraph with the actual repository advisory link. No invented email address or placeholder reporting URL is supplied.

Before that channel exists, report a minimal synthetic reproduction privately to the maintainer through the channel that delivered this artifact. Do not disclose secrets or a live exploitable vulnerability publicly. If a secret is ever exposed, revoke/rotate it first; deleting a current file does not remove historical exposure.

See [the threat model](docs/LIMITATIONS.md). No independent security certification, complete prompt-injection containment or provider/authentication audit is claimed. Contributions should include regression tests for confirmed security boundary failures.

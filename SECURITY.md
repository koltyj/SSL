# Security Policy

## Supported Versions

Only the latest `0.1.x` release line is supported for security fixes.

## Report A Vulnerability

- Do not open a public issue for security-sensitive findings.
- Use GitHub private vulnerability reporting if it is enabled for this repository.
- If private reporting is unavailable, contact the maintainer through GitHub and request a private channel before sharing details.

Include:

- Affected version or commit
- Console model and firmware
- Network topology or assumptions required to reproduce
- Reproduction steps
- Expected impact

## Security Model

- This client is designed for a trusted local network connected to an SSL console.
- The underlying console protocol is UDP-based and does not provide application-layer authentication.
- Do not expose the control host or console network directly to the public internet.
- Keep packet captures, debug logs, and saved templates free of secrets or private studio metadata before sharing them.

## What To Expect

Maintainers will triage reports, confirm impact, and coordinate a fix or mitigation when the issue is reproducible and in scope.

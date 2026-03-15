# Contributing

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Validate Before Opening A PR

```bash
python3 -m ruff check ssl-matrix-client tests
python3 -m pytest -q
python3 -m build
```

## Change Scope

- Keep pull requests focused. Small protocol, CLI, TUI, and docs changes review faster than mixed refactors.
- Add or update tests for behavior changes. Protocol handlers, CLI parsing, template logic, and TUI state updates should all be covered.
- Do not commit packet captures, decompiled vendor code, local device addresses, secrets, or personal studio data.
- Update [CHANGELOG.md](CHANGELOG.md) when the user-visible behavior changes.

## Bug Reports

Include this context when relevant:

- Console model and firmware
- Operating system and Python version
- Exact command or workflow used
- Expected behavior vs actual behavior
- Verbose logs if available: `ssl-console -v ...`

## Hardware-Specific Changes

- Mark live-hardware validation clearly when a change was only tested against a specific console or firmware.
- Avoid claiming compatibility for unverified firmware revisions or console families.

## Community

By participating, you agree to follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

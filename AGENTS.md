# AGENTS.md

## Cursor Cloud specific instructions

This is a pure-Python UDP client for SSL Matrix mixing consoles. No external services, databases, or Docker containers are needed.

### Running commands

`ruff` and `pre-commit` are installed as user-site packages and may not be on `$PATH`. Use `python3 -m ruff` and `python3 -m pre_commit` instead of bare `ruff` / `pre-commit`.

### Development commands

See `CLAUDE.md` and `README.md` for full details. Quick reference:

- **Tests:** `python3 -m pytest tests/ -v` (264 pass, 10 TUI stubs skipped; all offline, no hardware needed)
- **Lint:** `python3 -m ruff check ssl-matrix-client/ tests/`
- **Format check:** `python3 -m ruff format --check ssl-matrix-client/ tests/`
- **Pre-commit:** `python3 -m pre_commit run --all-files`

### Application

- **CLI:** `python3 -m ssl-matrix-client --help` (works offline)
- **TUI:** `python3 -m ssl-matrix-client tui` (launches Textual dashboard; shows "Connecting..." without hardware — this is expected)
- **REPL:** `python3 -m ssl-matrix-client` (interactive; blocks waiting for input)

Live end-to-end testing requires a physical SSL Matrix console on `192.168.1.2:50081/udp`. All unit tests mock the protocol layer and run fully offline.

### Import quirk

The package directory is hyphenated (`ssl-matrix-client/`). Tests use an import shim in `tests/conftest.py` so modules can be imported as `ssl_matrix_client.*`. Outside the test runner, use `importlib.import_module("ssl-matrix-client")`.

### Pre-commit hooks

On fresh clones, `git config --unset-all core.hooksPath` may be needed before `python3 -m pre_commit install` will succeed (Cursor Cloud sets a global hooks path).

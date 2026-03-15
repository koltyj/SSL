# Support

## Usage Questions

Use GitHub Discussions if available. If not, open an issue and mark it as a usage question rather than a bug report.

## Bug Reports

Please include:

- Console model
- Firmware version
- Operating system
- Python version
- Exact command or TUI workflow
- Logs or traceback output
- Whether the problem reproduces consistently

## Before Reporting

Try these first:

- `ssl-console status`
- `ssl-console health`
- `ssl-console -v <command>`
- `python3 -m pytest -q`

## Known Limits

- The project has been validated primarily against SSL Matrix firmware `V3.0/5`.
- Other SSL console families are supported at the protocol layer but may still need hardware confirmation for every feature.
- Network control assumes a direct or trusted LAN connection to the console.

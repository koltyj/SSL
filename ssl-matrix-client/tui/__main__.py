"""Entry point: python3 -m ssl_matrix_client.tui [--ip IP] [--port PORT]"""

import argparse
import logging
import sys

from .app import SSLMatrixApp


def main():
    parser = argparse.ArgumentParser(description="SSL Matrix TUI Dashboard")
    parser.add_argument("--ip", default="192.168.1.2", help="Console IP (default: 192.168.1.2)")
    parser.add_argument("--port", type=int, default=50081, help="UDP port (default: 50081)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging to file")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(
            filename="ssl-tui.log",
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )

    app = SSLMatrixApp(console_ip=args.ip, console_port=args.port)
    app.run()


if __name__ == "__main__":
    main()

"""Allow running as: python3 -m ssl-matrix-client"""

import sys

if len(sys.argv) > 1 and sys.argv[1] == "tui":
    from .tui import main as tui_main

    tui_main(sys.argv[2:])
else:
    from .cli import main

    main()

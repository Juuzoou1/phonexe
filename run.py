"""
PyInstaller entry point for the phonexe executable.

Double-clicking the built phonexe.exe (no arguments) launches the desktop
GUI. Passing CLI arguments (e.g. `phonexe.exe analyze <backup>`) runs the
command-line interface instead.
"""

import sys


def main() -> int:
    if len(sys.argv) > 1:
        from phonexe.cli import main as cli_main
        return cli_main()
    try:
        from phonexe.gui.app import run as run_gui
        return run_gui()
    except ImportError:
        # No GUI toolkit available — fall back to CLI help.
        from phonexe.cli import main as cli_main
        return cli_main(["--help"])


if __name__ == "__main__":
    raise SystemExit(main())

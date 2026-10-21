"""Run the fixed EngineeringRules documentation checker without changing the kit."""

import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TOOL_VERSION = "0.1.8"
TOOL_REVISION = "c535a2745b8b436a5a9d4d0598192aa106912fee"
TOOL_ROOT = Path.home() / ".local/share/engineering-rules" / TOOL_VERSION
CHECKER_PATH = "Scripts/check-docs.py"


def git_output(*arguments):
    return subprocess.check_output(
        ["git", "-C", str(TOOL_ROOT), *arguments],
        stderr=subprocess.PIPE,
        timeout=10,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    options = parser.parse_args()
    try:
        revision = git_output("rev-parse", "HEAD").decode().strip()
        if revision != TOOL_REVISION:
            raise ValueError(
                "EngineeringRules checkout must be at " + TOOL_REVISION + "; found " + revision
            )
        checker = TOOL_ROOT / CHECKER_PATH
        if checker.read_bytes() != git_output("show", TOOL_REVISION + ":" + CHECKER_PATH):
            raise ValueError("Installed documentation checker differs from the pinned revision")
        python = TOOL_ROOT / ".build/docs-venv/bin/python"
        return subprocess.run(
            [str(python), "-B", str(checker), "--root", str(ROOT), "--format", options.format],
            check=False,
            timeout=60,
        ).returncode
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        message = "Cannot run pinned EngineeringRules " + TOOL_VERSION + ": " + str(error)
        if options.format == "json":
            print(json.dumps({"findings": [], "error": message}))
        else:
            print("documentation-rules: " + message, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

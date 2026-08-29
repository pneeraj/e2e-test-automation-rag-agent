"""
Thin orchestrator around the Playwright CLI.

Why this exists instead of just calling `npx playwright test` from Jenkins
directly: Jenkins (or any CI) needs one command that runs every suite, keeps
going even if one suite fails so all reports still get produced, and returns
a single non-zero exit code only at the end. Doing that logic in Groovy is
painful; doing it in a few lines of Python is not.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SUITES = {
    "ui": ["ui-chrome"],
    "api": ["api"],
    "mobile": ["mobile-chrome", "mobile-safari"],
}


def run_suite(projects: list[str]) -> int:
    # shutil.which resolves npx.cmd on Windows so shell=True isn't needed
    npx = shutil.which("npx") or "npx"
    cmd = [npx, "playwright", "test"]
    for project in projects:
        cmd += ["--project", project]

    print(f"\n$ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one or more Playwright suites.")
    parser.add_argument(
        "--suite",
        choices=[*SUITES.keys(), "all"],
        default="all",
        help="Which suite to run (default: all)",
    )
    args = parser.parse_args()

    suites_to_run = list(SUITES.keys()) if args.suite == "all" else [args.suite]

    failures = []
    for suite_name in suites_to_run:
        exit_code = run_suite(SUITES[suite_name])
        if exit_code != 0:
            failures.append(suite_name)

    if failures:
        print(f"\nSuite(s) with failures: {', '.join(failures)}", file=sys.stderr)
        return 1

    print("\nAll suites passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

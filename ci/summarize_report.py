"""
Reads the Playwright JSON reporter output (test-results/results.json) and
prints a short pass/fail summary for the Jenkins console log, plus writes
test-results/failures.json - a flattened list the RAG defect agent consumes
so it doesn't have to know anything about Playwright's report schema.
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_FILE = REPO_ROOT / "test-results" / "results.json"
FAILURES_FILE = REPO_ROOT / "test-results" / "failures.json"

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub("", text)


def flatten_specs(suites, file_path_prefix=""):
    for suite in suites:
        file_path = suite.get("file", file_path_prefix)
        for spec in suite.get("specs", []):
            yield file_path, spec
        yield from flatten_specs(suite.get("suites", []), file_path)


def main() -> int:
    if not RESULTS_FILE.exists():
        print(f"No report found at {RESULTS_FILE}, nothing to summarize.")
        return 0

    report = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))

    total = passed = failed = flaky = 0
    failures = []

    for file_path, spec in flatten_specs(report.get("suites", [])):
        for test in spec.get("tests", []):
            total += 1
            status = test.get("status")
            if status == "expected":
                passed += 1
            elif status == "flaky":
                flaky += 1
            else:
                failed += 1
                last_result = test["results"][-1] if test.get("results") else {}
                error = (last_result.get("error") or {}).get("message", "unknown error")
                failures.append(
                    {
                        "file": file_path,
                        "title": spec.get("title"),
                        "project": test.get("projectName"),
                        "error": strip_ansi(error),
                    }
                )

    print(f"Total: {total}  Passed: {passed}  Flaky: {flaky}  Failed: {failed}")

    FAILURES_FILE.write_text(json.dumps(failures, indent=2), encoding="utf-8")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

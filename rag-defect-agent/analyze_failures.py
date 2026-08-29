"""
Reads the failed-test details produced by ci/summarize_report.py, retrieves
similar past-incident notes from the local knowledge base (RAG), asks an LLM
to draft a root-cause hypothesis, and files (or prints, in dry-run) one Jira
defect per failure.

Usage:
    python analyze_failures.py            # respects RAG_DRY_RUN from .env
    RAG_DRY_RUN=false python analyze_failures.py   # actually files in Jira
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ingest import load_or_build_vector_store
from jira_mcp_client import JiraDefectClient, JiraIssueDraft

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

FAILURES_FILE = REPO_ROOT / "test-results" / "failures.json"

TRIAGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a senior SDET triaging a failing automated test. Use the "
            "reference notes only if they're actually relevant - don't force a "
            "match. Be specific and concise, this goes straight into a Jira ticket.",
        ),
        (
            "human",
            """Failing test: {title}
File: {file}
Project/browser: {project}

Error:
{error}

Reference notes from the team's known-issues log:
{context}

Reply with strict JSON only, no markdown fences, using keys:
summary (<=120 chars), root_cause (2-4 sentences), next_step (one concrete action).""",
        ),
    ]
)


def build_description(failure: dict, root_cause: str, next_step: str) -> str:
    return (
        f"Test: {failure['title']}\n"
        f"File: {failure['file']}\n"
        f"Project: {failure.get('project', 'unknown')}\n\n"
        f"Error:\n{failure['error']}\n\n"
        f"Root cause (AI-assisted draft - verify before acting):\n{root_cause}\n\n"
        f"Suggested next step:\n{next_step}"
    )


def main() -> None:
    if not FAILURES_FILE.exists():
        print(f"No report at {FAILURES_FILE}. Run ci/summarize_report.py first.")
        return

    failures = json.loads(FAILURES_FILE.read_text(encoding="utf-8"))
    if not failures:
        print("No failures to triage.")
        return

    vector_store = load_or_build_vector_store()
    llm = ChatOpenAI(model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    chain = TRIAGE_PROMPT | llm

    dry_run = os.environ.get("RAG_DRY_RUN", "true").lower() == "true"
    jira_client = None if dry_run else JiraDefectClient()

    for failure in failures:
        related_docs = vector_store.similarity_search(failure["error"], k=2)
        context = "\n---\n".join(doc.page_content for doc in related_docs) or "No matching notes."

        response = chain.invoke(
            {
                "title": failure["title"],
                "file": failure["file"],
                "project": failure.get("project", "unknown"),
                "error": failure["error"],
                "context": context,
            }
        )

        try:
            parsed = json.loads(response.content)
        except (json.JSONDecodeError, TypeError):
            parsed = {"summary": failure["title"][:120], "root_cause": response.content, "next_step": "Review manually."}

        description = build_description(failure, parsed.get("root_cause", ""), parsed.get("next_step", ""))
        draft = JiraIssueDraft(
            summary=f"[Automated triage] {parsed.get('summary', failure['title'])[:110]}",
            description=description,
        )

        if dry_run:
            print("\n--- DRY RUN: would file this Jira defect ---")
            print(f"Summary: {draft.summary}\n{description}")
        else:
            issue_key = jira_client.file_defect(draft)
            print(f"Filed {issue_key}: {draft.summary}")


if __name__ == "__main__":
    main()

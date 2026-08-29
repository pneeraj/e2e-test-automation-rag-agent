"""
Talks to Jira through the mcp-atlassian MCP server
(https://github.com/sooperset/mcp-atlassian) when it's available, and falls
back to a plain Jira REST call otherwise so the defect agent still works
before anyone has an MCP server wired up.

The tool name/arguments used below (`jira_create_issue`) match mcp-atlassian
as of writing. On a different Jira MCP server, adjust CREATE_ISSUE_TOOL and
the argument mapping in `_file_via_mcp`.
"""
import asyncio
import os
import re
from dataclasses import dataclass, field

import requests
from requests.auth import HTTPBasicAuth

CREATE_ISSUE_TOOL = "jira_create_issue"


@dataclass
class JiraIssueDraft:
    summary: str
    description: str
    issue_type: str = "Bug"
    labels: tuple[str, ...] = field(default_factory=lambda: ("automated-triage",))


class JiraDefectClient:
    def __init__(self):
        self.base_url = os.environ["JIRA_BASE_URL"].rstrip("/")
        self.email = os.environ["JIRA_EMAIL"]
        self.api_token = os.environ["JIRA_API_TOKEN"]
        self.project_key = os.environ.get("JIRA_PROJECT_KEY", "QA")
        self.mcp_command = os.environ.get("JIRA_MCP_COMMAND", "uvx")
        self.mcp_args = os.environ.get("JIRA_MCP_ARGS", "mcp-atlassian").split()

    def file_defect(self, draft: JiraIssueDraft) -> str:
        """Returns the created issue key, e.g. 'QA-123'."""
        try:
            return asyncio.run(self._file_via_mcp(draft))
        except Exception as mcp_error:  # server not installed / not reachable
            print(f"[jira] MCP path unavailable ({mcp_error}), falling back to REST API")
            return self._file_via_rest(draft)

    async def _file_via_mcp(self, draft: JiraIssueDraft) -> str:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=self.mcp_command,
            args=self.mcp_args,
            env={
                "JIRA_URL": self.base_url,
                "JIRA_USERNAME": self.email,
                "JIRA_API_TOKEN": self.api_token,
            },
        )

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    CREATE_ISSUE_TOOL,
                    arguments={
                        "project_key": self.project_key,
                        "summary": draft.summary,
                        "description": draft.description,
                        "issue_type": draft.issue_type,
                    },
                )
                text = result.content[0].text if result.content else ""
                return _extract_issue_key(text)

    def _file_via_rest(self, draft: JiraIssueDraft) -> str:
        response = requests.post(
            f"{self.base_url}/rest/api/3/issue",
            auth=HTTPBasicAuth(self.email, self.api_token),
            json={
                "fields": {
                    "project": {"key": self.project_key},
                    "summary": draft.summary,
                    "issuetype": {"name": draft.issue_type},
                    "labels": list(draft.labels),
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {"type": "paragraph", "content": [{"type": "text", "text": draft.description}]}
                        ],
                    },
                }
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json()["key"]


def _extract_issue_key(text: str) -> str:
    match = re.search(r"[A-Z][A-Z0-9]+-\d+", text)
    return match.group(0) if match else text

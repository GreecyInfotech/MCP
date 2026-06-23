"""GitHub MCP server — repos, PRs, issues, and code search."""

from __future__ import annotations

import base64

from github import Github
from mcp.server.fastmcp import FastMCP

from eai_platform.config import get_settings
from eai_platform.mcp_base import error_result, text_result

mcp = FastMCP(
    "github",
    instructions=(
        "GitHub integration for repository management, pull requests, "
        "issues, and code search."
    ),
)


def _get_client() -> Github:
    settings = get_settings()
    if not settings.github_token:
        raise ValueError("GITHUB_TOKEN must be configured")
    return Github(settings.github_token)


@mcp.tool()
def list_repos(org: str = "", per_page: int = 30) -> str:
    """List repositories for an organization or authenticated user."""
    try:
        client = _get_client()
        settings = get_settings()
        target = org or settings.github_org
        if target:
            repos = client.get_organization(target).get_repos()
        else:
            repos = client.get_user().get_repos()
        result = [
            {
                "name": r.name,
                "full_name": r.full_name,
                "description": r.description,
                "language": r.language,
                "stars": r.stargazers_count,
                "default_branch": r.default_branch,
            }
            for i, r in enumerate(repos)
            if i < per_page
        ]
        return text_result({"repos": result})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def search_code(query: str, repo: str = "", per_page: int = 20) -> str:
    """Search code across GitHub (optionally scoped to owner/repo)."""
    try:
        client = _get_client()
        q = query if not repo else f"{query} repo:{repo}"
        results = client.search_code(q)
        items = [
            {
                "name": r.name,
                "path": r.path,
                "repository": r.repository.full_name,
                "url": r.html_url,
            }
            for i, r in enumerate(results)
            if i < per_page
        ]
        return text_result({"results": items})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def list_pull_requests(repo: str, state: str = "open", per_page: int = 20) -> str:
    """List pull requests for a repository (state: open, closed, all)."""
    try:
        client = _get_client()
        repository = client.get_repo(repo)
        prs = repository.get_pulls(state=state)
        result = [
            {
                "number": pr.number,
                "title": pr.title,
                "author": pr.user.login,
                "state": pr.state,
                "created_at": str(pr.created_at),
                "url": pr.html_url,
            }
            for i, pr in enumerate(prs)
            if i < per_page
        ]
        return text_result({"pull_requests": result})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def get_pull_request(repo: str, pr_number: int) -> str:
    """Get details for a specific pull request."""
    try:
        client = _get_client()
        pr = client.get_repo(repo).get_pull(pr_number)
        return text_result(
            {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "author": pr.user.login,
                "base": pr.base.ref,
                "head": pr.head.ref,
                "mergeable": pr.mergeable,
                "changed_files": pr.changed_files,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "url": pr.html_url,
            }
        )
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def create_issue(repo: str, title: str, body: str, labels: str = "") -> str:
    """Create a GitHub issue. Labels is a comma-separated string."""
    try:
        client = _get_client()
        label_list = [label.strip() for label in labels.split(",") if label.strip()] if labels else []
        issue = client.get_repo(repo).create_issue(title=title, body=body, labels=label_list)
        return text_result({"created": True, "number": issue.number, "url": issue.html_url})
    except Exception as exc:
        return error_result(str(exc))


@mcp.tool()
def get_file_contents(repo: str, path: str, ref: str = "main") -> str:
    """Get the contents of a file from a repository."""
    try:
        client = _get_client()
        content = client.get_repo(repo).get_contents(path, ref=ref)
        if isinstance(content, list):
            return text_result({"type": "directory", "entries": [c.path for c in content]})
        decoded = base64.b64decode(content.content).decode("utf-8", errors="replace")
        return text_result({"path": path, "sha": content.sha, "content": decoded})
    except Exception as exc:
        return error_result(str(exc))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

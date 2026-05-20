import base64
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv


BASE_URL = "https://api.github.com"
GSSOC_API_URL = "https://gssoc.girlscript.org/api/projects"


class GitHubClientError(Exception):
    pass


def _load_token(token: Optional[str] = None) -> str:
    if token:
        return token

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubClientError("GitHub token missing in .env")

    return token


def _github_get(path: str, token: Optional[str] = None, params: Optional[Dict] = None):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {_load_token(token)}",
        "User-Agent": "GitScout-AI",
    }

    response = requests.get(
        f"{BASE_URL}{path}",
        headers=headers,
        params=params,
        timeout=20,
    )

    if response.status_code == 401:
        raise GitHubClientError("Invalid GitHub token.")

    if response.status_code == 403:
        raise GitHubClientError("GitHub rate limit exceeded.")

    if not response.ok:
        raise GitHubClientError(
            f"GitHub API error {response.status_code}: {response.text[:200]}"
        )

    return response.json()


def extract_repo_full_name(repo_url: str) -> str:
    if not repo_url:
        return ""

    match = re.search(r"github\.com/([^/]+/[^/#?]+)", repo_url)

    if match:
        return match.group(1).replace(".git", "").strip("/")

    if "/" in repo_url and " " not in repo_url:
        return repo_url.replace(".git", "").strip("/")

    return ""


def _decode_readme(content: Dict) -> str:
    try:
        return base64.b64decode(content.get("content", "")).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _normalize_issue(issue: Dict) -> Dict:
    labels = [label.get("name", "").lower() for label in issue.get("labels", [])]

    return {
        "id": issue.get("id"),
        "number": issue.get("number"),
        "title": issue.get("title", ""),
        "body": issue.get("body") or "",
        "url": issue.get("html_url", ""),
        "comments": issue.get("comments", 0),
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
        "state": issue.get("state", "open"),
        "assignee": issue.get("assignee", {}).get("login") if issue.get("assignee") else None,
        "labels": labels,
        "good_first_issue": "good first issue" in labels,
        "help_wanted": "help wanted" in labels,
        "pull_request": "pull_request" in issue,
    }


def _normalize_repo_metadata(repo: Dict) -> Dict:
    return {
        "name": repo.get("full_name", ""),
        "url": repo.get("html_url", ""),
        "description": repo.get("description") or "",
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "language": repo.get("language") or "",
        "open_issues_count": repo.get("open_issues_count", 0),
        "updated_at": repo.get("updated_at"),
        "topics": repo.get("topics", []),
    }


def _normalize_gssoc_project(item: Dict) -> Dict:
    repo_url = (
        item.get("repo_url")
        or item.get("repository")
        or item.get("github_url")
        or item.get("github")
        or item.get("url")
        or ""
    )

    tech_stack = (
        item.get("tech_stack")
        or item.get("techStack")
        or item.get("technologies")
        or item.get("tags")
        or []
    )

    if isinstance(tech_stack, str):
        tech_stack = [tech_stack]

    name = (
        item.get("name")
        or item.get("project_name")
        or item.get("title")
        or "Unknown Project"
    )

    difficulty = (
        item.get("difficulty")
        or item.get("level")
        or item.get("project_difficulty")
        or ""
    )

    return {
        "id": item.get("id"),
        "name": name,
        "description": item.get("description", ""),
        "url": repo_url,
        "repo_url": repo_url,
        "repo_full_name": extract_repo_full_name(repo_url),
        "language": item.get("language", ""),
        "tech_stack": tech_stack,
        "difficulty": difficulty,
        "category": item.get("category", ""),
        "good_first_issues": item.get("good_first_issues", item.get("good_first_issue_count", 0)),
        "open_issues": item.get("open_issues", item.get("open_issues_count", 0)),
        "stars": item.get("stars", 0),
        "forks": item.get("forks", 0),
        "admin": item.get("admin") or item.get("admin_name") or item.get("mentor") or "",
        "updated_at": item.get("updated_at", ""),
        "is_gssoc": True,
    }


def fetch_gssoc_projects() -> List[Dict]:
    response = requests.get(GSSOC_API_URL, timeout=20)

    if not response.ok:
        raise GitHubClientError(f"Could not load GSSoC projects: {response.status_code}")

    try:
        data = response.json()
    except ValueError:
        raise GitHubClientError("GSSoC response is not valid JSON.")

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("projects") or data.get("data") or data.get("items") or []
    else:
        items = []

    if not isinstance(items, list):
        raise GitHubClientError("GSSoC project format not recognized.")

    projects = [_normalize_gssoc_project(item) for item in items]
    return [p for p in projects if p.get("name")]


def get_repository_metadata(full_name: str, token: Optional[str] = None) -> Dict:
    if not full_name:
        return {}

    repo = _github_get(f"/repos/{full_name}", token=token)
    return _normalize_repo_metadata(repo)


def get_repository_readme(full_name: str, token: Optional[str] = None) -> str:
    if not full_name:
        return ""

    try:
        content = _github_get(f"/repos/{full_name}/readme", token=token)
        return _decode_readme(content)
    except GitHubClientError:
        return ""


def fetch_open_issues(
    full_name: str,
    token: Optional[str] = None,
    per_page: int = 100,
) -> List[Dict]:
    if not full_name:
        return []

    params = {
        "state": "open",
        "per_page": per_page,
        "sort": "created",
        "direction": "desc",
    }

    issues = _github_get(
        f"/repos/{full_name}/issues",
        token=token,
        params=params,
    )

    return [
        _normalize_issue(issue)
        for issue in issues
        if not issue.get("pull_request")
    ]


def get_gssoc_filter_options() -> Dict[str, List[str]]:
    projects = fetch_gssoc_projects()

    tech_stacks = set()
    languages = set()
    difficulties = set()

    language_like = {
        "python", "javascript", "typescript", "java", "c++", "c",
        "c#", "go", "golang", "rust", "php", "ruby", "kotlin",
        "swift", "dart", "r", "scala", "html", "css", "sql"
    }

    for project in projects:
        for tech in project.get("tech_stack", []):
            if not tech:
                continue

            tech_stacks.add(tech)

            if tech.lower().strip() in language_like:
                languages.add(tech)

        if project.get("language"):
            languages.add(project["language"])

        if project.get("difficulty"):
            difficulties.add(project["difficulty"])

    return {
        "tech_stacks": sorted(tech_stacks),
        "languages": sorted(languages),
        "difficulties": sorted(difficulties),
    }


def search_gssoc_projects(
    keywords: Optional[str] = None,
    tech_stack: Optional[str] = None,
    language: Optional[str] = None,
    difficulty: Optional[str] = None,
    sort_by: str = "Most Open Issues",
) -> List[Dict]:
    projects = fetch_gssoc_projects()
    filtered = []

    for project in projects:
        techs = [str(t).lower() for t in project.get("tech_stack", [])]

        text_blob = " ".join([
            project.get("name", ""),
            project.get("description", ""),
            project.get("admin", ""),
            project.get("language", ""),
            project.get("difficulty", ""),
            " ".join(project.get("tech_stack", [])),
        ]).lower()

        if keywords and keywords.lower().strip() not in text_blob:
            continue

        if tech_stack and tech_stack.lower() not in techs:
            continue

        if language:
            lang = language.lower()
            project_lang = project.get("language", "").lower()

            if lang != project_lang and lang not in techs:
                continue

        if difficulty:
            if difficulty.lower() not in project.get("difficulty", "").lower():
                continue

        filtered.append(project)

    if sort_by == "Most Good First Issues":
        filtered.sort(key=lambda x: x.get("good_first_issues", 0), reverse=True)
    elif sort_by == "Most Open Issues":
        filtered.sort(key=lambda x: x.get("open_issues", 0), reverse=True)
    elif sort_by == "Beginner Friendly First":
        filtered.sort(
            key=lambda x: (
                "beginner" in x.get("difficulty", "").lower(),
                x.get("good_first_issues", 0),
            ),
            reverse=True,
        )
    elif sort_by == "Name A-Z":
        filtered.sort(key=lambda x: x.get("name", "").lower())

    return filtered[:18]
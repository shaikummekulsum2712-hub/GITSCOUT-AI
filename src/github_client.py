import base64
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv


BASE_URL = "https://api.github.com"
GSSOC_API_URL = "https://gssoc.girlscript.org/api/projects"


class GitHubClientError(Exception):
    pass


def _load_token(token: Optional[str] = None) -> Optional[str]:
    """Load GitHub token if available.

    The app can still work without a token for public repos, but a token gives
    higher rate limits. This avoids crashing just because GITHUB_TOKEN is absent.
    """
    if token:
        return token

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    return os.getenv("GITHUB_TOKEN")


def _github_get(path: str, token: Optional[str] = None, params: Optional[Dict] = None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GitScout-AI",
    }

    loaded_token = _load_token(token)
    if loaded_token:
        headers["Authorization"] = f"Bearer {loaded_token}"

    response = requests.get(
        f"{BASE_URL}{path}",
        headers=headers,
        params=params,
        timeout=25,
    )

    if response.status_code == 401:
        raise GitHubClientError("Invalid GitHub token.")

    if response.status_code == 403:
        message = response.text[:250]
        raise GitHubClientError(f"GitHub rate limit or permission issue: {message}")

    if not response.ok:
        raise GitHubClientError(
            f"GitHub API error {response.status_code}: {response.text[:250]}"
        )

    return response.json()


def extract_repo_full_name(repo_url: str) -> str:
    if not repo_url:
        return ""

    repo_url = repo_url.strip()

    match = re.search(r"github\.com/([^/\s]+/[^/#?\s]+)", repo_url)
    if match:
        return match.group(1).replace(".git", "").strip("/")

    if re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", repo_url):
        return repo_url.replace(".git", "").strip("/")

    return ""


def _decode_readme(content: Dict) -> str:
    try:
        return base64.b64decode(content.get("content", "")).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _normalize_label(label: Any) -> str:
    if isinstance(label, dict):
        return str(label.get("name", "")).strip().lower()
    return str(label).strip().lower()


def _normalize_issue(issue: Dict) -> Dict:
    labels = [_normalize_label(label) for label in issue.get("labels", []) if _normalize_label(label)]

    return {
        "id": issue.get("id"),
        "number": issue.get("number"),
        "title": issue.get("title", "") or "",
        "body": issue.get("body") or "",
        "url": issue.get("html_url", "") or "",
        "api_url": issue.get("url", "") or "",
        "comments": issue.get("comments", 0) or 0,
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
        "state": issue.get("state", "open"),
        "assignee": issue.get("assignee", {}).get("login") if issue.get("assignee") else None,
        "labels": labels,
        "good_first_issue": "good first issue" in labels,
        "help_wanted": "help wanted" in labels,
        "pull_request": "pull_request" in issue,
    }


def _normalize_comment(comment: Dict) -> Dict:
    user = comment.get("user") or {}
    return {
        "user": user.get("login", "unknown"),
        "body": comment.get("body") or "",
        "created_at": comment.get("created_at"),
        "updated_at": comment.get("updated_at"),
        "url": comment.get("html_url", ""),
    }


def _normalize_repo_metadata(repo: Dict) -> Dict:
    return {
        "name": repo.get("full_name", ""),
        "full_name": repo.get("full_name", ""),
        "url": repo.get("html_url", ""),
        "repo_url": repo.get("html_url", ""),
        "description": repo.get("description") or "",
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "language": repo.get("language") or "",
        "open_issues_count": repo.get("open_issues_count", 0),
        "updated_at": repo.get("updated_at"),
        "topics": repo.get("topics", []),
        "default_branch": repo.get("default_branch", "main"),
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
        tech_stack = [part.strip() for part in tech_stack.split(",") if part.strip()]

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
        "description": item.get("description", "") or "",
        "url": repo_url,
        "repo_url": repo_url,
        "repo_full_name": extract_repo_full_name(repo_url),
        "language": item.get("language", "") or "",
        "tech_stack": tech_stack or [],
        "difficulty": difficulty,
        "category": item.get("category", "") or "",
        "good_first_issues": item.get("good_first_issues", item.get("good_first_issue_count", 0)) or 0,
        "open_issues": item.get("open_issues", item.get("open_issues_count", 0)) or 0,
        "stars": item.get("stars", 0) or 0,
        "forks": item.get("forks", 0) or 0,
        "admin": item.get("admin") or item.get("admin_name") or item.get("mentor") or "",
        "updated_at": item.get("updated_at", "") or "",
        "is_gssoc": True,
    }


def fetch_gssoc_projects() -> List[Dict]:
    response = requests.get(GSSOC_API_URL, timeout=25)

    if not response.ok:
        raise GitHubClientError(f"Could not load GSSoC projects: {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        raise GitHubClientError("GSSoC response is not valid JSON.") from exc

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("projects") or data.get("data") or data.get("items") or []
    else:
        items = []

    if not isinstance(items, list):
        raise GitHubClientError("GSSoC project format not recognized.")

    projects = [_normalize_gssoc_project(item) for item in items if isinstance(item, dict)]
    return [project for project in projects if project.get("name")]


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
        if isinstance(issue, dict) and not issue.get("pull_request")
    ]


def fetch_issue_comments(
    full_name: str,
    issue_number: int,
    token: Optional[str] = None,
    max_comments: int = 5,
) -> List[Dict]:
    if not full_name or not issue_number:
        return []

    comments = _github_get(
        f"/repos/{full_name}/issues/{issue_number}/comments",
        token=token,
        params={"per_page": min(max_comments, 20), "sort": "created", "direction": "desc"},
    )

    if not isinstance(comments, list):
        return []

    normalized = [_normalize_comment(comment) for comment in comments if isinstance(comment, dict)]

    # API returns oldest-first by default in many cases. Keep latest max_comments.
    return normalized[-max_comments:]


def get_issue_context(
    full_name: str,
    issue_number: int,
    token: Optional[str] = None,
    max_comments: int = 5,
) -> Dict:
    """Fetch full issue body + latest comments for deep AI understanding.

    The issue body is treated as the source of truth. Comments are separate
    context and should not be confused with the issue request.
    """
    if not full_name or not issue_number:
        return {}

    raw_issue = _github_get(f"/repos/{full_name}/issues/{issue_number}", token=token)
    issue = _normalize_issue(raw_issue)

    comments = []
    try:
        comments = fetch_issue_comments(
            full_name=full_name,
            issue_number=issue_number,
            token=token,
            max_comments=max_comments,
        )
    except GitHubClientError:
        comments = []

    return {
        "repo": full_name,
        "issue_number": issue_number,
        "title": issue.get("title", ""),
        "body": issue.get("body", ""),
        "labels": issue.get("labels", []),
        "comments_count": issue.get("comments", 0),
        "latest_comments": comments,
        "assignee": issue.get("assignee"),
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
        "url": issue.get("url", ""),
        "state": issue.get("state", "open"),
    }


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

            tech_stacks.add(str(tech))

            if str(tech).lower().strip() in language_like:
                languages.add(str(tech))

        if project.get("language"):
            languages.add(project["language"])

        if project.get("difficulty"):
            difficulties.add(project["difficulty"])

    return {
        "tech_stacks": sorted(tech_stacks),
        "languages": sorted(languages),
        "difficulties": sorted(difficulties),
    }


def _matches_keywords(project: Dict, keywords: str) -> bool:
    if not keywords:
        return True

    words = [word.strip().lower() for word in re.split(r"[\s,]+", keywords) if word.strip()]
    if not words:
        return True

    text_blob = " ".join([
        project.get("name", ""),
        project.get("description", ""),
        project.get("admin", ""),
        project.get("language", ""),
        project.get("difficulty", ""),
        project.get("category", ""),
        " ".join(project.get("tech_stack", [])),
        project.get("repo_full_name", ""),
    ]).lower()

    # Match if any meaningful keyword appears. This is friendlier than requiring exact phrase.
    return any(word in text_blob for word in words)


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

        if keywords and not _matches_keywords(project, keywords):
            continue

        if tech_stack and tech_stack.lower() not in techs:
            continue

        if language:
            lang = language.lower()
            project_lang = project.get("language", "").lower()

            if lang != project_lang and lang not in techs:
                continue

        if difficulty and difficulty.lower() not in project.get("difficulty", "").lower():
            continue

        filtered.append(project)

    if sort_by in {"Most Good First Issues", "Best AI/ML fit"}:
        filtered.sort(
            key=lambda x: (
                x.get("good_first_issues", 0),
                "python" in " ".join(x.get("tech_stack", [])).lower(),
                "ml" in " ".join(x.get("tech_stack", [])).lower()
                or "ai" in " ".join(x.get("tech_stack", [])).lower()
                or "machine" in x.get("description", "").lower(),
            ),
            reverse=True,
        )
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
    elif sort_by == "Recently Updated":
        filtered.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    elif sort_by == "Name A-Z":
        filtered.sort(key=lambda x: x.get("name", "").lower())

    return filtered[:18]

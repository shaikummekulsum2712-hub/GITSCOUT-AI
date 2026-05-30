# import base64
# import os
# import re
# from pathlib import Path
# from typing import Any, Dict, List, Optional

# import requests
# from dotenv import load_dotenv


# BASE_URL = "https://api.github.com"
# GSSOC_API_URL = "https://gssoc.girlscript.org/api/projects"


# class GitHubClientError(Exception):
#     pass


# def _load_token(token: Optional[str] = None) -> Optional[str]:
#     """Load GitHub token if available.

#     The app can still work without a token for public repos, but a token gives
#     higher rate limits. This avoids crashing just because GITHUB_TOKEN is absent.
#     """
#     if token:
#         return token

#     env_path = Path(__file__).resolve().parents[1] / ".env"
#     if env_path.exists():
#         load_dotenv(env_path)

#     return os.getenv("GITHUB_TOKEN")


# def _github_get(path: str, token: Optional[str] = None, params: Optional[Dict] = None):
#     headers = {
#         "Accept": "application/vnd.github+json",
#         "User-Agent": "GitScout-AI",
#     }

#     loaded_token = _load_token(token)
#     if loaded_token:
#         headers["Authorization"] = f"Bearer {loaded_token}"

#     response = requests.get(
#         f"{BASE_URL}{path}",
#         headers=headers,
#         params=params,
#         timeout=25,
#     )

#     if response.status_code == 401:
#         raise GitHubClientError("Invalid GitHub token.")

#     if response.status_code == 403:
#         message = response.text[:250]
#         raise GitHubClientError(f"GitHub rate limit or permission issue: {message}")

#     if not response.ok:
#         raise GitHubClientError(
#             f"GitHub API error {response.status_code}: {response.text[:250]}"
#         )

#     return response.json()


# def extract_repo_full_name(repo_url: str) -> str:
#     if not repo_url:
#         return ""

#     repo_url = repo_url.strip()

#     match = re.search(r"github\.com/([^/\s]+/[^/#?\s]+)", repo_url)
#     if match:
#         return match.group(1).replace(".git", "").strip("/")

#     if re.match(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", repo_url):
#         return repo_url.replace(".git", "").strip("/")

#     return ""


# def _decode_readme(content: Dict) -> str:
#     try:
#         return base64.b64decode(content.get("content", "")).decode("utf-8", errors="ignore")
#     except Exception:
#         return ""


# def _normalize_label(label: Any) -> str:
#     if isinstance(label, dict):
#         return str(label.get("name", "")).strip().lower()
#     return str(label).strip().lower()


# def _normalize_issue(issue: Dict) -> Dict:
#     labels = [_normalize_label(label) for label in issue.get("labels", []) if _normalize_label(label)]

#     return {
#         "id": issue.get("id"),
#         "number": issue.get("number"),
#         "title": issue.get("title", "") or "",
#         "body": issue.get("body") or "",
#         "url": issue.get("html_url", "") or "",
#         "api_url": issue.get("url", "") or "",
#         "comments": issue.get("comments", 0) or 0,
#         "created_at": issue.get("created_at"),
#         "updated_at": issue.get("updated_at"),
#         "state": issue.get("state", "open"),
#         "assignee": issue.get("assignee", {}).get("login") if issue.get("assignee") else None,
#         "labels": labels,
#         "good_first_issue": "good first issue" in labels,
#         "help_wanted": "help wanted" in labels,
#         "pull_request": "pull_request" in issue,
#     }


# def _normalize_comment(comment: Dict) -> Dict:
#     user = comment.get("user") or {}
#     return {
#         "user": user.get("login", "unknown"),
#         "body": comment.get("body") or "",
#         "created_at": comment.get("created_at"),
#         "updated_at": comment.get("updated_at"),
#         "url": comment.get("html_url", ""),
#     }


# def _normalize_repo_metadata(repo: Dict) -> Dict:
#     return {
#         "name": repo.get("full_name", ""),
#         "full_name": repo.get("full_name", ""),
#         "url": repo.get("html_url", ""),
#         "repo_url": repo.get("html_url", ""),
#         "description": repo.get("description") or "",
#         "stars": repo.get("stargazers_count", 0),
#         "forks": repo.get("forks_count", 0),
#         "language": repo.get("language") or "",
#         "open_issues_count": repo.get("open_issues_count", 0),
#         "updated_at": repo.get("updated_at"),
#         "topics": repo.get("topics", []),
#         "default_branch": repo.get("default_branch", "main"),
#     }


# def _normalize_gssoc_project(item: Dict) -> Dict:
#     repo_url = (
#         item.get("repo_url")
#         or item.get("repository")
#         or item.get("github_url")
#         or item.get("github")
#         or item.get("url")
#         or ""
#     )

#     tech_stack = (
#         item.get("tech_stack")
#         or item.get("techStack")
#         or item.get("technologies")
#         or item.get("tags")
#         or []
#     )

#     if isinstance(tech_stack, str):
#         tech_stack = [part.strip() for part in tech_stack.split(",") if part.strip()]

#     name = (
#         item.get("name")
#         or item.get("project_name")
#         or item.get("title")
#         or "Unknown Project"
#     )

#     difficulty = (
#         item.get("difficulty")
#         or item.get("level")
#         or item.get("project_difficulty")
#         or ""
#     )

#     return {
#         "id": item.get("id"),
#         "name": name,
#         "description": item.get("description", "") or "",
#         "url": repo_url,
#         "repo_url": repo_url,
#         "repo_full_name": extract_repo_full_name(repo_url),
#         "language": item.get("language", "") or "",
#         "tech_stack": tech_stack or [],
#         "difficulty": difficulty,
#         "category": item.get("category", "") or "",
#         "good_first_issues": item.get("good_first_issues", item.get("good_first_issue_count", 0)) or 0,
#         "open_issues": item.get("open_issues", item.get("open_issues_count", 0)) or 0,
#         "stars": item.get("stars", 0) or 0,
#         "forks": item.get("forks", 0) or 0,
#         "admin": item.get("admin") or item.get("admin_name") or item.get("mentor") or "",
#         "updated_at": item.get("updated_at", "") or "",
#         "is_gssoc": True,
#     }


# def fetch_gssoc_projects() -> List[Dict]:
#     response = requests.get(GSSOC_API_URL, timeout=25)

#     if not response.ok:
#         raise GitHubClientError(f"Could not load GSSoC projects: {response.status_code}")

#     try:
#         data = response.json()
#     except ValueError as exc:
#         raise GitHubClientError("GSSoC response is not valid JSON.") from exc

#     if isinstance(data, list):
#         items = data
#     elif isinstance(data, dict):
#         items = data.get("projects") or data.get("data") or data.get("items") or []
#     else:
#         items = []

#     if not isinstance(items, list):
#         raise GitHubClientError("GSSoC project format not recognized.")

#     projects = [_normalize_gssoc_project(item) for item in items if isinstance(item, dict)]
#     return [project for project in projects if project.get("name")]



# def search_github_repositories(
#     keywords: Optional[str] = None,
#     domain: Optional[str] = None,
#     tech_stack: Optional[List[str]] = None,
#     languages: Optional[List[str]] = None,
#     sort_by: str = "Best match",
#     token: Optional[str] = None,
#     per_page: int = 18,
# ) -> List[Dict]:
#     """Search public GitHub repositories for any domain.

#     Multiple selected languages/tech stacks are treated as OR choices:
#     - Python OR JavaScript OR Go
#     - Auth OR JWT OR OWASP

#     Domain is still the main search intent.
#     """
#     tech_stack = [str(x).strip() for x in (tech_stack or []) if str(x).strip()]
#     languages = [str(x).strip() for x in (languages or []) if str(x).strip()]

#     domain_terms = {
#         "AI/ML": ["machine-learning", "artificial-intelligence", "deep-learning", "nlp", "computer-vision", "pytorch", "tensorflow"],
#         "Web Development": ["frontend", "web", "react", "nextjs", "javascript", "typescript", "vue", "angular"],
#         "Backend": ["backend", "api", "server", "fastapi", "django", "flask", "nodejs", "express", "spring-boot"],
#         "Cybersecurity": ["security", "cybersecurity", "auth", "owasp", "jwt", "oauth", "encryption", "penetration-testing"],
#         "DevOps": ["devops", "docker", "kubernetes", "ci-cd", "deployment", "terraform", "monitoring", "infrastructure"],
#         "Mobile": ["mobile", "android", "flutter", "react-native", "ios", "kotlin", "swift"],
#         "Data Science": ["data-science", "pandas", "numpy", "jupyter", "visualization", "data-engineering", "etl"],
#         "Blockchain": ["blockchain", "solidity", "web3", "smart-contracts", "ethereum", "defi", "hardhat"],
#         "Docs": ["documentation", "docs", "tutorial", "markdown", "docusaurus", "api-docs", "examples"],
#         "Testing": ["testing", "test", "jest", "pytest", "e2e", "cypress", "selenium", "unit-testing"],
#         "UI/UX": ["ui", "ux", "react", "css", "design-system", "accessibility", "component-library", "storybook"],
#         "Databases": ["database", "postgresql", "mongodb", "redis", "mysql", "elasticsearch", "sql"],
#         "Cloud": ["cloud", "aws", "gcp", "azure", "kubernetes", "serverless", "deployment", "cloud-native"],
#         "Automation": ["automation", "script", "workflow", "ci-cd", "rpa", "python", "javascript"],
#         "CLI Tools": ["cli", "command-line", "tool", "go", "rust", "shell", "typescript", "terminal"],
#         "Developer Tools": ["dev-tools", "ide", "build-tools", "compiler", "debugger", "linter", "formatter"],
#     }

#     # GitHub search treats space-separated terms as AND, so do not join every
#     # selected stack/language into one huge query. Instead, run several smaller
#     # searches and merge results. That gives OR behavior.
#     domain_choices = domain_terms.get(domain or "", [domain or "open-source"])
#     domain_choices = [x for x in domain_choices if x][:3]

#     stack_choices = tech_stack[:4] or [""]
#     language_choices = languages[:4] or [""]

#     # If user selects almost everything, treat it as "any" to avoid building
#     # dozens of queries and to avoid making results random.
#     if len(tech_stack) >= 7:
#         stack_choices = [""]
#     if len(languages) >= 6:
#         language_choices = [""]

#     sort = "stars"
#     order = "desc"
#     if sort_by == "Recently Updated":
#         sort = "updated"
#     elif sort_by == "Most Open Issues":
#         sort = "help-wanted-issues"
#     elif sort_by == "Name A-Z":
#         sort = ""

#     def language_qualifier(lang: str) -> str:
#         if not lang:
#             return ""
#         if lang.lower() == "html/css":
#             return "language:HTML"
#         return f"language:{lang}"

#     queries = []
#     keyword_text = str(keywords or "").strip()

#     # Generate base queries (without good-first-issues restriction).
#     # For AI/ML, we'll also generate good-first-issues variants for ranking.
#     base_queries = []
#     for domain_term in domain_choices:
#         for stack in stack_choices:
#             for lang in language_choices:
#                 parts = []
#                 if keyword_text:
#                     parts.append(keyword_text)
#                 if domain_term:
#                     parts.append(domain_term)
#                 if stack:
#                     parts.append(str(stack))
#                 lq = language_qualifier(lang)
#                 if lq:
#                     parts.append(lq)

#                 q = " ".join(parts).strip()
#                 if q and q not in base_queries:
#                     base_queries.append(q)

#     # For AI/ML domain, prioritize good-first-issues; for other domains, use broader search.
#     if domain and domain.lower() == "ai/ml":
#         # AI/ML: prioritize good-first-issues repos
#         for q in base_queries[:4]:
#             if "good-first-issues" not in q:
#                 queries.append(f"{q} good-first-issues")
#             else:
#                 queries.append(q)
#         # Also add base queries to catch broader results
#         queries.extend(base_queries[:4])
#     else:
#         # Other domains: search broadly without good-first-issues restriction
#         queries = base_queries[:6]

#     # Keep API calls bounded.
#     queries = queries[:8] or [domain or "open-source"]

#     repos = []
#     seen = set()
#     per_query = max(5, min(10, per_page))

#     for q in queries:
#         params = {
#             "q": q,
#             "per_page": per_query,
#             "order": order,
#         }
#         if sort:
#             params["sort"] = sort

#         try:
#             data = _github_get("/search/repositories", token=token, params=params)
#         except GitHubClientError:
#             continue

#         items = data.get("items", []) if isinstance(data, dict) else []
#         for item in items:
#             if not isinstance(item, dict):
#                 continue

#             full_name = item.get("full_name", "")
#             if not full_name or full_name in seen:
#                 continue

#             seen.add(full_name)
#             normalized = _normalize_repo_metadata(item)
#             normalized.update({
#                 "repo_full_name": full_name,
#                 "tech_stack": item.get("topics", []) or [],
#                 "difficulty": "Beginner Friendly" if item.get("has_issues", True) else "",
#                 "open_issues": item.get("open_issues_count", 0),
#                 "good_first_issues": 0,
#                 "is_github_search": True,
#                 "_matched_query": q,
#             })
#             repos.append(normalized)

#             if len(repos) >= per_page:
#                 return repos

#     return repos


# def get_repository_metadata(full_name: str, token: Optional[str] = None) -> Dict:
#     if not full_name:
#         return {}

#     repo = _github_get(f"/repos/{full_name}", token=token)
#     return _normalize_repo_metadata(repo)


# def get_repository_readme(full_name: str, token: Optional[str] = None) -> str:
#     if not full_name:
#         return ""

#     try:
#         content = _github_get(f"/repos/{full_name}/readme", token=token)
#         return _decode_readme(content)
#     except GitHubClientError:
#         return ""


# def fetch_open_issues(
#     full_name: str,
#     token: Optional[str] = None,
#     per_page: int = 100,
# ) -> List[Dict]:
#     if not full_name:
#         return []

#     params = {
#         "state": "open",
#         "per_page": per_page,
#         "sort": "created",
#         "direction": "desc",
#     }

#     issues = _github_get(
#         f"/repos/{full_name}/issues",
#         token=token,
#         params=params,
#     )

#     return [
#         _normalize_issue(issue)
#         for issue in issues
#         if isinstance(issue, dict) and not issue.get("pull_request")
#     ]


# def fetch_issue_comments(
#     full_name: str,
#     issue_number: int,
#     token: Optional[str] = None,
#     max_comments: int = 5,
# ) -> List[Dict]:
#     if not full_name or not issue_number:
#         return []

#     comments = _github_get(
#         f"/repos/{full_name}/issues/{issue_number}/comments",
#         token=token,
#         params={"per_page": min(max_comments, 20), "sort": "created", "direction": "desc"},
#     )

#     if not isinstance(comments, list):
#         return []

#     normalized = [_normalize_comment(comment) for comment in comments if isinstance(comment, dict)]

#     # API returns oldest-first by default in many cases. Keep latest max_comments.
#     return normalized[-max_comments:]


# def get_issue_context(
#     full_name: str,
#     issue_number: int,
#     token: Optional[str] = None,
#     max_comments: int = 5,
# ) -> Dict:
#     """Fetch full issue body + latest comments for deep AI understanding.

#     The issue body is treated as the source of truth. Comments are separate
#     context and should not be confused with the issue request.
#     """
#     if not full_name or not issue_number:
#         return {}

#     raw_issue = _github_get(f"/repos/{full_name}/issues/{issue_number}", token=token)
#     issue = _normalize_issue(raw_issue)

#     comments = []
#     try:
#         comments = fetch_issue_comments(
#             full_name=full_name,
#             issue_number=issue_number,
#             token=token,
#             max_comments=max_comments,
#         )
#     except GitHubClientError:
#         comments = []

#     return {
#         "repo": full_name,
#         "issue_number": issue_number,
#         "title": issue.get("title", ""),
#         "body": issue.get("body", ""),
#         "labels": issue.get("labels", []),
#         "comments_count": issue.get("comments", 0),
#         "latest_comments": comments,
#         "assignee": issue.get("assignee"),
#         "created_at": issue.get("created_at"),
#         "updated_at": issue.get("updated_at"),
#         "url": issue.get("url", ""),
#         "state": issue.get("state", "open"),
#     }


# def get_gssoc_filter_options() -> Dict[str, List[str]]:
#     projects = fetch_gssoc_projects()

#     tech_stacks = set()
#     languages = set()
#     difficulties = set()

#     language_like = {
#         "python", "javascript", "typescript", "java", "c++", "c",
#         "c#", "go", "golang", "rust", "php", "ruby", "kotlin",
#         "swift", "dart", "r", "scala", "html", "css", "sql"
#     }

#     for project in projects:
#         for tech in project.get("tech_stack", []):
#             if not tech:
#                 continue

#             tech_stacks.add(str(tech))

#             if str(tech).lower().strip() in language_like:
#                 languages.add(str(tech))

#         if project.get("language"):
#             languages.add(project["language"])

#         if project.get("difficulty"):
#             difficulties.add(project["difficulty"])

#     return {
#         "tech_stacks": sorted(tech_stacks),
#         "languages": sorted(languages),
#         "difficulties": sorted(difficulties),
#     }


# def _matches_keywords(project: Dict, keywords: str) -> bool:
#     if not keywords:
#         return True

#     words = [word.strip().lower() for word in re.split(r"[\s,]+", keywords) if word.strip()]
#     if not words:
#         return True

#     text_blob = " ".join([
#         project.get("name", ""),
#         project.get("description", ""),
#         project.get("admin", ""),
#         project.get("language", ""),
#         project.get("difficulty", ""),
#         project.get("category", ""),
#         " ".join(project.get("tech_stack", [])),
#         project.get("repo_full_name", ""),
#     ]).lower()

#     # Match if any meaningful keyword appears. This is friendlier than requiring exact phrase.
#     return any(word in text_blob for word in words)


# def search_gssoc_projects(
#     keywords: Optional[str] = None,
#     tech_stack: Optional[str] = None,
#     language: Optional[str] = None,
#     difficulty: Optional[str] = None,
#     sort_by: str = "Most Open Issues",
# ) -> List[Dict]:
#     projects = fetch_gssoc_projects()
#     filtered = []

#     for project in projects:
#         techs = [str(t).lower() for t in project.get("tech_stack", [])]

#         if keywords and not _matches_keywords(project, keywords):
#             continue

#         if tech_stack and tech_stack.lower() not in techs:
#             continue

#         if language:
#             lang = language.lower()
#             project_lang = project.get("language", "").lower()

#             if lang != project_lang and lang not in techs:
#                 continue

#         if difficulty and difficulty.lower() not in project.get("difficulty", "").lower():
#             continue

#         filtered.append(project)

#     if sort_by in {"Most Good First Issues", "Best AI/ML fit"}:
#         filtered.sort(
#             key=lambda x: (
#                 x.get("good_first_issues", 0),
#                 "python" in " ".join(x.get("tech_stack", [])).lower(),
#                 "ml" in " ".join(x.get("tech_stack", [])).lower()
#                 or "ai" in " ".join(x.get("tech_stack", [])).lower()
#                 or "machine" in x.get("description", "").lower(),
#             ),
#             reverse=True,
#         )
#     elif sort_by == "Most Open Issues":
#         filtered.sort(key=lambda x: x.get("open_issues", 0), reverse=True)
#     elif sort_by == "Beginner Friendly First":
#         filtered.sort(
#             key=lambda x: (
#                 "beginner" in x.get("difficulty", "").lower(),
#                 x.get("good_first_issues", 0),
#             ),
#             reverse=True,
#         )
#     elif sort_by == "Recently Updated":
#         filtered.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
#     elif sort_by == "Name A-Z":
#         filtered.sort(key=lambda x: x.get("name", "").lower())

#     return filtered[:18]



"""
GitScout AI - Smart GitHub client

This module is responsible for:
- searching public GitHub repositories intelligently
- expanding domain/category filters into better GitHub search queries
- supporting direct repo/issue URLs
- normalizing GitHub API responses for the Streamlit UI
- fetching repo metadata, README, issues, issue context, and comments

Drop this file in:
    src/github_client.py
"""

from __future__ import annotations

import base64
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

import requests


GITHUB_API = "https://api.github.com"
DEFAULT_TIMEOUT = 20


# ─────────────────────────────────────────────────────────────
# Domain intelligence
# ─────────────────────────────────────────────────────────────

DOMAIN_PROFILES: Dict[str, Dict[str, Any]] = {
    "AI/ML": {
        "keywords": [
            "machine learning", "deep learning", "artificial intelligence", "ai",
            "ml", "nlp", "computer vision", "model", "dataset", "training",
            "inference", "pytorch", "tensorflow", "scikit-learn", "transformers",
            "llm", "rag", "embedding", "vector database", "mlops"
        ],
        "queries": [
            "machine learning python",
            "deep learning pytorch",
            "nlp transformers python",
            "computer vision python",
            "mlops python",
            "rag llm python",
            "scikit learn examples",
            "data science python",
        ],
        "project_types": [
            "ML Library", "NLP", "Computer Vision", "MLOps", "RAG/LLM",
            "Data Science", "Model Training", "Examples/Notebooks"
        ],
    },
    "Web Development": {
        "keywords": [
            "frontend", "web app", "react", "nextjs", "next.js", "vue",
            "angular", "svelte", "tailwind", "html", "css", "javascript",
            "typescript", "ui", "component", "dashboard", "web"
        ],
        "queries": [
            "react web app",
            "nextjs dashboard",
            "frontend typescript",
            "tailwind ui components",
            "javascript web app",
            "open source frontend",
        ],
        "project_types": [
            "Frontend", "Dashboard", "Component Library", "Full-stack Web",
            "Landing Page", "Admin Panel"
        ],
    },
    "Backend": {
        "keywords": [
            "backend", "api", "server", "rest", "graphql", "fastapi", "django",
            "flask", "express", "node", "spring boot", "database", "auth",
            "microservice", "worker", "queue", "redis", "postgres"
        ],
        "queries": [
            "backend api python",
            "fastapi backend",
            "django rest api",
            "node express api",
            "microservice backend",
            "authentication backend",
        ],
        "project_types": [
            "REST API", "Authentication", "Microservice", "Database Backend",
            "Queue/Workers", "GraphQL API"
        ],
    },
    "Cybersecurity": {
        "keywords": [
            "security", "cybersecurity", "auth", "authentication", "authorization",
            "jwt", "oauth", "owasp", "vulnerability", "scanner", "encryption",
            "cryptography", "pentest", "network security", "malware", "audit"
        ],
        "queries": [
            "security tool python",
            "owasp scanner",
            "jwt authentication",
            "vulnerability scanner",
            "cryptography python",
            "security audit tool",
        ],
        "project_types": [
            "Scanner", "Authentication", "OWASP", "Cryptography",
            "Security Audit", "Network Security"
        ],
    },
    "DevOps": {
        "keywords": [
            "devops", "docker", "kubernetes", "ci", "cd", "github actions",
            "terraform", "ansible", "jenkins", "deployment", "monitoring",
            "prometheus", "grafana", "infrastructure", "helm", "cloud native"
        ],
        "queries": [
            "devops tool",
            "docker kubernetes",
            "github actions ci",
            "terraform infrastructure",
            "monitoring prometheus grafana",
            "deployment automation",
        ],
        "project_types": [
            "CI/CD", "Docker", "Kubernetes", "Infrastructure as Code",
            "Monitoring", "Deployment"
        ],
    },
    "Mobile": {
        "keywords": [
            "mobile", "android", "ios", "flutter", "react native", "swift",
            "kotlin", "dart", "app", "native", "mobile ui"
        ],
        "queries": [
            "flutter app",
            "react native app",
            "android kotlin",
            "ios swift",
            "mobile app open source",
        ],
        "project_types": [
            "Android", "iOS", "Flutter", "React Native", "Mobile UI"
        ],
    },
    "Data Science": {
        "keywords": [
            "data science", "pandas", "numpy", "jupyter", "notebook",
            "visualization", "matplotlib", "plotly", "etl", "analytics",
            "statistics", "dataset", "data pipeline", "data cleaning"
        ],
        "queries": [
            "data science python",
            "pandas numpy",
            "jupyter notebook",
            "data visualization python",
            "etl data pipeline",
            "data cleaning python",
        ],
        "project_types": [
            "Data Cleaning", "Visualization", "ETL", "Analytics",
            "Notebook Examples", "Statistics"
        ],
    },
    "Blockchain": {
        "keywords": [
            "blockchain", "web3", "solidity", "ethereum", "smart contract",
            "defi", "nft", "hardhat", "truffle", "the graph", "graph protocol",
            "wallet", "dao", "rust blockchain"
        ],
        "queries": [
            "solidity smart contracts",
            "web3 ethereum",
            "hardhat defi",
            "the graph protocol",
            "blockchain rust",
        ],
        "project_types": [
            "Smart Contracts", "Web3", "DeFi", "Indexing", "Wallet",
            "The Graph"
        ],
    },
    "Docs": {
        "keywords": [
            "documentation", "docs", "readme", "guide", "tutorial", "examples",
            "markdown", "mdx", "docusaurus", "sphinx", "technical writing",
            "api docs", "developer docs"
        ],
        "queries": [
            "documentation open source",
            "docusaurus docs",
            "sphinx documentation",
            "markdown docs",
            "api documentation",
        ],
        "project_types": [
            "Documentation", "Tutorials", "API Docs", "README", "Examples"
        ],
    },
    "Testing": {
        "keywords": [
            "testing", "tests", "unit test", "integration test", "e2e",
            "pytest", "jest", "cypress", "selenium", "test framework",
            "coverage", "qa"
        ],
        "queries": [
            "testing framework",
            "pytest python",
            "jest javascript",
            "cypress e2e",
            "selenium testing",
        ],
        "project_types": [
            "Unit Testing", "Integration Testing", "E2E Testing",
            "Test Framework", "QA Automation"
        ],
    },
    "UI/UX": {
        "keywords": [
            "ui", "ux", "design system", "component library", "storybook",
            "accessibility", "a11y", "figma", "css", "tailwind",
            "frontend components", "theme"
        ],
        "queries": [
            "design system react",
            "component library",
            "storybook react",
            "accessibility ui",
            "tailwind components",
        ],
        "project_types": [
            "Design System", "Components", "Accessibility", "Storybook",
            "Frontend UI"
        ],
    },
    "Databases": {
        "keywords": [
            "database", "postgres", "postgresql", "mysql", "mongodb", "redis",
            "sqlite", "sql", "query", "orm", "migration", "elasticsearch",
            "database tool", "db"
        ],
        "queries": [
            "postgresql tool",
            "database migration",
            "redis tool",
            "mongodb python",
            "sql query tool",
            "database open source",
        ],
        "project_types": [
            "PostgreSQL", "Redis", "MongoDB", "SQL Tool", "Migrations", "ORM"
        ],
    },
    "Cloud": {
        "keywords": [
            "cloud", "aws", "gcp", "azure", "serverless", "lambda",
            "deployment", "cloud native", "kubernetes", "docker",
            "infrastructure", "terraform"
        ],
        "queries": [
            "aws tool",
            "serverless framework",
            "cloud native",
            "azure devops",
            "gcp python",
            "cloud deployment",
        ],
        "project_types": [
            "AWS", "GCP", "Azure", "Serverless", "Cloud Native", "Deployment"
        ],
    },
    "Automation": {
        "keywords": [
            "automation", "script", "workflow", "bot", "task runner",
            "scheduler", "rpa", "crawler", "scraper", "pipeline",
            "github automation"
        ],
        "queries": [
            "automation python",
            "workflow automation",
            "task automation",
            "github bot",
            "scraper automation",
        ],
        "project_types": [
            "Workflow", "Bot", "Scraper", "Task Runner", "Scheduler", "RPA"
        ],
    },
    "CLI Tools": {
        "keywords": [
            "cli", "command line", "terminal", "console", "shell", "tool",
            "developer utility", "command", "python cli", "go cli",
            "rust cli"
        ],
        "queries": [
            "cli tool python",
            "command line tool",
            "terminal tool",
            "developer cli",
            "rust cli tool",
            "go cli tool",
        ],
        "project_types": [
            "Command Line", "Terminal Tool", "Developer CLI", "Shell Tool"
        ],
    },
    "Developer Tools": {
        "keywords": [
            "developer tool", "developer tools", "devtool", "utility", "cli",
            "command line", "converter", "parser", "markdown", "document",
            "document converter", "docx", "pdf", "pptx", "xlsx", "file processing",
            "text extraction", "automation", "sdk", "api client", "linter",
            "formatter", "build tool", "debugger", "code generation",
            "codegen", "markdown converter", "document processing"
        ],
        "queries": [
            "developer tool",
            "cli tool",
            "document converter",
            "markdown converter",
            "pdf docx parser",
            "file processing python",
            "text extraction tool",
            "linter formatter",
            "api client sdk",
            "build tool",
        ],
        "project_types": [
            "CLI Tool", "Document Converter", "Parser", "Markdown Tool",
            "API Client", "Automation", "Linter/Formatter", "Build Tool",
            "File Processing", "Text Extraction"
        ],
    },
}


# aliases are used for scoring text matches and query expansion
TECH_ALIASES: Dict[str, List[str]] = {
    "HTML/CSS": ["html", "css", "frontend", "web"],
    "CLI": ["cli", "command line", "terminal", "console"],
    "Command Line": ["cli", "command line", "terminal"],
    "Document Converter": ["document converter", "converter", "docx", "pdf", "markdown", "file processing"],
    "Markdown Tool": ["markdown", "md", "mdx", "markdown converter"],
    "Parser": ["parser", "parse", "parsing"],
    "File Processing": ["file processing", "text extraction", "document processing"],
    "Text Extraction": ["text extraction", "ocr", "document extraction"],
    "API Client": ["api client", "sdk", "client library"],
    "Linters/Formatters": ["linter", "formatter", "lint", "format"],
    "Linter/Formatter": ["linter", "formatter", "lint", "format"],
    "Docs": ["docs", "documentation", "readme", "tutorial", "guide"],
    "Documentation": ["docs", "documentation", "readme", "tutorial", "guide"],
    "AI/ML": ["ai", "ml", "machine learning", "deep learning"],
    "RAG/LLM": ["rag", "llm", "language model", "embedding", "vector"],
}


# ─────────────────────────────────────────────────────────────
# Low-level helpers
# ─────────────────────────────────────────────────────────────

def _github_token() -> str:
    # Support both names because your app has used GEMINI/GITHUB envs separately.
    return os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or ""


def _headers() -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GitScout-AI",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = _github_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    response = requests.get(
        url,
        headers=_headers(),
        params=params or {},
        timeout=DEFAULT_TIMEOUT,
    )
    if response.status_code == 404:
        raise RuntimeError(f"GitHub API error 404: {response.text}")
    if response.status_code == 403:
        raise RuntimeError(
            "GitHub API rate limit or permission error. Add/refresh GITHUB_TOKEN."
        )
    if not response.ok:
        raise RuntimeError(f"GitHub API error {response.status_code}: {response.text}")
    return response.json()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _unique(items: Iterable[Any]) -> List[str]:
    result: List[str] = []
    seen = set()
    for item in items:
        text = str(item or "").strip()
        if not text:
            continue
        key = text.lower()
        if key not in seen:
            result.append(text)
            seen.add(key)
    return result


def _clean_text(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _repo_text(repo: Dict[str, Any]) -> str:
    parts = [
        repo.get("name", ""),
        repo.get("full_name", ""),
        repo.get("repo_full_name", ""),
        repo.get("description", ""),
        repo.get("language", ""),
        " ".join(_as_list(repo.get("topics", []))),
        " ".join(_as_list(repo.get("tech_stack", []))),
        repo.get("_search_blob", ""),
    ]
    return " ".join(str(part or "") for part in parts).lower()


def _contains_any(text: str, terms: Iterable[str]) -> List[str]:
    hits = []
    low = (text or "").lower()
    for term in terms:
        t = str(term or "").lower().strip()
        if t and t in low:
            hits.append(str(term))
    return _unique(hits)


def _language_query_part(languages: List[str]) -> str:
    # GitHub search supports one language: per query. For multiple languages,
    # we generate multiple queries rather than one invalid query.
    if not languages:
        return ""
    lang = languages[0]
    if lang == "HTML/CSS":
        return "language:HTML"
    if lang == "C#":
        return 'language:"C#"'
    if lang == "C++":
        return 'language:"C++"'
    return f"language:{lang}"


def parse_github_url_or_repo(value: str) -> Dict[str, Any]:
    """
    Supports:
    - microsoft/markitdown
    - https://github.com/microsoft/markitdown
    - https://github.com/microsoft/markitdown/issues/1982
    """
    raw = str(value or "").strip()

    if not raw:
        return {"owner": "", "repo": "", "full_name": "", "issue_number": None, "is_direct": False}

    # owner/repo shorthand
    shorthand = re.fullmatch(r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", raw)
    if shorthand:
        owner, repo = shorthand.groups()
        return {
            "owner": owner,
            "repo": repo,
            "full_name": f"{owner}/{repo}",
            "issue_number": None,
            "is_direct": True,
        }

    try:
        parsed = urlparse(raw)
    except Exception:
        return {"owner": "", "repo": "", "full_name": "", "issue_number": None, "is_direct": False}

    if "github.com" not in parsed.netloc.lower():
        return {"owner": "", "repo": "", "full_name": "", "issue_number": None, "is_direct": False}

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        return {"owner": "", "repo": "", "full_name": "", "issue_number": None, "is_direct": False}

    owner, repo = parts[0], parts[1]
    issue_number = None

    if len(parts) >= 4 and parts[2] == "issues":
        try:
            issue_number = int(parts[3])
        except ValueError:
            issue_number = None

    return {
        "owner": owner,
        "repo": repo,
        "full_name": f"{owner}/{repo}",
        "issue_number": issue_number,
        "is_direct": True,
    }


# ─────────────────────────────────────────────────────────────
# Repo normalization + scoring
# ─────────────────────────────────────────────────────────────

def _normalize_repo(item: Dict[str, Any], source: str = "github", matched_query: str = "") -> Dict[str, Any]:
    owner = item.get("owner") or {}
    topics = item.get("topics") or []

    full_name = item.get("full_name") or ""
    html_url = item.get("html_url") or item.get("repo_url") or ""

    normalized = {
        "name": item.get("name") or full_name.split("/")[-1] if full_name else item.get("name", ""),
        "full_name": full_name,
        "repo_full_name": full_name,
        "repo_url": html_url,
        "github_url": html_url,
        "html_url": html_url,
        "description": item.get("description") or "",
        "language": item.get("language") or "",
        "topics": topics,
        "tech_stack": topics,
        "stars": _safe_int(item.get("stargazers_count", item.get("stars", 0))),
        "forks": _safe_int(item.get("forks_count", item.get("forks", 0))),
        "open_issues": _safe_int(item.get("open_issues_count", item.get("open_issues", 0))),
        "open_issues_count": _safe_int(item.get("open_issues_count", item.get("open_issues", 0))),
        "updated_at": item.get("updated_at") or "",
        "created_at": item.get("created_at") or "",
        "pushed_at": item.get("pushed_at") or "",
        "default_branch": item.get("default_branch") or "main",
        "owner": owner.get("login") if isinstance(owner, dict) else "",
        "source": source,
        "is_github_search": source == "github",
        "is_gssoc": source == "gssoc",
        "_matched_query": matched_query,
    }

    normalized["_search_blob"] = " ".join(
        [
            normalized["name"],
            normalized["full_name"],
            normalized["description"],
            normalized["language"],
            " ".join(topics),
            matched_query,
        ]
    )
    return normalized


def _days_since(date_value: str) -> Optional[int]:
    if not date_value:
        return None
    try:
        dt = datetime.fromisoformat(str(date_value).replace("Z", "+00:00"))
        return max(0, (datetime.now(timezone.utc) - dt).days)
    except Exception:
        return None


def _match_language(repo: Dict[str, Any], languages: List[str]) -> Tuple[int, List[str]]:
    if not languages:
        return 10, []

    repo_lang = str(repo.get("language") or "").lower()
    text = _repo_text(repo)
    hits = []

    for lang in languages:
        lang_low = str(lang).lower()
        aliases = TECH_ALIASES.get(lang, [])
        choices = [lang_low] + [alias.lower() for alias in aliases]
        if repo_lang == lang_low or any(choice in text for choice in choices):
            hits.append(lang)

    if hits:
        return 18, hits[:3]

    return -8, []


def _match_domain(repo: Dict[str, Any], domain: str) -> Tuple[int, List[str]]:
    if not domain:
        return 0, []

    profile = DOMAIN_PROFILES.get(domain, {})
    terms = profile.get("keywords", [])
    text = _repo_text(repo)
    hits = _contains_any(text, terms)

    # If it came from an expanded domain query, give a smaller relevance credit
    # even if GitHub did not expose enough topics/description to match locally.
    matched_query = str(repo.get("_matched_query") or "").lower()
    query_hits = _contains_any(matched_query, profile.get("queries", []))

    if hits:
        return min(28, 12 + len(hits) * 4), hits[:5]

    if query_hits or repo.get("is_github_search"):
        return 8, ["GitHub domain search"]

    return -12, []


def _match_tech_stack(repo: Dict[str, Any], stacks: List[str]) -> Tuple[int, List[str]]:
    if not stacks:
        return 5, []

    text = _repo_text(repo)
    hits = []

    for stack in stacks:
        aliases = TECH_ALIASES.get(stack, [])
        choices = [str(stack).lower()] + [alias.lower() for alias in aliases]
        if any(choice in text for choice in choices):
            hits.append(stack)

    if hits:
        return min(22, len(hits) * 8), hits[:4]

    return -5, []


def _match_project_type(repo: Dict[str, Any], project_type: str) -> Tuple[int, List[str]]:
    if not project_type or project_type in {"Any", "All", "All project types"}:
        return 0, []

    text = _repo_text(repo)
    aliases = TECH_ALIASES.get(project_type, [])
    choices = [project_type.lower()] + [alias.lower() for alias in aliases]
    hits = [choice for choice in choices if choice in text]

    if hits:
        return 18, [project_type]

    return -6, []


def _match_keywords(repo: Dict[str, Any], keywords: str) -> Tuple[int, List[str]]:
    words = [
        word.strip().lower()
        for word in re.split(r"[\s,]+", str(keywords or ""))
        if len(word.strip()) > 1
    ]
    ignored = {
        "find", "repo", "repos", "project", "projects", "issue", "issues",
        "good", "first", "beginner", "open", "source", "github"
    }
    words = [word for word in words if word not in ignored]

    if not words:
        return 0, []

    text = _repo_text(repo)
    hits = [word for word in words if word in text]

    if hits:
        return min(18, len(hits) * 6), hits[:5]

    return -4, []


def _activity_score(repo: Dict[str, Any]) -> Tuple[int, str]:
    days = _days_since(repo.get("pushed_at") or repo.get("updated_at"))
    if days is None:
        return 0, "Unknown activity"

    if days <= 30:
        return 12, "updated recently"
    if days <= 120:
        return 7, "updated this season"
    if days <= 365:
        return 3, "updated this year"
    return -4, "possibly stale"


def _trust_score(repo: Dict[str, Any]) -> Tuple[int, str]:
    stars = _safe_int(repo.get("stars", 0))
    forks = _safe_int(repo.get("forks", 0))

    score = 0
    if stars >= 10000:
        score += 10
    elif stars >= 1000:
        score += 8
    elif stars >= 100:
        score += 5
    elif stars >= 20:
        score += 2

    if forks >= 500:
        score += 5
    elif forks >= 100:
        score += 3
    elif forks >= 20:
        score += 1

    if score >= 10:
        return score, "strong project signal"
    if score >= 5:
        return score, "trusted repo"
    if score > 0:
        return score, "some community signal"
    return 0, "new/small repo"


def score_repository_match(
    repo: Dict[str, Any],
    *,
    domain: str = "",
    languages: Optional[List[str]] = None,
    tech_stack: Optional[List[str]] = None,
    project_type: str = "",
    keywords: str = "",
) -> Dict[str, Any]:
    languages = languages or []
    tech_stack = tech_stack or []

    score = 50  # neutral baseline so not every repo becomes zero
    reasons: List[str] = []
    details: Dict[str, Any] = {}

    domain_delta, domain_hits = _match_domain(repo, domain)
    score += domain_delta
    if domain_hits:
        reasons.append(f"{domain} match")
        details["domain_hits"] = domain_hits

    lang_delta, lang_hits = _match_language(repo, languages)
    score += lang_delta
    if lang_hits:
        reasons.append("Language: " + ", ".join(lang_hits))
        details["language_hits"] = lang_hits

    stack_delta, stack_hits = _match_tech_stack(repo, tech_stack)
    score += stack_delta
    if stack_hits:
        reasons.append("Stack: " + ", ".join(stack_hits))
        details["stack_hits"] = stack_hits

    type_delta, type_hits = _match_project_type(repo, project_type)
    score += type_delta
    if type_hits:
        reasons.append("Type: " + ", ".join(type_hits))
        details["project_type_hits"] = type_hits

    keyword_delta, keyword_hits = _match_keywords(repo, keywords)
    score += keyword_delta
    if keyword_hits:
        reasons.append("Keyword: " + ", ".join(keyword_hits))
        details["keyword_hits"] = keyword_hits

    activity_delta, activity_reason = _activity_score(repo)
    score += activity_delta
    reasons.append(activity_reason)
    details["activity"] = activity_reason

    trust_delta, trust_reason = _trust_score(repo)
    score += trust_delta
    if trust_delta:
        reasons.append(trust_reason)
    details["trust"] = trust_reason

    open_issues = _safe_int(repo.get("open_issues", 0))
    if open_issues > 0:
        score += min(8, open_issues / 20)
        reasons.append(f"{open_issues} open issues")

    final = int(max(0, min(100, round(score))))

    if final >= 78:
        strength = "Strong match"
    elif final >= 62:
        strength = "Good match"
    elif final >= 48:
        strength = "Possible match"
    else:
        strength = "Weak match"

    return {
        "score": final,
        "strength": strength,
        "reasons": _unique(reasons)[:5],
        "details": details,
    }


def enrich_repo_match(
    repo: Dict[str, Any],
    *,
    domain: str = "",
    languages: Optional[List[str]] = None,
    tech_stack: Optional[List[str]] = None,
    project_type: str = "",
    keywords: str = "",
) -> Dict[str, Any]:
    item = dict(repo)
    match = score_repository_match(
        item,
        domain=domain,
        languages=languages,
        tech_stack=tech_stack,
        project_type=project_type,
        keywords=keywords,
    )

    item["repo_match_score"] = match["score"]
    item["match_strength"] = match["strength"]
    item["match_reasons"] = match["reasons"]
    item["match_details"] = match["details"]
    item["matched_because"] = " · ".join(match["reasons"][:4]) or "General repository match"
    return item


def _dedupe_repos(repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    result = []

    for repo in repos:
        key = str(repo.get("full_name") or repo.get("repo_full_name") or repo.get("name") or "").lower()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        result.append(repo)

    return result


# ─────────────────────────────────────────────────────────────
# Query building
# ─────────────────────────────────────────────────────────────

def get_domain_project_types(domain: str) -> List[str]:
    profile = DOMAIN_PROFILES.get(domain, {})
    return ["Any"] + list(profile.get("project_types", []))


def get_domain_tech_stacks(domain: str) -> List[str]:
    profile = DOMAIN_PROFILES.get(domain, {})
    terms = profile.get("keywords", [])
    # Keep UI-friendly items first if the profile has project types.
    return _unique(profile.get("project_types", []) + terms[:18])


def _build_query_variants(
    *,
    keywords: str = "",
    domain: str = "",
    tech_stack: Optional[List[str]] = None,
    languages: Optional[List[str]] = None,
    project_type: str = "",
) -> List[str]:
    tech_stack = tech_stack or []
    languages = languages or []

    direct = parse_github_url_or_repo(keywords)
    if direct.get("is_direct"):
        return []

    profile = DOMAIN_PROFILES.get(domain, {})
    base_queries = []

    if keywords and len(str(keywords).strip()) > 1:
        base_queries.append(str(keywords).strip())

    if project_type and project_type not in {"Any", "All", "All project types"}:
        aliases = TECH_ALIASES.get(project_type, [])
        base_queries.extend([project_type] + aliases[:3])

    # Stack choices are OR in user thinking, so make separate query branches.
    for stack in tech_stack[:4]:
        aliases = TECH_ALIASES.get(stack, [])
        base_queries.append(str(stack))
        base_queries.extend(aliases[:2])

    base_queries.extend(profile.get("queries", [])[:8])

    if not base_queries:
        base_queries = [domain or "open source"]

    # Language OR support: generate variants per language.
    language_parts = []
    if languages:
        for lang in languages[:4]:
            if lang == "HTML/CSS":
                language_parts.extend(["language:HTML", "language:CSS"])
            elif lang == "C#":
                language_parts.append('language:"C#"')
            elif lang == "C++":
                language_parts.append('language:"C++"')
            else:
                language_parts.append(f"language:{lang}")
    else:
        language_parts = [""]

    queries = []
    for base in _unique(base_queries)[:12]:
        for lang_part in language_parts:
            q = f"{base} {lang_part}".strip()
            # Good GitHub discovery defaults.
            q = f"{q} archived:false"
            queries.append(q)

    return _unique(queries)[:18]


# ─────────────────────────────────────────────────────────────
# Public repo search APIs
# ─────────────────────────────────────────────────────────────

def search_github_repositories(
    keywords: str = "",
    domain: str = "",
    tech_stack: Optional[List[str]] = None,
    languages: Optional[List[str]] = None,
    sort_by: str = "Best match",
    per_page: int = 18,
    project_type: str = "",
) -> List[Dict[str, Any]]:
    """
    Smart public GitHub repo search.

    Supports:
    - normal discovery filters
    - domain-expanded search
    - multiple languages as OR by issuing multiple queries
    - direct repo/issue URL or owner/repo input
    """
    tech_stack = tech_stack or []
    languages = languages or []

    direct = parse_github_url_or_repo(keywords)
    if direct.get("is_direct") and direct.get("full_name"):
        try:
            repo = get_repository_metadata(direct["full_name"])
            repo["_direct_issue_number"] = direct.get("issue_number")
            repo["matched_because"] = "Direct GitHub repo/issue link"
            repo["repo_match_score"] = 100
            repo["match_strength"] = "Direct match"
            return [repo]
        except Exception:
            return []

    queries = _build_query_variants(
        keywords=keywords,
        domain=domain,
        tech_stack=tech_stack,
        languages=languages,
        project_type=project_type,
    )

    sort = "updated"
    order = "desc"
    if sort_by == "Most Open Issues":
        sort = "stars"  # GitHub repo search does not sort by open issues reliably.
    elif sort_by == "Name A-Z":
        sort = ""
        order = "asc"
    elif sort_by == "Recently Updated":
        sort = "updated"
    elif sort_by in {"Most Good First Issues", "Beginner Friendly First", "Best match"}:
        sort = "best-match"

    candidates: List[Dict[str, Any]] = []

    # Keep each query small to avoid rate limit and duplicates.
    query_per_page = max(5, min(10, per_page))

    for query in queries:
        params = {
            "q": query,
            "per_page": query_per_page,
            "page": 1,
        }
        if sort and sort != "best-match":
            params["sort"] = sort
            params["order"] = order

        try:
            data = _get(f"{GITHUB_API}/search/repositories", params=params)
        except Exception:
            continue

        for item in data.get("items", []) or []:
            normalized = _normalize_repo(item, source="github", matched_query=query)
            enriched = enrich_repo_match(
                normalized,
                domain=domain,
                languages=languages,
                tech_stack=tech_stack,
                project_type=project_type,
                keywords=keywords,
            )
            candidates.append(enriched)

    candidates = _dedupe_repos(candidates)

    # Do not hard reject too early. Rank first, then keep decent results.
    candidates.sort(
        key=lambda repo: (
            _safe_int(repo.get("repo_match_score", 0)),
            _safe_int(repo.get("stars", 0)),
            _safe_int(repo.get("open_issues", 0)),
        ),
        reverse=True,
    )

    # Keep enough variety, but avoid very weak garbage when we have better matches.
    strong = [repo for repo in candidates if _safe_int(repo.get("repo_match_score", 0)) >= 48]
    final = strong if len(strong) >= 6 else candidates

    return final[:per_page]


def search_gssoc_projects(
    keywords: str = "",
    tech_stack: str = "",
    language: str = "",
    difficulty: str = "",
    sort_by: str = "Most Good First Issues",
) -> List[Dict[str, Any]]:
    """
    Optional GSSoC source.

    Your earlier app expected this function, but public GSSoC tracker APIs
    change often. This implementation falls back to GitHub search so your UI
    does not break when the tracker is unavailable.
    """
    stacks = _as_list(tech_stack)
    langs = _as_list(language)
    query = " ".join(part for part in [keywords, tech_stack, "good first issue help wanted"] if part)

    results = search_github_repositories(
        keywords=query,
        domain="",
        tech_stack=stacks,
        languages=langs,
        sort_by=sort_by,
        per_page=12,
    )

    for repo in results:
        repo["is_gssoc"] = False
        repo["source"] = "github-fallback"

    return results


def get_gssoc_filter_options() -> Dict[str, List[str]]:
    return {
        "tech_stacks": _unique(
            [
                "Python", "JavaScript", "TypeScript", "React", "Next.js",
                "FastAPI", "Django", "Flask", "Node.js", "Express",
                "Docker", "Kubernetes", "PostgreSQL", "MongoDB", "Redis",
                "CLI", "Document Converter", "Markdown Tool", "Parser",
                "API Client", "Automation", "Testing", "Documentation",
                "PyTorch", "TensorFlow", "Scikit-learn", "Pandas", "NumPy",
                "Solidity", "Web3", "Cybersecurity", "DevOps"
            ]
        ),
        "languages": [
            "Python", "JavaScript", "TypeScript", "Java", "C", "C++",
            "Go", "Rust", "Kotlin", "Swift", "PHP", "Ruby", "C#",
            "HTML/CSS", "SQL", "Solidity", "Shell", "Dart", "Scala"
        ],
        "difficulties": ["Beginner Friendly", "Intermediate", "Advanced"],
        "domains": list(DOMAIN_PROFILES.keys()),
    }


# ─────────────────────────────────────────────────────────────
# Repo metadata / README / issues
# ─────────────────────────────────────────────────────────────

def get_repository_metadata(full_name: str) -> Dict[str, Any]:
    full_name = str(full_name or "").strip()
    if not full_name:
        return {}

    data = _get(f"{GITHUB_API}/repos/{full_name}")
    repo = _normalize_repo(data, source="github", matched_query="direct metadata")
    repo["repo_match_score"] = repo.get("repo_match_score", 100)
    repo["match_strength"] = repo.get("match_strength", "Direct match")
    repo["matched_because"] = repo.get("matched_because", "Loaded directly from GitHub")
    return repo


def get_repository_readme(full_name: str) -> str:
    try:
        data = _get(f"{GITHUB_API}/repos/{full_name}/readme")
        content = data.get("content", "")
        encoding = data.get("encoding", "")
        if encoding == "base64" and content:
            return base64.b64decode(content).decode("utf-8", errors="ignore")
        return ""
    except Exception:
        return ""


def _normalize_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    labels = []
    for label in issue.get("labels", []) or []:
        if isinstance(label, dict):
            labels.append(label.get("name", ""))
        else:
            labels.append(str(label))

    assignee = issue.get("assignee")
    assignees = issue.get("assignees") or []

    return {
        "id": issue.get("id"),
        "number": issue.get("number"),
        "title": issue.get("title") or "",
        "body": issue.get("body") or "",
        "state": issue.get("state") or "",
        "url": issue.get("html_url") or "",
        "html_url": issue.get("html_url") or "",
        "api_url": issue.get("url") or "",
        "comments_url": issue.get("comments_url") or "",
        "comments": _safe_int(issue.get("comments", 0)),
        "labels": _unique(labels),
        "assignee": assignee.get("login") if isinstance(assignee, dict) else assignee,
        "assignees": [
            item.get("login", "") for item in assignees if isinstance(item, dict)
        ],
        "created_at": issue.get("created_at") or "",
        "updated_at": issue.get("updated_at") or "",
        "user": (issue.get("user") or {}).get("login") if isinstance(issue.get("user"), dict) else "",
        "pull_request": issue.get("pull_request"),
    }


def fetch_open_issues(full_name: str) -> List[Dict[str, Any]]:
    if not full_name:
        return []

    params = {
        "state": "open",
        "per_page": 100,
        "sort": "updated",
        "direction": "desc",
    }

    try:
        data = _get(f"{GITHUB_API}/repos/{full_name}/issues", params=params)
    except Exception as exc:
        raise RuntimeError(
            f"GitHub could not load issues for {full_name}. "
            f"The repo may be private, renamed, unavailable, or rate limited. Details: {exc}"
        )

    issues = []
    for issue in data or []:
        # GitHub returns PRs in the issues endpoint too.
        if issue.get("pull_request"):
            continue
        issues.append(_normalize_issue(issue))

    return issues


def get_issue_context(full_name: str, issue_number: int, max_comments: int = 5) -> Dict[str, Any]:
    issue_number = int(issue_number)

    issue_raw = _get(f"{GITHUB_API}/repos/{full_name}/issues/{issue_number}")
    issue = _normalize_issue(issue_raw)

    comments: List[Dict[str, Any]] = []
    if max_comments > 0:
        try:
            comment_data = _get(
                f"{GITHUB_API}/repos/{full_name}/issues/{issue_number}/comments",
                params={"per_page": max_comments, "page": 1},
            )
            for comment in comment_data or []:
                comments.append(
                    {
                        "user": (comment.get("user") or {}).get("login", ""),
                        "body": comment.get("body") or "",
                        "created_at": comment.get("created_at") or "",
                        "updated_at": comment.get("updated_at") or "",
                        "html_url": comment.get("html_url") or "",
                    }
                )
        except Exception:
            comments = []

    repo = {}
    try:
        repo = get_repository_metadata(full_name)
    except Exception:
        repo = {"repo_full_name": full_name, "full_name": full_name}

    # Keep the raw full issue body. Issue Coach should use this, not the truncated summary.
    return {
        "repo": repo,
        "repo_full_name": full_name,
        "issue": issue,
        "issue_number": issue_number,
        "title": issue.get("title", ""),
        "body": issue.get("body", ""),
        "labels": issue.get("labels", []),
        "comments": comments,
        "comment_count": issue.get("comments", 0),
        "url": issue.get("html_url", ""),
        "html_url": issue.get("html_url", ""),
        "source": "github",
    }


# ─────────────────────────────────────────────────────────────
# Convenience helpers for direct URL mode
# ─────────────────────────────────────────────────────────────

def load_from_github_input(value: str) -> Dict[str, Any]:
    """
    Optional helper for UI direct mode.

    Returns:
    {
      "kind": "repo" | "issue" | "unknown",
      "repo": repo_metadata,
      "issue_context": issue_context or None,
      "full_name": "owner/repo",
      "issue_number": 123 or None
    }
    """
    parsed = parse_github_url_or_repo(value)
    if not parsed.get("is_direct") or not parsed.get("full_name"):
        return {"kind": "unknown", "repo": None, "issue_context": None}

    full_name = parsed["full_name"]
    repo = get_repository_metadata(full_name)
    issue_number = parsed.get("issue_number")

    if issue_number:
        return {
            "kind": "issue",
            "repo": repo,
            "issue_context": get_issue_context(full_name, issue_number, max_comments=5),
            "full_name": full_name,
            "issue_number": issue_number,
        }

    return {
        "kind": "repo",
        "repo": repo,
        "issue_context": None,
        "full_name": full_name,
        "issue_number": None,
    }
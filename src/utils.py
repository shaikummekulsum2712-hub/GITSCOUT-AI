"""General utility helpers for GitScout AI."""

import json
import re
from typing import Any, Dict, Optional


def clean_text(value: Optional[str]) -> str:
    """Clean a text input by normalizing whitespace and removing invisible characters."""
    if not value:
        return ""
    text = re.sub(r"\s+", " ", value).strip()
    return text


def clean_markdown(value: Optional[str]) -> str:
    """Remove markdown formatting and collapse long whitespace in repository or issue text."""
    if not value:
        return ""
    text = re.sub(r"```[\s\S]*?```", "", value)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[\*_]{1,2}", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def safe_json_loads(value: str, default: Optional[Any] = None) -> Any:
    """Parse JSON safely and return a default value on failure."""
    if not value or not isinstance(value, str):
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def format_repo_label(repo: Dict[str, Any]) -> str:
    """Format a repository label summary for display in the UI."""
    language = repo.get("language", "Unknown")
    stars = repo.get("stars", 0)
    return f"{language} · ⭐ {stars}"


def ensure_list(value: Optional[Any]) -> list:
    """Convert a value to a list if possible, otherwise return an empty list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]

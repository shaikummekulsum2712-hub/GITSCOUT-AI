from datetime import datetime, timezone
from typing import Dict, List, Optional


DIFFICULTY_WEIGHTS = {
    "Beginner": 1.0,
    "Intermediate": 0.78,
    "Advanced": 0.55,
}


def _safe_float(value, default: float = 5.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _age_score(created_at: Optional[str]) -> float:
    if not created_at:
        return 0.55

    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return 0.55

    age_days = (datetime.now(timezone.utc) - created).days

    if age_days <= 7:
        return 1.0
    if age_days <= 30:
        return 0.85
    if age_days <= 90:
        return 0.65
    return 0.45


def _comment_score(comments: int) -> float:
    if comments == 0:
        return 1.0
    if comments <= 2:
        return 0.9
    if comments <= 5:
        return 0.72
    if comments <= 10:
        return 0.48
    return 0.25


def competition_level(comments: int, ai_competition=None) -> str:
    ai_score = _safe_float(ai_competition, default=0)

    if ai_score >= 8 or comments >= 8:
        return "High"
    if ai_score >= 5 or comments >= 4:
        return "Medium"
    if comments <= 1:
        return "Very Low"
    return "Low"


def _assignee_score(assignee: Optional[str]) -> float:
    return 1.0 if not assignee else 0.25


def _label_bonus(labels: List[str]) -> float:
    labels = [str(label).lower() for label in labels or []]
    bonus = 1.0

    if "good first issue" in labels:
        bonus += 0.4
    if "help wanted" in labels:
        bonus += 0.28
    if "documentation" in labels or "docs" in labels:
        bonus += 0.18
    if "bug" in labels:
        bonus += 0.12
    if "enhancement" in labels:
        bonus += 0.08

    return bonus


def _difficulty_factor(difficulty: str) -> float:
    return DIFFICULTY_WEIGHTS.get(str(difficulty), 0.7)


def _skill_match_factor(skill_match) -> float:
    score = _safe_float(skill_match, default=6)
    return max(0.0, min(score / 10.0, 1.0))


def _competition_factor(comments: int, competition=None) -> float:
    ai_score = _safe_float(competition, default=comments + 1)
    normalized = max(1.0, min(ai_score, 10.0))
    comment_pressure = min(comments / 10.0, 1.0)

    # 1.0 is best. Lower means more competition.
    return max(0.15, 1.0 - ((normalized - 1) / 9) * 0.5 - comment_pressure * 0.25)


def _compute_issue_score(issue: Dict, user_profile: Dict) -> float:
    comments = _safe_int(issue.get("comments", 0))
    difficulty = issue.get("difficulty", "Intermediate")

    score = (
        2.4 * _assignee_score(issue.get("assignee"))
        + 1.8 * _comment_score(comments)
        + 1.2 * _age_score(issue.get("created_at"))
        + 1.7 * _label_bonus(issue.get("labels", []))
        + 2.2 * _skill_match_factor(issue.get("skill_match", 6))
        + 1.1 * _difficulty_factor(difficulty)
        + 1.5 * _competition_factor(comments, issue.get("competition"))
    )

    if user_profile.get("skill_level") == "Beginner" and difficulty == "Beginner":
        score += 0.9

    return round(score, 3)


def rank_issues(issues: List[Dict], user_profile: Dict) -> List[Dict]:
    ranked = []

    for issue in issues:
        if issue.get("state") and issue.get("state") != "open":
            continue

        if issue.get("pull_request"):
            continue

        comments = _safe_int(issue.get("comments", 0))
        item = dict(issue)
        item["competition_level"] = competition_level(comments, item.get("competition"))
        item["rank_score"] = _compute_issue_score(item, user_profile)
        item["scout_score"] = min(100, max(0, round(item["rank_score"] * 8.5)))

        ranked.append(item)

    ranked.sort(key=lambda item: item["rank_score"], reverse=True)
    return ranked

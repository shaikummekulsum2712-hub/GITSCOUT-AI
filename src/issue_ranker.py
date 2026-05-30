from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────
# Premium GitScout Issue Ranker
# ─────────────────────────────────────────────────────────────
#
# Goal:
# Rank issues in a way that feels explainable, not random.
#
# It scores an issue on 7 visible factors:
# 1. Availability      -> unassigned/open issue
# 2. Beginner signal   -> good first issue/help wanted/docs labels
# 3. Competition       -> comments count + discussion pressure
# 4. Freshness         -> not too stale, not too chaotic
# 5. Task clarity      -> title/body has enough detail
# 6. Skill match       -> labels/title/body match user skills/interests
# 7. Effort fit        -> issue looks small enough for beginner/intermediate
#
# Every ranked issue gets:
# - scout_score: 0-100
# - fit_label: Excellent fit / Good fit / Possible fit / Stretch
# - rank_explanation: list of factor ratings shown in UI
# - score_tooltip: compact hover text
# - competition_level: Very Low / Low / Medium / High
# ─────────────────────────────────────────────────────────────


BEGINNER_LABELS = {
    "good first issue",
    "good-first-issue",
    "beginner",
    "beginner friendly",
    "level: beginner",
    "level-beginner",
    "first timers only",
    "first-timers-only",
    "easy",
    "easy pick",
}

HELPFUL_LABELS = {
    "help wanted",
    "up for grabs",
    "available",
    "ready",
    "triaged",
}

DOC_LABELS = {
    "documentation",
    "docs",
    "readme",
    "examples",
    "tutorial",
}

RISKY_LABELS = {
    "blocked",
    "needs discussion",
    "needs design",
    "rfc",
    "breaking change",
    "priority: critical",
    "critical",
    "security",
}

BIG_TASK_WORDS = {
    "architecture",
    "migration",
    "rewrite",
    "refactor entire",
    "large",
    "complex",
    "breaking",
    "major",
    "redesign",
    "overhaul",
}

SMALL_TASK_WORDS = {
    "docs",
    "readme",
    "typo",
    "example",
    "test",
    "unit test",
    "loading",
    "button",
    "message",
    "error message",
    "validation",
    "minor",
    "small",
}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clean_label(label: Any) -> str:
    if isinstance(label, dict):
        return str(label.get("name", "")).strip().lower()
    return str(label or "").strip().lower()


def _labels(issue: Dict[str, Any]) -> List[str]:
    raw = issue.get("labels", []) or []
    if isinstance(raw, str):
        raw = [part.strip() for part in raw.split(",")]
    return [_clean_label(label) for label in raw if _clean_label(label)]


def _text(issue: Dict[str, Any]) -> str:
    parts = [
        issue.get("title", ""),
        issue.get("body", ""),
        " ".join(_labels(issue)),
    ]
    return " ".join(str(part or "") for part in parts).lower()


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def _days_old(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None

    try:
        created = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        return max(0, (datetime.now(timezone.utc) - created).days)
    except Exception:
        return None


def _factor(label: str, score: float, reason: str) -> Dict[str, Any]:
    return {
        "label": label,
        "score": round(_clamp(score), 1),
        "reason": reason,
    }


def _availability_factor(issue: Dict[str, Any]) -> Dict[str, Any]:
    assignee = issue.get("assignee") or issue.get("assignees")

    if not assignee:
        return _factor("Availability", 100, "No assignee found, so it may still be available.")

    return _factor("Availability", 25, "Already assigned, so your chance of getting it is lower.")


def _beginner_signal_factor(issue: Dict[str, Any]) -> Dict[str, Any]:
    labels = set(_labels(issue))
    text = _text(issue)

    score = 45
    reasons = []

    if labels & BEGINNER_LABELS:
        score += 35
        reasons.append("beginner-friendly label")
    if labels & HELPFUL_LABELS:
        score += 18
        reasons.append("help-wanted/ready label")
    if labels & DOC_LABELS:
        score += 12
        reasons.append("docs/examples label")
    if any(word in text for word in SMALL_TASK_WORDS):
        score += 8
        reasons.append("small-task wording")

    if not reasons:
        reasons.append("no strong beginner label detected")

    return _factor("Beginner signal", score, ", ".join(reasons).capitalize() + ".")


def _competition_factor(issue: Dict[str, Any]) -> Dict[str, Any]:
    comments = _safe_int(issue.get("comments", 0))
    participants = _safe_int(issue.get("participants", 0))
    reactions = _safe_int(issue.get("reactions", 0))

    # Lower comments = better. Participants/reactions can indicate attention.
    pressure = comments + (participants * 0.7) + (reactions * 0.15)

    if pressure <= 0:
        return _factor("Competition", 100, "No comments yet, very low visible competition.")
    if pressure <= 2:
        return _factor("Competition", 90, f"Only {comments} comment(s), low competition.")
    if pressure <= 5:
        return _factor("Competition", 72, f"{comments} comment(s), still manageable.")
    if pressure <= 10:
        return _factor("Competition", 48, f"{comments} comment(s), moderate competition.")
    return _factor("Competition", 25, f"{comments} comment(s), likely crowded.")


def competition_level(comments: int, ai_competition: Any = None) -> str:
    ai_score = _safe_float(ai_competition, default=0)

    if ai_score >= 8 or comments >= 8:
        return "High"
    if ai_score >= 5 or comments >= 4:
        return "Medium"
    if comments <= 1:
        return "Very Low"
    return "Low"


def _freshness_factor(issue: Dict[str, Any]) -> Dict[str, Any]:
    days = _days_old(issue.get("created_at") or issue.get("updated_at"))

    if days is None:
        return _factor("Freshness", 55, "No date found, using neutral freshness.")

    if days <= 2:
        return _factor("Freshness", 90, "Very recent issue.")
    if days <= 14:
        return _factor("Freshness", 100, "Recent enough and not too old.")
    if days <= 45:
        return _factor("Freshness", 82, f"{days} days old, still likely relevant.")
    if days <= 120:
        return _factor("Freshness", 58, f"{days} days old, may still be valid.")
    return _factor("Freshness", 35, f"{days} days old, may be stale.")


def _clarity_factor(issue: Dict[str, Any]) -> Dict[str, Any]:
    title = str(issue.get("title") or "")
    body = str(issue.get("body") or "")
    text = _text(issue)

    body_len = len(body.strip())
    score = 45
    reasons = []

    if len(title) >= 18:
        score += 10
        reasons.append("specific title")
    if body_len >= 180:
        score += 22
        reasons.append("detailed body")
    elif body_len >= 60:
        score += 12
        reasons.append("some context")
    else:
        reasons.append("short issue body")

    if any(word in text for word in ["expected", "actual", "steps", "reproduce", "proposed", "solution", "changes"]):
        score += 18
        reasons.append("clear expected/proposed behavior")

    if any(word in text for word in ["screenshot", "error", "traceback", "logs"]):
        score += 8
        reasons.append("debugging evidence")

    return _factor("Task clarity", score, ", ".join(reasons).capitalize() + ".")


def _skill_match_factor(issue: Dict[str, Any], user_profile: Dict[str, Any]) -> Dict[str, Any]:
    text = _text(issue)

    skills = user_profile.get("skills") or user_profile.get("user_skills") or []
    interests = user_profile.get("interests") or user_profile.get("ml_interests") or []
    contribution_types = user_profile.get("contribution_types") or []

    wanted = [str(x).lower() for x in skills + interests + contribution_types if str(x).strip()]
    if not wanted:
        wanted = ["python", "docs", "bug", "documentation"]

    hits = []
    for item in wanted:
        # Handle common beginner phrases.
        normalized = item.replace(" basics", "").replace("/", " ").strip()
        if normalized and normalized in text:
            hits.append(item)

    labels = set(_labels(issue))
    if labels & DOC_LABELS and any(x in wanted for x in ["docs", "documentation"]):
        hits.append("documentation")
    if "bug" in labels and "bug" in wanted:
        hits.append("bug")

    unique_hits = sorted(set(hits))

    if len(unique_hits) >= 3:
        return _factor("Skill match", 95, "Matches " + ", ".join(unique_hits[:4]) + ".")
    if len(unique_hits) == 2:
        return _factor("Skill match", 82, "Matches " + ", ".join(unique_hits) + ".")
    if len(unique_hits) == 1:
        return _factor("Skill match", 68, "Some match: " + unique_hits[0] + ".")
    return _factor("Skill match", 45, "No strong match to selected skills/interests.")


def _effort_fit_factor(issue: Dict[str, Any], user_profile: Dict[str, Any]) -> Dict[str, Any]:
    text = _text(issue)
    labels = set(_labels(issue))
    skill_level = str(user_profile.get("skill_level") or "Beginner").lower()

    score = 62
    reasons = []

    if labels & DOC_LABELS:
        score += 18
        reasons.append("docs work")
    if "good first issue" in labels or labels & BEGINNER_LABELS:
        score += 15
        reasons.append("beginner label")
    if any(word in text for word in SMALL_TASK_WORDS):
        score += 12
        reasons.append("small focused task")
    if any(word in text for word in BIG_TASK_WORDS):
        score -= 25
        reasons.append("large/complex wording")
    if skill_level == "beginner" and any(word in text for word in ["deep learning", "compiler", "cuda", "distributed", "architecture"]):
        score -= 18
        reasons.append("may need advanced context")

    if not reasons:
        reasons.append("neutral effort estimate")

    return _factor("Effort fit", score, ", ".join(reasons).capitalize() + ".")


def _risk_factor(issue: Dict[str, Any]) -> Dict[str, Any]:
    labels = set(_labels(issue))
    text = _text(issue)

    score = 100
    reasons = []

    if labels & RISKY_LABELS:
        score -= 35
        reasons.append("risky/blocked label")
    if any(word in text for word in ["needs discussion", "blocked", "waiting", "duplicate", "stale"]):
        score -= 30
        reasons.append("blocked/stale wording")
    if any(word in text for word in ["breaking change", "security vulnerability", "production incident"]):
        score -= 20
        reasons.append("high-risk area")

    if not reasons:
        reasons.append("no major risk signals")

    return _factor("Risk level", score, ", ".join(reasons).capitalize() + ".")


def build_rank_explanation(issue: Dict[str, Any], user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        _availability_factor(issue),
        _beginner_signal_factor(issue),
        _competition_factor(issue),
        _freshness_factor(issue),
        _clarity_factor(issue),
        _skill_match_factor(issue, user_profile),
        _effort_fit_factor(issue, user_profile),
        _risk_factor(issue),
    ]


def _weighted_score(factors: List[Dict[str, Any]]) -> float:
    weights = {
        "Availability": 0.16,
        "Beginner signal": 0.16,
        "Competition": 0.15,
        "Freshness": 0.10,
        "Task clarity": 0.14,
        "Skill match": 0.14,
        "Effort fit": 0.11,
        "Risk level": 0.04,
    }

    total = 0.0
    weight_sum = 0.0

    for factor in factors:
        label = factor["label"]
        weight = weights.get(label, 0.1)
        total += factor["score"] * weight
        weight_sum += weight

    return total / max(weight_sum, 0.001)


def fit_label(score: int) -> str:
    if score >= 82:
        return "Excellent fit"
    if score >= 68:
        return "Good fit"
    if score >= 52:
        return "Possible fit"
    return "Stretch"


def score_tooltip(factors: List[Dict[str, Any]]) -> str:
    lines = []
    for factor in factors:
        lines.append(f"{factor['label']}: {factor['score']}/100 — {factor['reason']}")
    return "\n".join(lines)


def _compact_score_reasons(factors: List[Dict[str, Any]]) -> List[str]:
    # Show top 3 strongest reasons + biggest weakness.
    sorted_good = sorted(factors, key=lambda f: f["score"], reverse=True)
    sorted_bad = sorted(factors, key=lambda f: f["score"])

    reasons = []
    for factor in sorted_good[:3]:
        reasons.append(f"{factor['label']}: {int(round(factor['score']))}/100")

    weakest = sorted_bad[0]
    if weakest["score"] < 55:
        reasons.append(f"Watch: {weakest['label']} {int(round(weakest['score']))}/100")

    return reasons


def rank_issues(issues: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    ranked: List[Dict[str, Any]] = []

    for issue in issues or []:
        # Only open issues, never PRs.
        if issue.get("state") and str(issue.get("state")).lower() != "open":
            continue
        if issue.get("pull_request"):
            continue

        item = dict(issue)
        comments = _safe_int(item.get("comments", 0))

        factors = build_rank_explanation(item, user_profile)
        score = int(round(_clamp(_weighted_score(factors), 0, 100)))

        item["rank_factors"] = factors
        item["rank_explanation"] = factors
        item["score_tooltip"] = score_tooltip(factors)
        item["score_reasons"] = _compact_score_reasons(factors)
        item["competition_level"] = competition_level(comments, item.get("competition"))
        item["scout_score"] = score
        item["fit_label"] = fit_label(score)

        # Keep rank_score for old UI compatibility.
        item["rank_score"] = round(score / 100, 4)

        ranked.append(item)

    ranked.sort(
        key=lambda item: (
            item.get("scout_score", 0),
            -_safe_int(item.get("comments", 0)),
            _safe_int(item.get("number", 0)),
        ),
        reverse=True,
    )

    return ranked
# # from datetime import datetime, timezone
# # from typing import Dict, List, Optional


# # DIFFICULTY_WEIGHTS = {
# #     "Beginner": 1.0,
# #     "Intermediate": 0.8,
# #     "Advanced": 0.6,
# # }


# # def _age_score(created_at: Optional[str]) -> float:
# #     if not created_at:
# #         return 0.0

# #     try:
# #         created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
# #     except ValueError:
# #         return 0.0

# #     age_days = (datetime.now(timezone.utc) - created).days
# #     if age_days <= 7:
# #         return 1.0
# #     if age_days <= 30:
# #         return 0.8
# #     if age_days <= 90:
# #         return 0.6
# #     return 0.4


# # def _comment_score(comments: int) -> float:
# #     if comments <= 1:
# #         return 1.0
# #     if comments <= 5:
# #         return 0.8
# #     if comments <= 10:
# #         return 0.6
# #     return 0.4


# # def _assignee_score(assignee: Optional[str]) -> float:
# #     return 1.0 if not assignee else 0.5


# # def _label_bonus(labels: List[str]) -> float:
# #     normalized = [label.lower() for label in labels or []]
# #     if "good first issue" in normalized or "beginner" in normalized:
# #         return 1.2
# #     if "help wanted" in normalized:
# #         return 1.1
# #     return 1.0


# # def _difficulty_factor(difficulty: str) -> float:
# #     return DIFFICULTY_WEIGHTS.get(difficulty, 0.7)


# # def _skill_match_factor(skill_match: float) -> float:
# #     try:
# #         score = float(skill_match)
# #     except (TypeError, ValueError):
# #         return 0.7
# #     return min(max(score / 10.0, 0.0), 1.0)


# # def _competition_penalty(competition: float) -> float:
# #     try:
# #         score = float(competition)
# #     except (TypeError, ValueError):
# #         return 0.7
# #     return max(0.0, 1.0 - (score / 10.0) * 0.4)


# # def _compute_issue_score(issue: Dict, user_profile: Dict) -> float:
# #     comments = issue.get("comments", 0)
# #     assignee = issue.get("assignee")
# #     labels = issue.get("labels", [])
# #     difficulty = issue.get("difficulty", "Intermediate")
# #     skill_match = issue.get("skill_match", 5)
# #     competition = issue.get("competition", 5)

# #     age_factor = _age_score(issue.get("created_at"))
# #     comment_factor = _comment_score(comments)
# #     assignee_factor = _assignee_score(assignee)
# #     label_bonus = _label_bonus(labels)
# #     difficulty_factor = _difficulty_factor(difficulty)
# #     skill_match_factor = _skill_match_factor(skill_match)
# #     competition_penalty = _competition_penalty(competition)

# #     score = (
# #         2.0 * assignee_factor
# #         + 1.4 * comment_factor
# #         + 1.2 * age_factor
# #         + 1.5 * label_bonus
# #         + 2.0 * skill_match_factor
# #         + 1.0 * difficulty_factor
# #         + 1.0 * competition_penalty
# #     )

# #     if user_profile.get("skill_level", "Beginner") == "Beginner" and difficulty == "Beginner":
# #         score += 1.0

# #     return round(score, 3)


# # def rank_issues(issues: List[Dict], user_profile: Dict) -> List[Dict]:
# #     ranked = []
# #     for issue in issues:
# #         if issue.get("state") != "open":
# #             continue

# #         if issue.get("pull_request"):
# #             continue

# #         score = _compute_issue_score(issue, user_profile)
# #         ranked.append({**issue, "rank_score": score})

# #     ranked.sort(key=lambda item: item["rank_score"], reverse=True)
# #     return ranked
# from datetime import datetime, timezone
# from typing import Dict, List, Optional


# DIFFICULTY_WEIGHTS = {
#     "Beginner": 1.0,
#     "Intermediate": 0.78,
#     "Advanced": 0.5,
# }


# def competition_level(comments: int) -> str:
#     if comments == 0:
#         return "Very Low"
#     if comments <= 3:
#         return "Low"
#     if comments <= 7:
#         return "Medium"
#     return "High"


# def _age_score(created_at: Optional[str]) -> float:
#     if not created_at:
#         return 0.5

#     try:
#         created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
#     except ValueError:
#         return 0.5

#     age_days = (datetime.now(timezone.utc) - created).days

#     if age_days <= 14:
#         return 1.0
#     if age_days <= 45:
#         return 0.85
#     if age_days <= 120:
#         return 0.65
#     return 0.45


# def _comment_score(comments: int) -> float:
#     if comments == 0:
#         return 1.0
#     if comments <= 3:
#         return 0.85
#     if comments <= 7:
#         return 0.6
#     return 0.35


# def _assignee_score(assignee: Optional[str]) -> float:
#     return 1.0 if not assignee else 0.2


# def _label_bonus(labels: List[str]) -> float:
#     labels = [label.lower() for label in labels or []]

#     bonus = 1.0

#     if "good first issue" in labels:
#         bonus += 0.35
#     if "help wanted" in labels:
#         bonus += 0.25
#     if "documentation" in labels:
#         bonus += 0.18
#     if "bug" in labels:
#         bonus += 0.1
#     if "enhancement" in labels:
#         bonus += 0.08

#     return bonus


# def _difficulty_factor(difficulty: str) -> float:
#     return DIFFICULTY_WEIGHTS.get(str(difficulty), 0.7)


# def _skill_match_factor(skill_match) -> float:
#     try:
#         return max(0.0, min(float(skill_match) / 10.0, 1.0))
#     except (TypeError, ValueError):
#         return 0.6


# def _competition_factor(competition) -> float:
#     try:
#         score = float(competition)
#     except (TypeError, ValueError):
#         score = 5

#     return max(0.2, 1.0 - ((score - 1) / 9) * 0.65)


# def _compute_issue_score(issue: Dict, user_profile: Dict) -> float:
#     comments = int(issue.get("comments", 0) or 0)
#     difficulty = issue.get("difficulty", "Intermediate")

#     score = (
#         2.2 * _assignee_score(issue.get("assignee"))
#         + 1.7 * _comment_score(comments)
#         + 1.3 * _age_score(issue.get("created_at"))
#         + 1.6 * _label_bonus(issue.get("labels", []))
#         + 2.4 * _skill_match_factor(issue.get("skill_match", 6))
#         + 1.2 * _difficulty_factor(difficulty)
#         + 1.4 * _competition_factor(issue.get("competition", comments + 1))
#     )

#     if user_profile.get("skill_level") == "Beginner" and difficulty == "Beginner":
#         score += 1.0

#     return round(score, 3)


# def rank_issues(issues: List[Dict], user_profile: Dict) -> List[Dict]:
#     ranked = []

#     for issue in issues:
#         if issue.get("state") != "open":
#             continue
#         if issue.get("pull_request"):
#             continue

#         comments = int(issue.get("comments", 0) or 0)

#         ranked.append({
#             **issue,
#             "competition_level": competition_level(comments),
#             "rank_score": _compute_issue_score(issue, user_profile),
#         })

#     ranked.sort(key=lambda item: item["rank_score"], reverse=True)
#     return ranked



from datetime import datetime, timezone
from typing import Dict, List, Optional


DIFFICULTY_WEIGHTS = {
    "Beginner": 1.0,
    "Intermediate": 0.8,
    "Advanced": 0.6,
}


def _safe_float(value, default: float = 5.0) -> float:
    try:
        return float(value)
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


def _competition_level(comments: int, ai_competition=None) -> str:
    ai_score = _safe_float(ai_competition, default=0)

    if ai_score >= 8 or comments >= 8:
        return "High"
    if ai_score >= 5 or comments >= 4:
        return "Medium"
    if comments <= 1:
        return "Very Low"
    return "Low"


def _assignee_score(assignee: Optional[str]) -> float:
    return 1.0 if not assignee else 0.35


def _label_bonus(labels: List[str]) -> float:
    labels = [label.lower() for label in labels or []]
    bonus = 1.0

    if "good first issue" in labels:
        bonus += 0.35
    if "help wanted" in labels:
        bonus += 0.25
    if "documentation" in labels or "docs" in labels:
        bonus += 0.15
    if "bug" in labels:
        bonus += 0.1

    return bonus


def _difficulty_factor(difficulty: str) -> float:
    return DIFFICULTY_WEIGHTS.get(str(difficulty), 0.7)


def _skill_match_factor(skill_match) -> float:
    score = _safe_float(skill_match, default=6)
    return max(0.0, min(score / 10.0, 1.0))


def _competition_penalty(competition) -> float:
    score = _safe_float(competition, default=5)
    return max(0.2, 1.0 - ((score / 10.0) * 0.55))


def _compute_issue_score(issue: Dict, user_profile: Dict) -> float:
    comments = int(issue.get("comments", 0) or 0)

    score = (
        2.4 * _assignee_score(issue.get("assignee"))
        + 1.8 * _comment_score(comments)
        + 1.3 * _age_score(issue.get("created_at"))
        + 1.5 * _label_bonus(issue.get("labels", []))
        + 2.4 * _skill_match_factor(issue.get("skill_match", 6))
        + 1.1 * _difficulty_factor(issue.get("difficulty", "Intermediate"))
        + 1.2 * _competition_penalty(issue.get("competition", 5))
    )

    if user_profile.get("skill_level") == "Beginner" and issue.get("difficulty") == "Beginner":
        score += 1.2

    return round(score, 3)


def rank_issues(issues: List[Dict], user_profile: Dict) -> List[Dict]:
    ranked = []

    for issue in issues:
        if issue.get("state") != "open":
            continue

        if issue.get("pull_request"):
            continue

        issue["competition_level"] = _competition_level(
            int(issue.get("comments", 0) or 0),
            issue.get("competition"),
        )

        issue["rank_score"] = _compute_issue_score(issue, user_profile)
        issue["scout_score"] = min(100, round(issue["rank_score"] * 8.5))

        ranked.append(issue)

    ranked.sort(key=lambda item: item["rank_score"], reverse=True)
    return ranked
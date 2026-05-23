import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from dotenv import load_dotenv


MODEL_NAME = "gemini-2.5-flash"


class GeminiAPIError(Exception):
    pass


def _load_gemini_key(api_key: Optional[str] = None) -> str:
    if api_key:
        return api_key

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise GeminiAPIError("Gemini API key not found. Set GEMINI_API_KEY in .env.")

    return key


def _gemini_request(
    prompt: str,
    api_key: Optional[str] = None,
    max_output_tokens: int = 1600,
    temperature: float = 0.2,
) -> str:
    key = _load_gemini_key(api_key)
    genai.configure(api_key=key)

    try:
        model = genai.GenerativeModel(
            MODEL_NAME,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            },
        )
        response = model.generate_content(prompt)
        text = response.text
    except Exception as exc:
        raise GeminiAPIError(f"Gemini request failed: {exc}") from exc

    if not text or not text.strip():
        raise GeminiAPIError("Gemini returned an empty response.")

    return text.strip()


def _clean_json_text(text: str) -> str:
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"^```\s*", "", cleaned).strip()
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    return cleaned



def _loose_json_values(text: str) -> Dict[str, Any]:
    """Extract common JSON-like fields even when the model returns malformed JSON.

    Handles keys like "core problem" as well as "core_problem" and stops each value
    at the next known key. This prevents raw JSON text from leaking into the UI.
    """
    cleaned = _clean_json_text(text)
    keys = [
        "summary",
        "core_problem", "core problem",
        "expected_change", "expected change",
        "why_it_matters", "why it matters",
        "what_to_do", "what to do", "what you'll do",
        "first_step", "first step",
        "difficulty",
        "estimated_time", "estimated time",
        "comment_short", "comment short",
        "comment_detailed", "comment detailed",
    ]

    def extract_string(possible_keys: List[str]) -> str:
        key_pattern = "|".join(re.escape(k) for k in possible_keys)
        all_key_pattern = "|".join(re.escape(k) for k in keys)
        pattern = (
            r'"(?:' + key_pattern + r')"\s*:\s*"'
            r'([\s\S]*?)"'
            r'\s*(?=,\s*"(?:' + all_key_pattern + r'|required_knowledge|files_likely_needed|step_by_step_plan|risks_or_unknowns|competition|skill_match)"|\s*[,}])'
        )
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            return _clean_labeled_text(match.group(1))
        return ""

    def extract_list(possible_keys: List[str]) -> List[str]:
        key_pattern = "|".join(re.escape(k) for k in possible_keys)
        pattern = r'"(?:' + key_pattern + r')"\s*:\s*\[([\s\S]*?)\]'
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if not match:
            return []
        raw = match.group(1)
        items = re.findall(r'"([\s\S]*?)"', raw)
        if not items:
            items = [x.strip(" ,") for x in raw.split(",")]
        return [_clean_labeled_text(item) for item in items if _clean_labeled_text(item)]

    parsed = {
        "summary": extract_string(["summary"]),
        "core_problem": extract_string(["core_problem", "core problem"]),
        "expected_change": extract_string(["expected_change", "expected change"]),
        "why_it_matters": extract_string(["why_it_matters", "why it matters"]),
        "what_to_do": extract_string(["what_to_do", "what to do", "what you'll do"]),
        "first_step": extract_string(["first_step", "first step"]),
        "difficulty": extract_string(["difficulty"]) or "Intermediate",
        "estimated_time": extract_string(["estimated_time", "estimated time"]) or "Not sure",
        "comment_short": extract_string(["comment_short", "comment short"]),
        "comment_detailed": extract_string(["comment_detailed", "comment detailed"]),
        "required_knowledge": extract_list(["required_knowledge", "required knowledge"]),
        "files_likely_needed": extract_list(["files_likely_needed", "files likely needed", "likely_files", "likely files"]),
        "step_by_step_plan": extract_list(["step_by_step_plan", "step by step plan", "plan"]),
        "risks_or_unknowns": extract_list(["risks_or_unknowns", "risks or unknowns", "risks"]),
        "competition": 5,
        "skill_match": 6,
    }
    # Keep only if it actually found useful fields.
    useful = parsed.get("summary") or parsed.get("core_problem") or parsed.get("expected_change") or parsed.get("what_to_do")
    return parsed if useful else {}


def _fallback_from_issue(issue_title: str = "", issue_body: str = "") -> Dict[str, Any]:
    body = _clean_labeled_text(issue_body)
    title = _clean_labeled_text(issue_title)
    short = body[:500] if body else title or "The issue needs review before a reliable breakdown can be generated."

    return {
        "summary": short[:260],
        "core_problem": short,
        "expected_change": "Read the issue body carefully and identify the requested change before commenting.",
        "why_it_matters": "A clear understanding prevents generic comments and helps you make a focused PR.",
        "what_to_do": "Review the issue, reproduce or inspect the relevant area, then propose a small focused fix or documentation update.",
        "required_knowledge": ["GitHub workflow", "Repo setup", "Relevant project stack"],
        "files_likely_needed": ["README/docs or files mentioned in the issue"],
        "step_by_step_plan": [
            "Read the issue body fully.",
            "Check whether a maintainer has confirmed the task is ready.",
            "Find the files mentioned in the issue or related docs.",
            "Comment with a specific first step and ask to be assigned.",
        ],
        "first_step": "Read the issue body and identify the exact expected change.",
        "risks_or_unknowns": [],
        "difficulty": "Intermediate",
        "competition": 5,
        "skill_match": 6,
        "estimated_time": "Not sure",
        "comment_short": "Hi! I’d like to work on this issue. I’ll review the requested change and start with a focused PR. Please assign this to me if available.",
        "comment_detailed": "Hi! I’d like to work on this issue. I’ll first review the issue body, identify the exact expected change, check the relevant files, and then submit a focused PR. Please assign this to me if this approach sounds good.",
        "explanation": short,
    }


def _extract_json(text: str) -> Dict[str, Any]:
    """Best-effort JSON extraction with malformed-JSON recovery."""
    cleaned = _clean_json_text(text)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        candidate = match.group(0)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            loose = _loose_json_values(candidate)
            if loose:
                return loose

    loose = _loose_json_values(cleaned)
    if loose:
        return loose

    return _fallback_from_issue(issue_body=cleaned)


def _safe_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(value)]



def _clean_labeled_text(value: Any) -> str:
    """Clean labels, raw JSON fragments, markdown, and repeated prefixes from model text."""
    text = str(value or "").strip()
    if not text:
        return ""

    # If a value is accidentally a dict/list string, strip braces/quotes enough for display.
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^```\s*", "", text).strip()
    text = re.sub(r"\s*```$", "", text).strip()

    # Remove common JSON-ish punctuation at edges.
    text = text.strip(" \n\t\r,{}[]")

    # Remove repeated field labels at the start.
    text = re.sub(
        r'^(summary|core_problem|core problem|expected_change|expected change|what_to_do|what to do|why_it_matters|why it matters|first_step|first step|explanation)\s*[:=\-]\s*',
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    # Remove wrapping quotes.
    text = text.strip('"').strip("'").strip()

    # Clean markdown clutter but keep content.
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _clean_list_items(value: Any) -> List[str]:
    """Convert model list/string output into a clean list of display strings."""
    if value is None:
        return []
    if isinstance(value, list):
        raw_items = value
    else:
        text = str(value)
        # Split numbered lists, bullets, semicolons, or newlines.
        raw_items = re.split(r"(?:\n+|;\s+|\s+\d+\.\s+|•\s+|-{1,2}\s+)", text)

    cleaned = []
    seen = set()
    for item in raw_items:
        cleaned_item = _clean_labeled_text(item)
        if not cleaned_item:
            continue
        key = cleaned_item.lower()
        if key not in seen:
            cleaned.append(cleaned_item)
            seen.add(key)
    return cleaned


def _comments_for_prompt(comments: List[Dict[str, Any]]) -> str:
    if not comments:
        return "No comments provided."

    lines = []
    for comment in comments[-5:]:
        body = str(comment.get("body", "")).strip()
        if not body:
            continue
        lines.append(
            f"- {comment.get('user', 'unknown')} at {comment.get('created_at', 'unknown')}:\n"
            f"{body[:900]}"
        )

    return "\n\n".join(lines) if lines else "No useful comment text provided."


def summarize_repository(repo_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    prompt = f"""
You are GitScout AI, an expert open-source project scout.

Summarize this repository for a Python + AI/ML beginner contributor in ONE clear sentence.

Focus on:
- what the project does
- main tech area
- why it may be useful to contribute to

Repository: {repo_data.get("name") or repo_data.get("full_name") or "Unknown"}
Description: {repo_data.get("description", "")}
Tech stack: {repo_data.get("tech_stack", [])}
Language: {repo_data.get("language", "")}
README:
{str(repo_data.get("readme", ""))[:2500]}

Return only one polished sentence.
"""
    summary = _gemini_request(prompt, api_key=api_key, max_output_tokens=250)
    return {"summary": summary.strip(), "prompt": prompt}


def summarize_issue(issue_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    prompt = f"""
Summarize this GitHub issue in one simple beginner-friendly sentence.

Use the issue body as the main source of truth.

Title: {issue_data.get("title", "")}
Body: {str(issue_data.get("body", ""))[:2200]}
Labels: {issue_data.get("labels", [])}
Comments count: {issue_data.get("comments", issue_data.get("comments_count", 0))}

Return only one sentence.
"""
    summary = _gemini_request(prompt, api_key=api_key, max_output_tokens=250)
    return {"summary": summary.strip(), "prompt": prompt}


def analyze_issue(issue_data: Dict[str, Any], skill_level: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Backward-compatible issue analysis.

    If issue_data contains latest_comments or repo context, this calls the deeper
    analyzer. Otherwise it returns the old compact fields plus deeper fields.
    """
    if issue_data.get("latest_comments") is not None or issue_data.get("repo"):
        return analyze_issue_deep(issue_data, {"skill_level": skill_level}, api_key=api_key)

    prompt = f"""
You are GitScout AI, an open-source mentor.

Analyze this GitHub issue for a {skill_level} contributor.

Return ONLY valid JSON:
{{
  "summary": "one short sentence",
  "core_problem": "what problem the issue is actually asking to solve",
  "expected_change": "what should be changed or built",
  "what_to_do": "what the contributor likely needs to do",
  "why_good_match": "why this is or is not a good fit",
  "files_likely_needed": ["possible file or folder names, or Not clear from issue"],
  "difficulty": "Beginner or Intermediate or Advanced",
  "competition": 1,
  "skill_match": 8,
  "estimated_time": "short estimate",
  "first_step": "first practical step"
}}

Rules:
- Use issue body as the source of truth.
- Do not treat another user's comment as the main issue request.
- competition: 1 means very low, 10 means very high.
- skill_match: 1 means bad fit, 10 means excellent fit.

Issue title: {issue_data.get("title", "")}
Issue body: {str(issue_data.get("body", ""))[:3500]}
Labels: {issue_data.get("labels", [])}
Comments count: {issue_data.get("comments", 0)}
Assignee: {issue_data.get("assignee") or "None"}
Created at: {issue_data.get("created_at", "Unknown")}
"""
    output = _gemini_request(prompt, api_key=api_key)
    parsed = _extract_json(output)
    normalized = _normalize_issue_analysis(parsed, prompt)
    if not normalized.get("core_problem") or normalized.get("core_problem", "").strip().startswith("{"):
        fallback = _fallback_from_issue(issue_context.get("title", ""), issue_context.get("body", ""))
        normalized = _normalize_issue_analysis(fallback, prompt)
    return normalized


def analyze_issue_deep(
    issue_context: Dict[str, Any],
    user_profile: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate the main GitScout 'Understand this issue' response.

    This prompt is intentionally NOT a summary prompt. It forces the model to
    translate the GitHub issue into beginner-friendly contribution guidance.
    """
    user_profile = user_profile or {}
    comments_text = _comments_for_prompt(issue_context.get("latest_comments", []))

    prompt = f"""
You are GitScout AI, a senior open-source mentor for beginners.

Your job is NOT to summarize the GitHub issue.
Your job is to translate the issue into practical contribution guidance.

The user is trying to decide:
- Can I work on this issue?
- What is the actual task?
- What files/areas should I inspect?
- What should I do first?
- Is this beginner-friendly or too advanced?

CRITICAL RULES:
1. Use the issue body as the source of truth.
2. Use comments only as extra context.
3. Do not copy big chunks of the issue body.
4. Do not repeat model/product marketing descriptions unless needed.
5. Explain what the contributor actually needs to do.
6. If this is advanced, say honestly that it is advanced.
7. If the issue looks like a huge model/framework implementation, warn that it is not a good first PR.
8. Do not invent exact file names unless they are mentioned. If unsure, give likely folders/areas.
9. Keep each bullet short, practical, and beginner-readable.
10. Never output raw JSON as a string value.

USER PROFILE:
Skill level: {user_profile.get("skill_level", "Beginner")}
Skills: {user_profile.get("user_skills", [])}
Interests: {user_profile.get("ml_interests", [])}
Preferred contribution types: {user_profile.get("contribution_types", [])}

REPO:
{issue_context.get("repo", "Unknown repo")}

ISSUE:
Number: {issue_context.get("issue_number", "")}
Title: {issue_context.get("title", "")}
Labels: {issue_context.get("labels", [])}
Assignee: {issue_context.get("assignee") or "None"}
Comments count: {issue_context.get("comments_count", 0)}
Created: {issue_context.get("created_at", "Unknown")}
Updated: {issue_context.get("updated_at", "Unknown")}

ISSUE BODY:
{str(issue_context.get("body", ""))[:6500]}

LATEST COMMENTS:
{comments_text}

Return ONLY valid JSON.
No markdown.
No text before or after JSON.
Use EXACTLY these snake_case keys.
Every explanation field must be an array of short bullet strings, not a long paragraph.

{{
  "summary": "One simple sentence explaining the issue in beginner language.",
  "core_problem": [
    "What is missing, broken, or requested?",
    "Why the current repo cannot do it yet?"
  ],
  "expected_change": [
    "What the PR should add/change.",
    "What should be true after the PR is merged."
  ],
  "why_it_matters": [
    "Why this change helps users, maintainers, or contributors."
  ],
  "what_to_do": [
    "Concrete task 1 the contributor will do.",
    "Concrete task 2 the contributor will do.",
    "Concrete task 3 the contributor will do."
  ],
  "required_knowledge": [
    "Skill/tool/concept needed"
  ],
  "files_likely_needed": [
    "Likely file/folder/area to inspect"
  ],
  "step_by_step_plan": [
    "First practical action",
    "Second practical action",
    "Third practical action",
    "Testing/docs action"
  ],
  "first_step": "The first practical thing to do after opening the repo.",
  "risks_or_unknowns": [
    "Anything unclear or risky"
  ],
  "difficulty": "Beginner or Intermediate or Advanced",
  "beginner_warning": "Clear warning if this is not a good first issue, otherwise empty string.",
  "competition": 1,
  "skill_match": 8,
  "estimated_time": "realistic estimate",
  "comment_short": "Paste-ready GitHub comment asking to work on it.",
  "comment_detailed": "Paste-ready GitHub comment with a brief plan asking to be assigned."
}}

Before returning JSON, check:
- Did you explain the task instead of copying the issue?
- Did you say if it is too advanced?
- Did you give concrete actions?
"""
    output = _gemini_request(prompt, api_key=api_key, max_output_tokens=2600, temperature=0.12)
    parsed = _extract_json(output)
    normalized = _normalize_issue_analysis(parsed, prompt)

    # If the model still returned copied/raw JSON-like text, fall back to a
    # deterministic issue-body based explanation instead of showing garbage.
    bad_core = str(normalized.get("core_problem", "")).strip()
    if not bad_core or bad_core.startswith("{") or '"summary"' in bad_core[:120]:
        fallback = _fallback_from_issue(issue_context.get("title", ""), issue_context.get("body", ""))
        normalized = _normalize_issue_analysis(fallback, prompt)

    return normalized


def generate_contribution_comment(
    issue_breakdown: Dict[str, Any],
    style: str = "Short and polite",
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a paste-ready GitHub assignment comment as plain text."""
    style_guidance = {
        "Short and polite": (
            "Write 5-7 sentences. Be polite, specific, and ask to be assigned. "
            "Mention the first concrete step."
        ),
        "Beginner-friendly": (
            "Write 6-8 sentences. Be honest that the contributor is learning, but show preparation, "
            "a clear first step, and willingness to follow maintainer guidance."
        ),
        "Confident technical": (
            "Write 8-10 sentences. Sound technically confident and specific. "
            "Mention the core problem, likely implementation approach, validation/testing plan, "
            "and ask to be assigned. Do not overpromise or claim already completed work."
        ),
        "Detailed plan": (
            "Write 9-12 sentences. Include a concise step-by-step plan in paragraph form, "
            "mention what you will inspect, what you will change, how you will test, and ask to be assigned."
        ),
    }.get(style, "Write 6-8 polite, specific, paste-ready sentences.")

    prompt = f"""
You are GitScout AI.

Write ONLY the GitHub issue comment the user can paste into the issue discussion to ask to work on the issue and get assigned.
No JSON.
No markdown heading.
Do not wrap the answer in quotes.
Do not say you already fixed it.
Do not sound generic.
Make the comment specific to this issue.
Ask to be assigned at the end.

Style: {style}
Style guidance: {style_guidance}

Issue title: {issue_breakdown.get("title", issue_breakdown.get("summary", ""))}
Core problem: {issue_breakdown.get("core_problem", "")}
Expected change: {issue_breakdown.get("expected_change", "")}
Why it matters: {issue_breakdown.get("why_it_matters", "")}
First step: {issue_breakdown.get("first_step", "")}
Likely files/areas: {issue_breakdown.get("files_likely_needed", [])}
Required knowledge: {issue_breakdown.get("required_knowledge", [])}
Comment intent: {issue_breakdown.get("comment_intent", "Ask to work on this issue and get assigned.")}

Write the final paste-ready comment now.
"""
    output = _gemini_request(prompt, api_key=api_key, max_output_tokens=1200, temperature=0.35)
    comment = _clean_json_text(output).strip()

    try:
        parsed = json.loads(comment)
        if isinstance(parsed, dict) and parsed.get("comment"):
            comment = str(parsed["comment"]).strip()
    except Exception:
        pass

    comment = re.sub(r"^comment\s*[:\-]\s*", "", comment, flags=re.IGNORECASE).strip()
    if not comment:
        comment = (
            "Hi! I’d like to work on this issue. I understand that the main goal is to address the requested change "
            "in a focused way without making unrelated modifications. I’ll start by reviewing the issue body, checking "
            "the relevant files or documentation, and confirming the expected behavior before implementing anything. "
            "After that, I’ll make a small, focused change and include basic validation or testing notes in the PR. "
            "Please assign this to me if it is available."
        )

    return {"comment": comment, "prompt": prompt}


def _normalize_issue_analysis(parsed: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    files = parsed.get("files_likely_needed", "Not clear from issue")
    if isinstance(files, str):
        files_value = _clean_labeled_text(files)
    else:
        files_value = [_clean_labeled_text(item) for item in files if _clean_labeled_text(item)]

    required = _clean_list_items(parsed.get("required_knowledge", []))
    plan = _clean_list_items(parsed.get("step_by_step_plan", []))
    risks = _clean_list_items(parsed.get("risks_or_unknowns", []))

    summary = _clean_labeled_text(parsed.get("summary", ""))
    core_problem = _clean_labeled_text(parsed.get("core_problem", ""))
    expected_change = _clean_labeled_text(parsed.get("expected_change", ""))

    return {
        "summary": summary,
        "core_problem": core_problem,
        "expected_change": expected_change,
        "why_it_matters": _clean_labeled_text(parsed.get("why_it_matters", "")),
        "what_to_do": _clean_labeled_text(parsed.get("what_to_do", expected_change or core_problem or summary)),
        "why_good_match": _clean_labeled_text(parsed.get("why_good_match", "")),
        "required_knowledge": required,
        "files_likely_needed": files_value,
        "step_by_step_plan": plan,
        "first_step": _clean_labeled_text(parsed.get("first_step", "")),
        "risks_or_unknowns": risks,
        "difficulty": _clean_labeled_text(parsed.get("difficulty", "Intermediate")) or "Intermediate",
        "competition": parsed.get("competition", 5),
        "skill_match": parsed.get("skill_match", 6),
        "estimated_time": _clean_labeled_text(parsed.get("estimated_time", "Not sure")) or "Not sure",
        "comment_short": _clean_labeled_text(parsed.get("comment_short", "")),
        "comment_detailed": _clean_labeled_text(parsed.get("comment_detailed", "")),
        "explanation": _clean_labeled_text(parsed.get("explanation", core_problem or expected_change or summary)),
        "prompt": prompt,
    }
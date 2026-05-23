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


def _extract_json(text: str) -> Dict[str, Any]:
    """Best-effort JSON extraction.

    Gemini is usually good, but not perfect: it may wrap JSON in markdown,
    add a sentence before JSON, or occasionally return plain text. This parser
    prevents the app from crashing by returning a fallback dictionary when JSON
    extraction fails.
    """
    cleaned = _clean_json_text(text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Fallback: preserve the useful text instead of throwing and breaking UI.
    fallback = cleaned[:1200] if cleaned else "AI returned an empty or invalid structured response."
    return {
        "summary": fallback[:350],
        "core_problem": fallback,
        "expected_change": "The model did not return structured JSON, so GitScout is showing the raw explanation as a fallback.",
        "why_it_matters": "",
        "what_to_do": fallback,
        "required_knowledge": [],
        "files_likely_needed": ["Not confidently detected"],
        "step_by_step_plan": [
            "Read the full issue body on GitHub.",
            "Identify the exact requested change.",
            "Check the repo files related to the feature or bug.",
            "Ask a maintainer for clarification if the request is unclear.",
        ],
        "first_step": "Open the issue on GitHub and read the full issue body plus the latest maintainer comments.",
        "risks_or_unknowns": ["AI response was not valid JSON, so this is a fallback explanation."],
        "difficulty": "Intermediate",
        "competition": 5,
        "skill_match": 6,
        "estimated_time": "Not sure",
        "comment_short": "Hi! I’d like to work on this issue. I’ll review the details and start with the expected change. Please assign this to me if available.",
        "comment_detailed": "Hi! I’d like to work on this issue. I’ll first review the issue body, identify the expected change, inspect the related files, and ask for clarification if anything is unclear. Please assign this to me if available.",
        "explanation": fallback,
    }


def _safe_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(value)]


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
    return _normalize_issue_analysis(parsed, prompt)


def analyze_issue_deep(
    issue_context: Dict[str, Any],
    user_profile: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate the main GitScout 'Understand this issue' response.

    The prompt separates issue body and comments so Gemini does not confuse
    discussion comments with the actual maintainer request.
    """
    user_profile = user_profile or {}
    comments_text = _comments_for_prompt(issue_context.get("latest_comments", []))

    prompt = f"""
You are GitScout AI, a senior open-source mentor for Python + AI/ML beginners.

Your job is to help a beginner understand the REAL task in this GitHub issue.
Be practical, honest, and specific. Do not hype.

IMPORTANT SOURCE RULES:
1. The issue body is the source of truth.
2. Latest comments are only extra context.
3. Do NOT confuse comments with the actual issue request.
4. If the issue body is incomplete or unclear, say what is missing.
5. Do not invent exact file names unless they are mentioned. If unsure, say likely areas instead.

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

Return ONLY valid JSON with this exact shape.
Do not wrap it in markdown.
Do not write ```json.
Do not add any explanation before or after the JSON:
{{
  "summary": "2 sentence beginner-friendly overview",
  "core_problem": "what is broken/missing/requested, explained simply",
  "expected_change": "what the contributor is expected to implement or change",
  "why_it_matters": "why this change matters to the repo/user",
  "what_to_do": "concrete explanation of the work",
  "required_knowledge": ["skill 1", "skill 2"],
  "files_likely_needed": ["file/area 1", "file/area 2"],
  "step_by_step_plan": ["step 1", "step 2", "step 3", "step 4"],
  "first_step": "the first practical thing to do after cloning the repo",
  "risks_or_unknowns": ["unknown/risk 1", "unknown/risk 2"],
  "difficulty": "Beginner or Intermediate or Advanced",
  "competition": 1,
  "skill_match": 8,
  "estimated_time": "realistic estimate",
  "comment_short": "short polite GitHub comment asking to work on it",
  "comment_detailed": "more detailed GitHub comment with a brief plan"
}}
"""
    output = _gemini_request(prompt, api_key=api_key, max_output_tokens=2200, temperature=0.15)
    parsed = _extract_json(output)
    return _normalize_issue_analysis(parsed, prompt)


def generate_contribution_comment(
    issue_breakdown: Dict[str, Any],
    style: str = "Short and polite",
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate or improve the ready-to-copy GitHub issue comment.

    This intentionally returns plain text, not JSON. Comments are free-form text,
    and forcing JSON here caused unnecessary failures when Gemini returned a
    natural comment instead of a JSON object.
    """
    style_guidance = {
        "Short and polite": "Keep it short, polite, and direct. 2-4 sentences.",
        "Beginner-friendly": "Be honest that the contributor is a beginner, but sound serious and willing to learn.",
        "Confident technical": "Sound confident and technical, with a concise plan. Do not overpromise.",
        "Detailed plan": "Include a brief practical plan in 4-6 sentences.",
    }.get(style, "Keep it polite, natural, and paste-ready.")

    prompt = f"""
You are GitScout AI.

Write ONLY the GitHub issue comment the user can paste.
No JSON.
No markdown headings.
No bullet list unless the style asks for a detailed plan.
Do not wrap the answer in quotes.

Style: {style}
Style guidance: {style_guidance}

Issue title: {issue_breakdown.get("title", issue_breakdown.get("summary", ""))}
Core problem: {issue_breakdown.get("core_problem", "")}
Expected change: {issue_breakdown.get("expected_change", "")}
First step: {issue_breakdown.get("first_step", "")}
Likely files/areas: {issue_breakdown.get("files_likely_needed", [])}
Required knowledge: {issue_breakdown.get("required_knowledge", [])}

Write the final paste-ready comment now.
"""
    output = _gemini_request(prompt, api_key=api_key, max_output_tokens=600, temperature=0.35)
    comment = _clean_json_text(output).strip()

    # If Gemini still returns a JSON-ish response, try to read the comment,
    # but never fail if parsing does not work.
    try:
        parsed = json.loads(comment)
        if isinstance(parsed, dict) and parsed.get("comment"):
            comment = str(parsed["comment"]).strip()
    except Exception:
        pass

    comment = re.sub(r"^comment\s*[:\-]\s*", "", comment, flags=re.IGNORECASE).strip()
    if not comment:
        comment = (
            "Hi! I’d like to work on this issue. I’ll review the issue details, "
            "identify the expected change, and start with a small focused PR. "
            "Please assign this to me if available."
        )

    return {"comment": comment, "prompt": prompt}


def _normalize_issue_analysis(parsed: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    files = parsed.get("files_likely_needed", "Not clear from issue")
    if isinstance(files, str):
        files_value = files
    else:
        files_value = [str(item) for item in files if str(item).strip()]

    required = _safe_list(parsed.get("required_knowledge", []))
    plan = _safe_list(parsed.get("step_by_step_plan", []))
    risks = _safe_list(parsed.get("risks_or_unknowns", []))

    summary = parsed.get("summary", "")
    core_problem = parsed.get("core_problem", "")
    expected_change = parsed.get("expected_change", "")

    return {
        "summary": summary,
        "core_problem": core_problem,
        "expected_change": expected_change,
        "why_it_matters": parsed.get("why_it_matters", ""),
        "what_to_do": parsed.get("what_to_do", expected_change or core_problem or summary),
        "why_good_match": parsed.get("why_good_match", ""),
        "required_knowledge": required,
        "files_likely_needed": files_value,
        "step_by_step_plan": plan,
        "first_step": parsed.get("first_step", ""),
        "risks_or_unknowns": risks,
        "difficulty": parsed.get("difficulty", "Intermediate"),
        "competition": parsed.get("competition", 5),
        "skill_match": parsed.get("skill_match", 6),
        "estimated_time": parsed.get("estimated_time", "Not sure"),
        "comment_short": parsed.get("comment_short", ""),
        "comment_detailed": parsed.get("comment_detailed", ""),
        "explanation": parsed.get("explanation", core_problem or expected_change or summary),
        "prompt": prompt,
    }

# # import json
# # import os
# # from pathlib import Path
# # from typing import Any, Dict, Optional

# # import google.generativeai as genai
# # from dotenv import load_dotenv


# # MODEL_NAME = "gemini-2.5-flash"


# # class GeminiAPIError(Exception):
# #     pass


# # def _load_gemini_key(api_key: Optional[str] = None) -> str:
# #     if api_key:
# #         return api_key

# #     env_path = Path(__file__).resolve().parents[1] / ".env"
# #     if env_path.exists():
# #         load_dotenv(env_path)

# #     key = os.getenv("GEMINI_API_KEY")
# #     if not key:
# #         raise GeminiAPIError("Gemini API key not found. Set GEMINI_API_KEY in .env or pass api_key explicitly.")

# #     return key


# # def _extract_text(response_json: Dict[str, Any]) -> str:
# #     if not isinstance(response_json, dict):
# #         raise GeminiAPIError("Unexpected Gemini response format.")

# #     if "output_text" in response_json:
# #         return response_json["output_text"]

# #     output = response_json.get("output")
# #     if isinstance(output, list) and output:
# #         first = output[0]
# #         if isinstance(first, dict):
# #             contents = first.get("content")
# #             if isinstance(contents, list):
# #                 texts = [item.get("text", "") for item in contents if isinstance(item, dict) and "text" in item]
# #                 return "".join(texts).strip()
# #     raise GeminiAPIError("Unable to extract text from Gemini response.")


# # def _gemini_request(prompt: str, api_key: Optional[str] = None) -> str:
# #     key = _load_gemini_key(api_key)
# #     genai.configure(api_key=key)

# #     try:
# #         response = genai.responses.create(model=MODEL_NAME, input=prompt)
# #     except Exception as exc:
# #         raise GeminiAPIError(f"Gemini request failed: {exc}") from exc

# #     if not response or not hasattr(response, "output_text"):
# #         raise GeminiAPIError("Gemini response did not include generated text.")

# #     text = response.output_text
# #     if not isinstance(text, str) or not text.strip():
# #         raise GeminiAPIError("Gemini returned empty or invalid text.")

# #     return text.strip()


# # def summarize_repository(repo_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
# #     readme = repo_data.get("readme", "")
# #     prompt = (
# #         "You are an expert open-source curator. Summarize this GitHub repository in one concise sentence "
# #         "for a developer looking for beginner-friendly contributions. Include the main technology focus and the repo's value.\n\n"
# #         f"Repository name: {repo_data.get('name', 'Unknown')}\n"
# #         f"Description: {repo_data.get('description', 'No description')}\n"
# #         f"Language: {repo_data.get('language', 'Unknown')}\n"
# #         f"Stars: {repo_data.get('stars', 0)}\n"
# #         f"Topics: {', '.join(repo_data.get('topics', [])) if repo_data.get('topics') else 'None'}\n"
# #         "README content:\n"
# #         f"{readme[:2500]}\n\n"
# #         "Provide exactly one clear sentence."
# #     )
# #     summary = _gemini_request(prompt, api_key=api_key)
# #     return {
# #         "summary": summary.strip(),
# #         "prompt": prompt,
# #     }


# # def summarize_issue(issue_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
# #     prompt = (
# #         "You are an AI issue assistant. Read the issue details and write a clear, concise summary that a contributor can understand. "
# #         "Keep it short and mention the goal and why it matters.\n\n"
# #         f"Issue title: {issue_data.get('title', 'No title')}\n"
# #         f"Body: {issue_data.get('body', 'No description')}\n"
# #         f"Labels: {', '.join(issue_data.get('labels', [])) or 'None'}\n"
# #         f"Comments: {issue_data.get('comments', 0)}\n"
# #         "Summary:\n"
# #     )
# #     summary = _gemini_request(prompt, api_key=api_key)
# #     return {"summary": summary.strip(), "prompt": prompt}


# # def analyze_issue(issue_data: Dict[str, Any], skill_level: str, api_key: Optional[str] = None) -> Dict[str, Any]:
# #     prompt = (
# #         "You are an AI issue analyst. Given the issue details and user skill level, return a JSON object with keys:\n"
# #         "summary, difficulty, competition, skill_match, explanation.\n"
# #         "- summary: one concise sentence.\n"
# #         "- difficulty: Beginner, Intermediate, or Advanced.\n"
# #         "- competition: a numeric score from 1-10, where 10 means very competitive.\n"
# #         "- skill_match: a numeric score from 1-10 for this user's skill level.\n"
# #         "- explanation: one sentence.\n"
# #         "Output only valid JSON with no extra commentary.\n\n"
# #         f"Skill level: {skill_level}\n"
# #         f"Issue title: {issue_data.get('title', 'No title')}\n"
# #         f"Body: {issue_data.get('body', 'No description')}\n"
# #         f"Labels: {', '.join(issue_data.get('labels', [])) or 'None'}\n"
# #         f"Comments: {issue_data.get('comments', 0)}\n"
# #         f"Assignee: {issue_data.get('assignee') or 'None'}\n"
# #         f"Created at: {issue_data.get('created_at', 'Unknown')}\n"
# #         "JSON:\n"
# #     )
# #     output_text = _gemini_request(prompt, api_key=api_key)

# #     try:
# #         parsed = json.loads(output_text)
# #     except ValueError:
# #         raise GeminiAPIError("Gemini issue analysis response was not valid JSON.")

# #     return {
# #         "summary": parsed.get("summary", ""),
# #         "difficulty": parsed.get("difficulty", "Unknown"),
# #         "competition": parsed.get("competition", "N/A"),
# #         "skill_match": parsed.get("skill_match", "N/A"),
# #         "explanation": parsed.get("explanation", ""),
# #         "prompt": prompt,
# #     }


# import json
# import os
# import re
# from pathlib import Path
# from typing import Any, Dict, Optional

# import google.generativeai as genai
# from dotenv import load_dotenv


# MODEL_NAME = "gemini-2.5-flash"


# class GeminiAPIError(Exception):
#     pass


# def _load_gemini_key(api_key: Optional[str] = None) -> str:
#     if api_key:
#         return api_key

#     env_path = Path(__file__).resolve().parents[1] / ".env"
#     if env_path.exists():
#         load_dotenv(env_path)

#     key = os.getenv("GEMINI_API_KEY")
#     if not key:
#         raise GeminiAPIError("Gemini API key not found. Set GEMINI_API_KEY in .env.")

#     return key


# def _gemini_request(prompt: str, api_key: Optional[str] = None) -> str:
#     key = _load_gemini_key(api_key)
#     genai.configure(api_key=key)

#     try:
#         model = genai.GenerativeModel(
#             MODEL_NAME,
#             generation_config={
#                 "temperature": 0.2,
#                 "max_output_tokens": 500,
#             },
#         )
#         response = model.generate_content(prompt)
#         text = response.text
#     except Exception as exc:
#         raise GeminiAPIError(f"Gemini request failed: {exc}") from exc

#     if not text or not text.strip():
#         raise GeminiAPIError("Gemini returned empty response.")

#     return text.strip()


# def _extract_json(text: str) -> Dict[str, Any]:
#     cleaned = text.strip()
#     cleaned = re.sub(r"^```json", "", cleaned, flags=re.IGNORECASE).strip()
#     cleaned = re.sub(r"^```", "", cleaned).strip()
#     cleaned = re.sub(r"```$", "", cleaned).strip()

#     try:
#         return json.loads(cleaned)
#     except json.JSONDecodeError:
#         match = re.search(r"\{[\s\S]*\}", cleaned)
#         if match:
#             return json.loads(match.group(0))
#         raise GeminiAPIError("Gemini issue analysis response was not valid JSON.")


# def summarize_repository(repo_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
#     prompt = f"""
# You are an expert open-source curator.

# Summarize this GSSoC/GitHub repository in ONE concise sentence for a beginner contributor.

# Project name: {repo_data.get("name")}
# Description: {repo_data.get("description")}
# Tech stack: {repo_data.get("tech_stack")}
# Language: {repo_data.get("language")}
# README:
# {repo_data.get("readme", "")[:2200]}

# Return only one clear sentence.
# """
#     return {"summary": _gemini_request(prompt, api_key), "prompt": prompt}


# def summarize_issue(issue_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
#     prompt = f"""
# Summarize this GitHub issue in one short beginner-friendly sentence.

# Title: {issue_data.get("title")}
# Body: {issue_data.get("body", "")[:1500]}
# Labels: {issue_data.get("labels")}
# Comments: {issue_data.get("comments")}

# Return only one sentence.
# """
#     return {"summary": _gemini_request(prompt, api_key), "prompt": prompt}


# def analyze_issue(issue_data: Dict[str, Any], skill_level: str, api_key: Optional[str] = None) -> Dict[str, Any]:
#     prompt = f"""
# You are an open-source issue analyst.

# Analyze this GitHub issue for a {skill_level} contributor.

# Return ONLY valid JSON:
# {{
#   "summary": "one short sentence",
#   "difficulty": "Beginner",
#   "competition": 1,
#   "skill_match": 8,
#   "explanation": "one short reason"
# }}

# Rules:
# - competition 1 means low competition, 10 means very high competition.
# - More comments means more competition.
# - good first issue/help wanted usually means better for beginners.
# - If issue is unclear, lower the skill_match.

# Issue:
# Title: {issue_data.get("title")}
# Body: {issue_data.get("body", "")[:1800]}
# Labels: {issue_data.get("labels")}
# Comments: {issue_data.get("comments")}
# Assignee: {issue_data.get("assignee")}
# Created at: {issue_data.get("created_at")}
# """
#     text = _gemini_request(prompt, api_key)
#     parsed = _extract_json(text)

#     return {
#         "summary": parsed.get("summary", ""),
#         "difficulty": parsed.get("difficulty", "Intermediate"),
#         "competition": parsed.get("competition", 5),
#         "skill_match": parsed.get("skill_match", 6),
#         "explanation": parsed.get("explanation", ""),
#     }


import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

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


def _gemini_request(prompt: str, api_key: Optional[str] = None) -> str:
    key = _load_gemini_key(api_key)
    genai.configure(api_key=key)

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        text = response.text
    except Exception as exc:
        raise GeminiAPIError(f"Gemini request failed: {exc}") from exc

    if not text or not text.strip():
        raise GeminiAPIError("Gemini returned an empty response.")

    return text.strip()


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise GeminiAPIError("Gemini response did not contain valid JSON.")

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise GeminiAPIError("Gemini issue analysis JSON parsing failed.") from exc


def summarize_repository(repo_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    prompt = f"""
You are GitScout AI, an expert open-source project scout.

Summarize this repository for a student contributor in ONE clear sentence.

Focus on:
- what the project does
- main tech area
- why it may be useful to contribute to

Project name: {repo_data.get("name", "Unknown")}
Description: {repo_data.get("description", "")}
Tech stack: {repo_data.get("tech_stack", [])}
Language: {repo_data.get("language", "")}
README:
{repo_data.get("readme", "")[:2500]}

Return only one polished sentence.
"""

    summary = _gemini_request(prompt, api_key)

    return {
        "summary": summary.strip(),
        "prompt": prompt,
    }


def summarize_issue(issue_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    prompt = f"""
Summarize this GitHub issue in one simple sentence.

Issue title: {issue_data.get("title", "")}
Issue body: {issue_data.get("body", "")[:2000]}
Labels: {issue_data.get("labels", [])}
Comments: {issue_data.get("comments", 0)}

Return only one sentence.
"""

    summary = _gemini_request(prompt, api_key)

    return {
        "summary": summary.strip(),
        "prompt": prompt,
    }


def analyze_issue(
    issue_data: Dict[str, Any],
    skill_level: str,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    prompt = f"""
You are GitScout AI, an expert open-source mentor.

Analyze this GitHub issue for a {skill_level} contributor.

Return ONLY valid JSON.

JSON format:
{{
  "summary": "short clear summary of the issue",
  "what_to_do": "what the contributor likely needs to do",
  "why_good_match": "why this issue is or is not good for this user",
  "files_likely_needed": "possible files/folders they may need to inspect, or 'Not clear from issue'",
  "difficulty": "Beginner or Intermediate or Advanced",
  "competition": 1,
  "skill_match": 1,
  "estimated_time": "short estimate like 30 min, 2 hours, 1 day",
  "first_step": "first practical step the user should take"
}}

Scoring rules:
- competition: 1 means very low competition, 10 means very high competition
- skill_match: 1 means bad fit, 10 means excellent fit
- prefer beginner-friendly explanations

Issue title: {issue_data.get("title", "")}
Issue body: {issue_data.get("body", "")[:3000]}
Labels: {issue_data.get("labels", [])}
Comments: {issue_data.get("comments", 0)}
Assignee: {issue_data.get("assignee") or "None"}
Created at: {issue_data.get("created_at", "Unknown")}
"""

    output = _gemini_request(prompt, api_key)
    parsed = _extract_json(output)

    return {
        "summary": parsed.get("summary", ""),
        "what_to_do": parsed.get("what_to_do", ""),
        "why_good_match": parsed.get("why_good_match", ""),
        "files_likely_needed": parsed.get("files_likely_needed", "Not clear from issue"),
        "difficulty": parsed.get("difficulty", "Intermediate"),
        "competition": parsed.get("competition", 5),
        "skill_match": parsed.get("skill_match", 6),
        "estimated_time": parsed.get("estimated_time", "Not sure"),
        "first_step": parsed.get("first_step", ""),
        "prompt": prompt,
    }
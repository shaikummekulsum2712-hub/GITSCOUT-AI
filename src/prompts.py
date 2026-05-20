"""Prompt templates for AI calls."""

REPO_SUMMARY_PROMPT = """
You are an expert open-source curator.
Given repository metadata and README content, write one concise sentence describing:
- the repository's tech focus
- its core purpose
- why it is appealing to contributors
Do not add extra commentary.
"""

ISSUE_SUMMARY_PROMPT = """
You are an issue summarization assistant.
Summarize this GitHub issue in one clear sentence for a contributor.
Include the goal and why the issue matters.
"""

DIFFICULTY_PROMPT = """
Given the issue title, description, and labels,
classify the issue difficulty as Beginner, Intermediate, or Advanced.
Respond with only the difficulty label.
"""

SKILL_MATCH_PROMPT = """
Assess how well this issue fits a contributor at the given skill level.
Return a score from 1 to 10 and one short sentence explaining the match.
Do not include any other text.
"""

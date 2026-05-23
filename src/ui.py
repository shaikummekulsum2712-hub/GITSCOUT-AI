
import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import streamlit as st

from src.ai_agent import (
    analyze_issue,
    analyze_issue_deep,
    generate_contribution_comment,
    summarize_repository,
)
from src.github_client import (
    fetch_open_issues,
    get_gssoc_filter_options,
    get_repository_metadata,
    get_repository_readme,
    get_issue_context,
    search_gssoc_projects,
)
from src.issue_ranker import rank_issues


MAX_AI_ISSUES = 1
DEFAULT_SORT = "Most Good First Issues"


# ─────────────────────────────────────────────────────────────
# PAGE CONFIG + THEME
# ─────────────────────────────────────────────────────────────

def configure_page() -> None:
    st.set_page_config(
        page_title="GitScout AI",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def inject_css() -> None:
    """
    CSS only. No custom HTML layout blocks.
    This avoids the black-code-box bug from Streamlit markdown parsing.
    """
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background:
        radial-gradient(circle at top left, rgba(36, 99, 235, 0.22), transparent 32%),
        radial-gradient(circle at top right, rgba(124, 59, 237, 0.20), transparent 30%),
        radial-gradient(circle at 50% 0%, rgba(7, 182, 213, 0.16), transparent 42%),
        linear-gradient(180deg, #F0F5FF 0%, #F8FAFC 34%, #F5F7FB 100%) !important;
    color: #0F172A !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stSidebar"],
#MainMenu,
footer,
.stDeployButton {
    display: none !important;
    visibility: hidden !important;
}

.main .block-container {
    padding-top: 1.25rem !important;
    padding-left: 2.2rem !important;
    padding-right: 2.2rem !important;
    max-width: 1360px !important;
}

h1, h2, h3, h4, p, span, label, div {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

h1 {
    color: #0F172A !important;
    font-weight: 900 !important;
    letter-spacing: -0.055em !important;
}

h2, h3 {
    color: #0F172A !important;
    font-weight: 800 !important;
    letter-spacing: -0.025em !important;
}

[data-testid="stMarkdownContainer"] p {
    font-size: 15px !important;
    line-height: 1.65 !important;
    color: #0F172A !important;
    font-weight: 500 !important;
}

[data-testid="stCaptionContainer"] {
    color: #475569 !important;
    font-weight: 600 !important;
}

/* Streamlit bordered containers as cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #D6E0EF !important;
    border-radius: 24px !important;
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08) !important;
    background: rgba(255, 255, 255, 0.97) !important;
}

/* Buttons */
.stButton > button {
    border-radius: 13px !important;
    font-weight: 800 !important;
    font-family: 'Inter', sans-serif !important;
    min-height: 2.65rem !important;
    transition: all 0.15s ease !important;
}

.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #2463EB, #7C3BED) !important;
    border: 1.5px solid #2463EB !important;
    color: #FFFFFF !important;
    box-shadow: 0 6px 16px rgba(37, 99, 235, 0.25) !important;
}

.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover {
    filter: brightness(0.97) !important;
    transform: translateY(-1px) !important;
}

.stButton > button[kind="secondary"],
.stButton > button[data-testid="baseButton-secondary"] {
    background: #FFFFFF !important;
    border: 1.5px solid #D6E0EF !important;
    color: #2463EB !important;
    box-shadow: 0 1px 4px rgba(15,23,42,0.05) !important;
}

.stButton > button[kind="secondary"]:hover,
.stButton > button[data-testid="baseButton-secondary"]:hover {
    background: #EFF6FF !important;
    border-color: #93C5FD !important;
}

/* Link buttons */
[data-testid="stLinkButton"] a {
    border-radius: 13px !important;
    font-weight: 800 !important;
    border: 1.5px solid #D6E0EF !important;
    color: #2463EB !important;
    background: #FFFFFF !important;
}

/* Inputs */
.stTextInput input,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div {
    background: #FFFFFF !important;
    color: #0F172A !important;
    border-color: #D6E0EF !important;
    border-radius: 14px !important;
    font-size: 14px !important;
    min-height: 2.75rem !important;
}

.stTextInput input::placeholder {
    color: #64748B !important;
}

[data-testid="stMetricValue"] {
    color: #0F172A !important;
    font-size: 1.15rem !important;
    font-weight: 900 !important;
}

[data-testid="stMetricLabel"] {
    color: #475569 !important;
    font-weight: 700 !important;
}

div[data-testid="stVerticalBlock"] {
    gap: 0.75rem;
}

/* Make brand button look more like product identity */
button[kind="secondary"]:has(div p) {
    text-align: left !important;
}

/* Roadmap/premium polish */
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #B8C7FF !important;
    box-shadow: 0 14px 36px rgba(36, 99, 235, 0.10) !important;
}

.stProgress > div > div > div > div {
    background: linear-gradient(135deg, #2463EB, #7C3BED, #07B6D5) !important;
}

[data-testid="stExpander"] {
    border: 1.5px solid #D6E0EF !important;
    border-radius: 18px !important;
    background: rgba(255,255,255,0.78) !important;
}

[data-testid="stExpander"] summary {
    font-weight: 800 !important;
    color: #2463EB !important;
}

</style>
""",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# CACHE WRAPPERS
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def cached_filter_options() -> Dict[str, List[str]]:
    try:
        data = get_gssoc_filter_options()
        if not isinstance(data, dict):
            return {"tech_stacks": [], "languages": [], "difficulties": []}

        return {
            "tech_stacks": unique_clean(data.get("tech_stacks") or data.get("tech_stack") or data.get("stacks") or []),
            "languages": unique_clean(data.get("languages") or data.get("language") or []),
            "difficulties": unique_clean(data.get("difficulties") or data.get("difficulty") or []),
        }
    except Exception:
        return {"tech_stacks": [], "languages": [], "difficulties": []}


@st.cache_data(ttl=900, show_spinner=False)
def cached_search_projects(
    keywords: str,
    tech_stack: str,
    language: str,
    difficulty: str,
    sort_by: str,
) -> List[Dict[str, Any]]:
    results = search_gssoc_projects(
        keywords=keywords or "",
        tech_stack=tech_stack or "",
        language=language or "",
        difficulty=difficulty or "",
        sort_by=sort_by or DEFAULT_SORT,
    )
    return results if isinstance(results, list) else []


@st.cache_data(ttl=1800, show_spinner=False)
def cached_repo_metadata(full_name: str) -> Dict[str, Any]:
    return get_repository_metadata(full_name)


@st.cache_data(ttl=1800, show_spinner=False)
def cached_repo_readme(full_name: str) -> str:
    return get_repository_readme(full_name)


@st.cache_data(ttl=1800, show_spinner=False)
def cached_open_issues(full_name: str) -> List[Dict[str, Any]]:
    issues = fetch_open_issues(full_name)
    return issues if isinstance(issues, list) else []


@st.cache_data(ttl=3600, show_spinner=False)
def cached_repo_summary(repo_data: Dict[str, Any]) -> Dict[str, Any]:
    return summarize_repository(repo_data)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_issue_analysis(issue_data: Dict[str, Any], skill_level: str) -> Dict[str, Any]:
    return analyze_issue(issue_data, skill_level)


@st.cache_data(ttl=1200, show_spinner=False)
def cached_issue_context(full_name: str, issue_number: int) -> Dict[str, Any]:
    return get_issue_context(full_name, issue_number, max_comments=5)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_deep_issue_analysis(issue_context: Dict[str, Any], user_profile: Dict[str, Any]) -> Dict[str, Any]:
    return analyze_issue_deep(issue_context, user_profile)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_contribution_comment(issue_breakdown: Dict[str, Any], style: str) -> Dict[str, Any]:
    return generate_contribution_comment(issue_breakdown, style)


# ─────────────────────────────────────────────────────────────
# SESSION
# ─────────────────────────────────────────────────────────────

def init_session_state() -> None:
    defaults = {
        "page": "discover",

        "repo_results": [],
        "selected_repos": [],
        "active_repo": None,
        "active_repo_detail": None,

        "ranked_issues": [],
        "selected_issue_idx": 0,
        "issue_ai_breakdowns": {},
        "generated_comments": {},
        "saved_issues": [],

        "keywords": "",
        "hero_keywords": "",
        "repo_filter_keywords": "",

        "tech_stack": "",
        "language": "Python",
        "difficulty": "",
        "sort_by": DEFAULT_SORT,
        "skill_level": "Beginner",

        "repo_filters_open": False,
        "issue_filters_open": False,

        "user_skills": ["Python basics"],
        "ml_interests": ["AI/ML"],
        "contribution_types": ["Docs", "Bug"],

        "issue_labels": ["good first issue", "help wanted"],
        "custom_labels": "",
        "assignee_filter": "Only unassigned",
        "max_comments": 5,
        "issue_keywords": "",
        "issue_type": "Any",
        "ml_area": "Any",
        "required_knowledge": "Any",
        "issue_sort": "Best match",
        "comment_style": "Short and polite",
        "roadmap_built": False,
        "default_repos_loaded": False,
        "time_available": "1-2 hours",
        "roadmap_stage": "Python → NumPy/Pandas",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go(page: str) -> None:
    st.session_state.page = page
    st.rerun()


# ─────────────────────────────────────────────────────────────
# GENERAL HELPERS
# ─────────────────────────────────────────────────────────────

def unique_clean(value: Any) -> List[str]:
    if value is None:
        return []

    if isinstance(value, str):
        items = [part.strip() for part in value.split(",")]
    elif isinstance(value, (list, tuple, set)):
        items = [str(item).strip() for item in value]
    else:
        items = [str(value).strip()]

    cleaned: List[str] = []
    seen = set()

    for item in items:
        if not item:
            continue
        key = item.lower()
        if key not in seen:
            cleaned.append(item)
            seen.add(key)

    return cleaned


def safe_key(value: Any) -> str:
    return hashlib.md5(str(value).encode("utf-8", errors="ignore")).hexdigest()[:10]


def strip_markdown(text: Any) -> str:
    raw = str(text or "")
    raw = re.sub(r"```.*?```", " ", raw, flags=re.DOTALL)
    raw = re.sub(r"`([^`]*)`", r"\1", raw)
    raw = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", raw)
    raw = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", raw)
    raw = re.sub(r"^\s{0,3}#{1,6}\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"[*_>#\-]+", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


def truncate(text: Optional[Any], length: int = 155) -> str:
    clean = strip_markdown(text)
    if not clean:
        return "No description available."
    return clean if len(clean) <= length else clean[: length - 3] + "..."


def extract_repo_full_name(url: str) -> str:
    if not url:
        return ""

    try:
        parsed = urlparse(url)
        parts = [part for part in parsed.path.strip("/").split("/") if part]

        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
    except Exception:
        return ""

    return ""


def repo_url(repo: Dict[str, Any]) -> str:
    return (
        repo.get("repo_url")
        or repo.get("github_url")
        or repo.get("html_url")
        or repo.get("url")
        or "#"
    )


def repo_full_name(repo: Dict[str, Any]) -> str:
    explicit = repo.get("repo_full_name") or repo.get("full_name")

    if explicit:
        return str(explicit)

    url_full_name = extract_repo_full_name(repo_url(repo))
    if url_full_name:
        return url_full_name

    name = repo.get("name")
    if isinstance(name, str) and "/" in name:
        return name

    return str(name or "")


def get_repo_display_name(repo: Dict[str, Any]) -> str:
    return repo_full_name(repo) or str(repo.get("name") or "Unknown repository")


def get_repo_tags(repo: Dict[str, Any]) -> List[str]:
    return unique_clean(repo.get("tech_stack") or repo.get("topics") or repo.get("tags"))[:7]


def searchable_repo_text(repo: Dict[str, Any]) -> str:
    parts = [
        repo.get("name", ""),
        repo_full_name(repo),
        repo.get("description", ""),
        repo.get("summary", ""),
        " ".join(get_repo_tags(repo)),
        repo.get("language", ""),
    ]
    return " ".join(str(part) for part in parts).lower()


def infer_best_for(repo: Dict[str, Any]) -> str:
    text = searchable_repo_text(repo)

    if any(word in text for word in ["nlp", "language model", "transformer", "huggingface", "tokenizer", "llm"]):
        return "NLP / LLMs"
    if any(word in text for word in ["vision", "image", "opencv", "ocr", "segmentation", "detection"]):
        return "Computer Vision"
    if any(word in text for word in ["pandas", "numpy", "preprocess", "data clean", "dataset"]):
        return "Data preprocessing"
    if any(word in text for word in ["sklearn", "scikit", "classification", "regression", "clustering"]):
        return "Classical ML"
    if any(word in text for word in ["pytorch", "tensorflow", "keras", "deep learning", "neural"]):
        return "Deep Learning"
    if any(word in text for word in ["doc", "readme", "tutorial", "example"]):
        return "Docs / Examples"
    if "python" in text:
        return "Python beginners"
    return "AI/ML beginners"


def infer_required_skills(repo: Dict[str, Any]) -> List[str]:
    text = searchable_repo_text(repo)
    skills = []

    if "python" in text or repo.get("language") == "Python":
        skills.append("Python")
    if "numpy" in text:
        skills.append("NumPy")
    if "pandas" in text:
        skills.append("Pandas")
    if "sklearn" in text or "scikit" in text:
        skills.append("Scikit-learn")
    if "pytorch" in text:
        skills.append("PyTorch")
    if "tensorflow" in text or "keras" in text:
        skills.append("TensorFlow")
    if any(word in text for word in ["doc", "readme", "tutorial"]):
        skills.append("Docs")

    return skills[:4] or ["Python", "GitHub basics"]


def infer_contribution_fit(repo: Dict[str, Any]) -> str:
    text = searchable_repo_text(repo)
    difficulty = str(repo.get("difficulty", "")).lower()
    good_first = int(repo.get("good_first_issues", 0) or 0)

    if good_first > 0 or "beginner" in difficulty or "good first issue" in text:
        return "Beginner friendly"

    if any(word in text for word in ["pytorch", "tensorflow", "deep learning", "cuda", "compiler"]):
        return "Needs ML basics"

    return "Beginner possible"


def infer_available_work(repo: Dict[str, Any]) -> List[str]:
    text = searchable_repo_text(repo)
    work = []

    if any(word in text for word in ["doc", "readme", "tutorial", "example"]):
        work.append("Docs")
    if any(word in text for word in ["bug", "fix", "issue"]):
        work.append("Bugs")
    if any(word in text for word in ["test", "pytest", "unittest"]):
        work.append("Tests")
    if any(word in text for word in ["example", "notebook", "demo"]):
        work.append("Examples")
    if any(word in text for word in ["api", "backend", "fastapi"]):
        work.append("API")
    if any(word in text for word in ["preprocess", "dataset", "data"]):
        work.append("Data")

    return work[:4] or ["Docs", "Bugs", "Examples"]


def github_stat(value: Any) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return "—"

    return str(number) if number > 0 else "—"


def dynamic_repo_reasons(repo: Dict[str, Any]) -> List[str]:
    tags = get_repo_tags(repo)
    language = str(repo.get("language") or "").lower()
    skills = infer_required_skills(repo)
    fit = infer_contribution_fit(repo)
    open_issues = repo.get("open_issues") or repo.get("open_issues_count") or 0

    reasons = []

    if "Python" in skills or language == "python":
        reasons.append("Uses Python, which matches the AI/ML beginner path.")

    if fit == "Beginner friendly":
        reasons.append("Looks beginner-friendly based on labels, tags, or difficulty.")

    if open_issues and int(open_issues) > 0:
        reasons.append(f"Has {open_issues} open issues to explore.")

    if tags:
        reasons.append(f"Project area: {infer_best_for(repo)}.")

    if not reasons:
        reasons.append("Good candidate for checking beginner-friendly contribution opportunities.")

    reasons.append("GitScout ranks issues quickly first, then uses AI only for the selected issue.")

    return reasons[:4]

def is_selected_repo(repo: Dict[str, Any]) -> bool:
    """Return True if this repository is already in the current shortlist."""
    full_name = repo_full_name(repo)
    if not full_name:
        return False

    return any(repo_full_name(item) == full_name for item in st.session_state.selected_repos)


def add_repo_to_shortlist(repo: Dict[str, Any]) -> None:
    """Add a repository to the session shortlist without duplicates."""
    if not is_selected_repo(repo):
        st.session_state.selected_repos.append(dict(repo))




def issue_text(issue: Dict[str, Any]) -> str:
    return " ".join(
        [
            str(issue.get("title", "")),
            str(issue.get("body", "")),
            " ".join(unique_clean(issue.get("labels", []))),
        ]
    ).lower()


def infer_issue_type(issue: Dict[str, Any]) -> str:
    text = issue_text(issue)

    if any(word in text for word in ["doc", "readme", "documentation", "typo"]):
        return "Docs"
    if any(word in text for word in ["notebook", "example", "tutorial", "demo"]):
        return "Example notebook"
    if any(word in text for word in ["preprocess", "dataset", "data cleaning", "data pipeline"]):
        return "Data preprocessing"
    if any(word in text for word in ["train", "training", "model", "loss", "epoch"]):
        return "Model training"
    if any(word in text for word in ["metric", "accuracy", "evaluation", "benchmark"]):
        return "Evaluation"
    if any(word in text for word in ["api", "endpoint", "backend", "server"]):
        return "API/backend"
    if any(word in text for word in ["test", "pytest", "unit test"]):
        return "Testing"
    if any(word in text for word in ["bug", "fix", "error", "crash"]):
        return "Bug"
    return "General"


def infer_ml_area(issue: Dict[str, Any]) -> str:
    text = issue_text(issue)

    if any(word in text for word in ["nlp", "tokenizer", "transformer", "llm", "language model"]):
        return "NLP"
    if any(word in text for word in ["vision", "image", "opencv", "ocr", "segmentation", "detection"]):
        return "Computer Vision"
    if any(word in text for word in ["sklearn", "classification", "regression", "clustering"]):
        return "Classical ML"
    if any(word in text for word in ["pytorch", "tensorflow", "keras", "neural", "deep learning"]):
        return "Deep Learning"
    if any(word in text for word in ["data", "dataset", "preprocess", "cleaning"]):
        return "Data cleaning"
    if any(word in text for word in ["docker", "deploy", "pipeline", "mlops", "workflow"]):
        return "MLOps"
    return "General"


def infer_required_knowledge(issue: Dict[str, Any]) -> str:
    text = issue_text(issue)

    if "pytorch" in text:
        return "PyTorch"
    if "tensorflow" in text or "keras" in text:
        return "TensorFlow"
    if "sklearn" in text or "scikit" in text:
        return "Scikit-learn"
    if "numpy" in text or "pandas" in text:
        return "NumPy/Pandas"
    return "Python only"


def issue_matches_filters(issue: Dict[str, Any]) -> bool:
    labels = [label.lower() for label in unique_clean(issue.get("labels", []))]
    selected_labels = [label.lower() for label in st.session_state.issue_labels]
    custom_labels = [
        label.strip().lower()
        for label in st.session_state.custom_labels.split(",")
        if label.strip()
    ]

    required_labels = selected_labels + custom_labels
    if required_labels and not any(label in labels for label in required_labels):
        return False

    if st.session_state.assignee_filter == "Only unassigned" and issue.get("assignee"):
        return False

    if st.session_state.assignee_filter == "Assigned only" and not issue.get("assignee"):
        return False

    if int(issue.get("comments", 0) or 0) > int(st.session_state.max_comments):
        return False

    if st.session_state.issue_type != "Any" and infer_issue_type(issue) != st.session_state.issue_type:
        return False

    if st.session_state.ml_area != "Any" and infer_ml_area(issue) != st.session_state.ml_area:
        return False

    if st.session_state.required_knowledge != "Any" and infer_required_knowledge(issue) != st.session_state.required_knowledge:
        return False

    keyword = st.session_state.issue_keywords.strip().lower()
    if keyword and keyword not in issue_text(issue):
        return False

    return True


def local_issue_score(issue: Dict[str, Any]) -> float:
    score = 0.0
    labels = [label.lower() for label in unique_clean(issue.get("labels", []))]
    comments = int(issue.get("comments", 0) or 0)
    issue_type = infer_issue_type(issue)
    ml_area = infer_ml_area(issue)
    required = infer_required_knowledge(issue)

    if not issue.get("assignee"):
        score += 18
    if "good first issue" in labels:
        score += 22
    if "help wanted" in labels:
        score += 14

    if comments == 0:
        score += 16
    elif comments <= 2:
        score += 12
    elif comments <= 5:
        score += 8

    if issue_type in st.session_state.contribution_types:
        score += 10

    if ml_area in st.session_state.ml_interests or st.session_state.ml_area == ml_area:
        score += 10

    if required in st.session_state.user_skills or required == "Python only":
        score += 10

    created_at = issue.get("created_at")
    if created_at:
        try:
            created = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - created).days
            if age_days <= 30:
                score += 4
        except ValueError:
            pass

    return min(score, 100)


def score_badge(score: int) -> str:
    if score >= 80:
        return f"🟢 {score}"
    if score >= 55:
        return f"🟠 {score}"
    return f"🔴 {score}"


def issue_key(issue: Dict[str, Any]) -> str:
    return str(issue.get("url") or issue.get("html_url") or issue.get("title") or safe_key(issue))


def is_issue_saved(issue: Dict[str, Any]) -> bool:
    key = issue_key(issue)
    return any(saved.get("_saved_key") == key for saved in st.session_state.saved_issues)


def toggle_save_issue(issue: Dict[str, Any]) -> None:
    key = issue_key(issue)

    if is_issue_saved(issue):
        st.session_state.saved_issues = [
            saved for saved in st.session_state.saved_issues
            if saved.get("_saved_key") != key
        ]
    else:
        saved = dict(issue)
        saved["_saved_key"] = key
        saved["_saved_at"] = datetime.now(timezone.utc).isoformat()
        repo = st.session_state.active_repo_detail or st.session_state.active_repo or {}
        saved["_repo_name"] = get_repo_display_name(repo)
        st.session_state.saved_issues.append(saved)


# ─────────────────────────────────────────────────────────────
# DATA ACTIONS
# ─────────────────────────────────────────────────────────────

def search_projects() -> None:
    try:
        with st.spinner("Finding AI/ML repositories..."):
            st.session_state.repo_results = cached_search_projects(
                keywords=st.session_state.keywords,
                tech_stack=st.session_state.tech_stack,
                language=st.session_state.language,
                difficulty=st.session_state.difficulty,
                sort_by=st.session_state.sort_by,
            )
        st.session_state.page = "discover"

    except Exception as exc:
        st.error(f"Search failed: {exc}")



def load_default_repos_once() -> None:
    """Load starter AI/ML repos on first visit so the home page is never empty."""
    if st.session_state.default_repos_loaded or st.session_state.repo_results:
        return

    try:
        with st.spinner("Loading starter AI/ML repositories..."):
            st.session_state.repo_results = cached_search_projects(
                keywords="python machine learning ai ml docs",
                tech_stack="",
                language="Python",
                difficulty="",
                sort_by=DEFAULT_SORT,
            )
        st.session_state.default_repos_loaded = True
    except Exception:
        st.session_state.default_repos_loaded = True


def enrich_active_repo(repo: Dict[str, Any]) -> Dict[str, Any]:
    full_name = repo_full_name(repo)
    detail = dict(repo)

    if not full_name:
        detail["summary"] = repo.get("description", "No description available.")
        return detail

    try:
        metadata = cached_repo_metadata(full_name)
        detail.update(
            {
                "stars": metadata.get("stars", repo.get("stars", 0)),
                "forks": metadata.get("forks", repo.get("forks", 0)),
                "open_issues": metadata.get("open_issues_count", repo.get("open_issues", 0)),
                "language": metadata.get("language", repo.get("language", "")),
                "topics": metadata.get("topics", repo.get("topics", [])),
                "updated_at": metadata.get("updated_at", repo.get("updated_at", "")),
            }
        )
    except Exception:
        pass

    try:
        readme = cached_repo_readme(full_name)
        detail["readme"] = readme
        summary_data = cached_repo_summary(detail)

        if isinstance(summary_data, dict):
            detail["summary"] = summary_data.get("summary", detail.get("description", ""))
        else:
            detail["summary"] = detail.get("description", "No summary available.")
    except Exception:
        detail["summary"] = detail.get("description", "No summary available.")

    return detail


def select_repo_for_project(repo: Dict[str, Any]) -> None:
    add_repo_to_shortlist(repo)
    st.session_state.active_repo = repo
    st.session_state.active_repo_detail = None
    st.session_state.ranked_issues = []
    st.session_state.selected_issue_idx = 0
    st.session_state.issue_ai_breakdowns = {}
    go("queue")


def find_and_rank_issues_fast() -> None:
    repo = st.session_state.active_repo_detail or st.session_state.active_repo

    if not repo:
        st.warning("Select a repository first.")
        return

    full_name = repo_full_name(repo)

    if not full_name:
        st.error("This project does not have a valid GitHub repository URL.")
        return

    try:
        with st.spinner("Fetching and ranking issues without AI..."):
            raw_issues = cached_open_issues(full_name)

        filtered = [issue for issue in raw_issues if issue_matches_filters(issue)]

        if not filtered:
            st.session_state.ranked_issues = []
            st.warning("No issues matched your filters.")
            return

        ranked = []
        for issue in filtered:
            issue_copy = dict(issue)
            issue_copy["fast_score"] = round(local_issue_score(issue_copy))
            issue_copy["issue_type"] = infer_issue_type(issue_copy)
            issue_copy["ml_area"] = infer_ml_area(issue_copy)
            issue_copy["required_knowledge"] = infer_required_knowledge(issue_copy)
            issue_copy["summary"] = truncate(issue_copy.get("body") or issue_copy.get("title"), 160)
            issue_copy.setdefault("difficulty", "Beginner" if issue_copy["fast_score"] >= 70 else "Intermediate")
            issue_copy.setdefault("competition", "Low" if int(issue_copy.get("comments", 0) or 0) <= 2 else "Medium")
            issue_copy.setdefault("skill_match", min(10, max(1, round(issue_copy["fast_score"] / 10))))
            ranked.append(issue_copy)

        sort_by = st.session_state.issue_sort
        if sort_by == "Lowest competition":
            ranked.sort(key=lambda item: int(item.get("comments", 0) or 0))
        elif sort_by == "Newest":
            ranked.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        elif sort_by == "Beginner easiest":
            ranked.sort(key=lambda item: (item.get("difficulty") != "Beginner", -item.get("fast_score", 0)))
        else:
            ranked.sort(key=lambda item: item.get("fast_score", 0), reverse=True)

        st.session_state.ranked_issues = ranked
        st.session_state.selected_issue_idx = 0

    except Exception as exc:
        st.error(f"Issue search failed: {exc}")


def generate_ai_breakdown_for_selected() -> None:
    if not st.session_state.ranked_issues:
        return

    idx = min(st.session_state.selected_issue_idx, len(st.session_state.ranked_issues) - 1)
    issue = st.session_state.ranked_issues[idx]
    key = issue_key(issue)

    if key in st.session_state.issue_ai_breakdowns:
        return

    repo = st.session_state.active_repo_detail or st.session_state.active_repo or {}
    full_name = repo_full_name(repo)
    issue_number = issue.get("number")

    try:
        with st.spinner("Fetching full issue context and generating AI breakdown..."):
            if full_name and issue_number:
                issue_context = cached_issue_context(full_name, int(issue_number))
            else:
                issue_context = dict(issue)

            issue_context.update({
                "fast_score": issue.get("fast_score"),
                "issue_type": issue.get("issue_type"),
                "ml_area": issue.get("ml_area"),
                "required_knowledge": issue.get("required_knowledge"),
            })

            user_profile = {
                "skill_level": st.session_state.skill_level,
                "user_skills": st.session_state.user_skills,
                "ml_interests": st.session_state.ml_interests,
                "contribution_types": st.session_state.contribution_types,
            }

            ai_result = cached_deep_issue_analysis(issue_context, user_profile)

        enriched_issue = dict(issue)
        enriched_issue.update(issue_context)
        if isinstance(ai_result, dict):
            enriched_issue.update(ai_result)

        enriched_issue.setdefault("title", issue.get("title", "Untitled issue"))
        enriched_issue.setdefault("url", issue.get("url", "#"))
        enriched_issue.setdefault("labels", issue.get("labels", []))
        enriched_issue.setdefault("comments", issue.get("comments", 0))

        st.session_state.issue_ai_breakdowns[key] = enriched_issue

    except Exception as exc:
        # Keep the UI useful even when Gemini/API fails.
        fallback_issue = dict(issue)
        fallback_issue.update({
            "core_problem": "AI breakdown could not be generated. The issue body is still available below; read it as the source of truth.",
            "expected_change": "Could not extract this automatically. Open the GitHub issue and check the requested change from the maintainer.",
            "what_to_do": "Review the issue body, identify the expected change, inspect related files, and ask for clarification if needed.",
            "files_likely_needed": ["Not confidently detected"],
            "first_step": "Open the issue on GitHub and read the full issue body and latest maintainer comments.",
            "risks_or_unknowns": [f"AI/API error: {exc}"],
            "comment_short": "Hi! I’d like to work on this issue. I’ll review the details and start with the expected change. Please assign this to me if available.",
            "comment_detailed": "Hi! I’d like to work on this issue. I’ll first review the issue body, identify the expected change, inspect the related files, and ask for clarification if needed. Please assign this to me if available.",
        })
        st.session_state.issue_ai_breakdowns[key] = fallback_issue
        st.warning(f"AI breakdown used fallback mode: {exc}")

# ─────────────────────────────────────────────────────────────
# NAVIGATION
# ─────────────────────────────────────────────────────────────

def render_nav() -> None:
    brand_col, nav_col = st.columns([2.5, 2.4])

    with brand_col:
        st.markdown("## 🧭 GitScout AI")
        st.caption("AI/ML contribution roadmap builder")

    with nav_col:
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            if st.button("Roadmap", key="nav_discover", type="primary" if st.session_state.page == "discover" else "secondary", use_container_width=True):
                go("discover")

        with c2:
            if st.button("Project", key="nav_queue", type="primary" if st.session_state.page == "queue" else "secondary", use_container_width=True):
                go("queue")

        with c3:
            if st.button("Issue Coach", key="nav_issues", type="primary" if st.session_state.page == "issues" else "secondary", use_container_width=True):
                go("issues")

        with c4:
            if st.button(f"My Roadmap ({len(st.session_state.saved_issues)})", key="nav_saved", type="primary" if st.session_state.page == "saved" else "secondary", use_container_width=True):
                go("saved")

    st.divider()


# ─────────────────────────────────────────────────────────────
# DISCOVER PAGE
# ─────────────────────────────────────────────────────────────

def render_skill_matcher() -> None:
    with st.container(border=True):
        st.subheader("Build your AI/ML contribution roadmap")
        st.caption("Answer this like a 30-second quiz. GitScout uses it to recommend repos and rank issues.")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.multiselect(
                "I already know",
                [
                    "Python basics",
                    "NumPy/Pandas",
                    "Scikit-learn",
                    "PyTorch",
                    "TensorFlow",
                    "NLP",
                    "Computer Vision",
                    "Docs",
                ],
                key="user_skills",
            )

        with c2:
            st.multiselect(
                "I want to learn",
                [
                    "AI/ML",
                    "NLP",
                    "Computer Vision",
                    "Classical ML",
                    "Deep Learning",
                    "Data cleaning",
                    "MLOps",
                ],
                key="ml_interests",
            )

        with c3:
            st.multiselect(
                "I want to contribute through",
                [
                    "Docs",
                    "Bug",
                    "Example notebook",
                    "Data preprocessing",
                    "Model training",
                    "Evaluation",
                    "API/backend",
                    "Testing",
                ],
                key="contribution_types",
            )
            st.selectbox(
                "Time available",
                ["30 min", "1-2 hours", "Weekend"],
                key="time_available",
            )

        stage_labels = ["Python", "NumPy/Pandas", "Scikit-learn", "PyTorch", "Real PR"]
        progress = 0.2
        if "NumPy/Pandas" in st.session_state.user_skills:
            progress = 0.4
            st.session_state.roadmap_stage = "NumPy/Pandas → Scikit-learn"
        if "Scikit-learn" in st.session_state.user_skills:
            progress = 0.6
            st.session_state.roadmap_stage = "Scikit-learn → PyTorch"
        if "PyTorch" in st.session_state.user_skills or "TensorFlow" in st.session_state.user_skills:
            progress = 0.8
            st.session_state.roadmap_stage = "Deep Learning → Real PR"

        st.progress(progress, text=f"Roadmap stage: {st.session_state.roadmap_stage}")
        st.caption(" → ".join(stage_labels))

        b1, b2 = st.columns([1, 3])
        with b1:
            if st.button("Build my roadmap", key="build_roadmap_btn", type="primary", use_container_width=True):
                st.session_state.roadmap_built = True
                query_parts = ["python", "machine learning"]
                query_parts.extend(st.session_state.ml_interests or [])
                query_parts.extend(st.session_state.contribution_types or [])
                st.session_state.keywords = " ".join(query_parts)
                st.session_state.hero_keywords = st.session_state.keywords
                st.session_state.repo_filter_keywords = st.session_state.keywords
                search_projects()
                st.rerun()
        with b2:
            st.caption("Tip: for your first PR, choose Docs, Bug, or Example notebook with max 5 comments.")


def render_repo_refine_panel() -> None:
    options = cached_filter_options()

    tech_stacks = [""] + options.get("tech_stacks", [])
    languages = [""] + options.get("languages", [])
    difficulties = [""] + options.get("difficulties", [])

    if "Python" not in languages:
        languages.insert(1, "Python")

    if st.session_state.tech_stack not in tech_stacks:
        st.session_state.tech_stack = ""
    if st.session_state.language not in languages:
        st.session_state.language = "Python" if "Python" in languages else ""
    if st.session_state.difficulty not in difficulties:
        st.session_state.difficulty = ""

    with st.container(border=True):
        top_left, top_right = st.columns([5, 1])

        with top_left:
            st.subheader("Refine AI/ML repositories")
            st.caption("Use search and GSSoC-style filters to narrow down projects.")

        with top_right:
            if st.button("Close", key="close_repo_filters", use_container_width=True):
                st.session_state.repo_filters_open = False
                st.rerun()

        f1, f2, f3, f4, f5 = st.columns([1.4, 1, 1, 1, 1])

        with f1:
            st.text_input(
                "Search",
                key="repo_filter_keywords",
                placeholder="NLP, pandas, pytorch, docs...",
            )

        with f2:
            st.selectbox(
                "Tech stack",
                tech_stacks,
                key="tech_stack",
                format_func=lambda value: "All tech stacks" if not value else value,
            )

        with f3:
            st.selectbox(
                "Language",
                languages,
                key="language",
                format_func=lambda value: "All languages" if not value else value,
            )

        with f4:
            st.selectbox(
                "Difficulty",
                difficulties,
                key="difficulty",
                format_func=lambda value: "All difficulties" if not value else value,
            )

        with f5:
            st.selectbox(
                "Sort by",
                [
                    DEFAULT_SORT,
                    "Most Open Issues",
                    "Recently Updated",
                    "Beginner Friendly First",
                    "Name A-Z",
                ],
                key="sort_by",
            )

        a1, a2, _ = st.columns([1, 1, 4])

        with a1:
            if st.button("Apply filters", key="apply_repo_filters", type="primary", use_container_width=True):
                st.session_state.keywords = st.session_state.repo_filter_keywords
                search_projects()

        with a2:
            if st.button("Reset", key="reset_repo_filters", use_container_width=True):
                st.session_state.repo_filter_keywords = ""
                st.session_state.keywords = ""
                st.session_state.tech_stack = ""
                st.session_state.language = "Python"
                st.session_state.difficulty = ""
                st.session_state.sort_by = DEFAULT_SORT
                search_projects()


def render_repo_card(repo: Dict[str, Any], idx: int) -> None:
    url = repo_url(repo)
    display_name = get_repo_display_name(repo)
    tags = get_repo_tags(repo)
    summary = truncate(repo.get("summary") or repo.get("description"), 150)

    best_for = infer_best_for(repo)
    required = infer_required_skills(repo)
    fit = infer_contribution_fit(repo)
    work = infer_available_work(repo)

    stars = github_stat(repo.get("stars"))
    forks = github_stat(repo.get("forks"))
    open_issues = github_stat(repo.get("open_issues") or repo.get("open_issues_count"))

    with st.container(border=True):
        h1, h2 = st.columns([0.16, 0.84])

        with h1:
            st.markdown(f"### {display_name[:1].upper()}")

        with h2:
            st.markdown(f"**`{display_name}`**")
            st.caption(f"{fit} · {best_for}")

        st.write(summary)
        st.caption(f"Best for: {best_for}")
        st.caption(f"Required: {' · '.join(required)}")
        st.caption(f"Work: {' · '.join(work)}")

        if tags:
            st.caption("Tags: " + " · ".join(tags[:4]))

        st.divider()

        if any(value != "—" for value in [stars, forks, open_issues]):
            m1, m2, m3 = st.columns(3)
            m1.caption(f"⭐ {stars}")
            m2.caption(f"🍴 {forks}")
            m3.caption(f"💬 {open_issues} issues")
        else:
            st.caption("GitHub stats load on the project page.")

        b1, b2 = st.columns(2)

        with b1:
            if st.button("View Project →", key=f"view_repo_{idx}_{safe_key(display_name)}", type="primary", use_container_width=True):
                select_repo_for_project(repo)

        with b2:
            st.link_button("GitHub ↗", url, use_container_width=True)


def discover_page() -> None:
    load_default_repos_once()

    with st.container(border=True):
        left, right = st.columns([1.18, 0.82])

        with left:
            st.caption(
                f"🧭 {len(st.session_state.repo_results)} recommended repos · "
                f"{len(st.session_state.ranked_issues)} ranked issues · "
                f"{len(st.session_state.saved_issues)} saved to roadmap"
            )
            st.title("Your AI/ML open-source roadmap starts here.")
            st.write(
                "Tell GitScout what you know, get beginner-friendly AI/ML repos, then use the Issue Coach "
                "to understand the task and comment confidently."
            )

        with right:
            with st.container(border=True):
                st.markdown("**Current loop**")
                st.write("Discover → Understand → Comment → Get assigned")
                st.caption("The main feature is not search — it is helping you understand the issue deeply.")

    render_skill_matcher()

    s1, s2 = st.columns([5, 1])

    with s1:
        st.text_input(
            "Search projects",
            key="hero_keywords",
            placeholder="Optional search: pandas docs, NLP, PyTorch, data preprocessing...",
            label_visibility="collapsed",
        )

    with s2:
        if st.button("Search", key="hero_search_btn", type="primary", use_container_width=True):
            query = st.session_state.hero_keywords.strip() or "python ai ml machine learning"
            st.session_state.keywords = query
            st.session_state.repo_filter_keywords = query
            search_projects()

    with st.expander("Advanced repository filters", expanded=False):
        render_repo_refine_panel()

    h1, h2 = st.columns([5, 1])

    with h1:
        st.subheader("Recommended repos for AI/ML beginners")
        st.caption("Starter recommendations appear automatically. Open a repo to load real GitHub stats and issue context.")

    with h2:
        if st.button("Refresh", key="refresh_default_repos", use_container_width=True):
            st.session_state.default_repos_loaded = False
            st.session_state.repo_results = []
            load_default_repos_once()
            st.rerun()

    if not st.session_state.repo_results:
        st.info("No repos found yet. Try searching: `pandas`, `NLP`, `PyTorch`, `data preprocessing`, or `docs`.")
        return

    for row_start in range(0, len(st.session_state.repo_results[:12]), 3):
        row = st.session_state.repo_results[row_start: row_start + 3]
        cols = st.columns(3)

        for offset, repo in enumerate(row):
            with cols[offset]:
                render_repo_card(repo, row_start + offset)


# ─────────────────────────────────────────────────────────────
# PROJECT PAGE
# ─────────────────────────────────────────────────────────────

def queue_page() -> None:
    repo = st.session_state.active_repo

    if not repo:
        st.warning("Select a repository first.")
        return

    if st.button("← Back to repositories", key="back_to_repos"):
        go("discover")

    if st.session_state.active_repo_detail is None:
        with st.spinner("Loading repository details and AI summary for this repo only..."):
            st.session_state.active_repo_detail = enrich_active_repo(repo)

    detail = st.session_state.active_repo_detail

    url = repo_url(detail)
    display_name = get_repo_display_name(detail)
    tags = get_repo_tags(detail)
    summary = detail.get("summary") or detail.get("description") or "No summary available."
    summary = truncate(summary, 650)

    stars = github_stat(detail.get("stars"))
    forks = github_stat(detail.get("forks"))
    open_issues = github_stat(detail.get("open_issues") or detail.get("open_issues_count"))

    best_for = infer_best_for(detail)
    required = infer_required_skills(detail)
    fit = infer_contribution_fit(detail)
    work = infer_available_work(detail)

    left, right = st.columns([0.9, 1.1])

    with left:
        with st.container(border=True):
            st.caption(f"`{display_name}`")
            st.header(detail.get("name", display_name))
            st.write(summary)

            if tags:
                st.caption("Tags: " + " · ".join(tags))

            s1, s2, s3 = st.columns(3)
            s1.metric("Stars", stars)
            s2.metric("Forks", forks)
            s3.metric("Open issues", open_issues)

            st.divider()
            st.markdown(f"**Best for:** {best_for}")
            st.markdown(f"**Required skills:** {' · '.join(required)}")
            st.markdown(f"**Contribution fit:** {fit}")
            st.markdown(f"**Available work:** {' · '.join(work)}")

        st.link_button("Open repository on GitHub ↗", url, use_container_width=True)

    with right:
        with st.container(border=True):
            st.subheader("Why this repo matches you")

            for reason in dynamic_repo_reasons(detail):
                st.write(f"✓ {reason}")

        with st.container(border=True):
            st.subheader("Suggested contribution path")
            st.write("1. Start with docs/examples or low-comment beginner issues.")
            st.write("2. Move to small bugs or tests in the same repo.")
            st.write("3. After one merged PR, try a data/model-related issue.")

        if st.button("Find issues in this repo →", key="goto_issues", type="primary", use_container_width=True):
            go("issues")


# ─────────────────────────────────────────────────────────────
# ISSUES PAGE
# ─────────────────────────────────────────────────────────────

def render_issue_refine_panel() -> None:
    with st.container(border=True):
        st.subheader("Find low-competition issues")
        st.caption("Start simple. Advanced filters are hidden so the page feels like a coach, not a form.")

        c1, c2, c3 = st.columns([1, 1, 1.2])

        with c1:
            st.selectbox("Assignee", ["Only unassigned", "Any", "Assigned only"], key="assignee_filter")

        with c2:
            st.number_input("Max comments", min_value=0, max_value=50, step=1, key="max_comments")

        with c3:
            st.selectbox(
                "Sort",
                ["Best match", "Lowest competition", "Newest", "Beginner easiest"],
                key="issue_sort",
            )

        with st.expander("Advanced issue filters", expanded=False):
            common_labels = [
                "good first issue",
                "help wanted",
                "bug",
                "documentation",
                "enhancement",
                "frontend",
                "backend",
                "ui",
                "api",
                "python",
                "javascript",
            ]

            a1, a2, a3 = st.columns(3)

            with a1:
                st.multiselect("Labels", common_labels, key="issue_labels")
                st.text_input("Custom labels", key="custom_labels", placeholder="auth, api, ui...")

            with a2:
                st.selectbox(
                    "Issue type",
                    [
                        "Any",
                        "Docs",
                        "Bug",
                        "Example notebook",
                        "Data preprocessing",
                        "Model training",
                        "Evaluation",
                        "API/backend",
                        "Testing",
                    ],
                    key="issue_type",
                )
                st.selectbox(
                    "ML area",
                    [
                        "Any",
                        "NLP",
                        "Computer Vision",
                        "Classical ML",
                        "Deep Learning",
                        "Data cleaning",
                        "MLOps",
                        "General",
                    ],
                    key="ml_area",
                )

            with a3:
                st.selectbox(
                    "Required knowledge",
                    ["Any", "Python only", "NumPy/Pandas", "Scikit-learn", "PyTorch", "TensorFlow"],
                    key="required_knowledge",
                )
                st.text_input("Keyword", key="issue_keywords", placeholder="loading, docs, tokenizer...")

        b1, b2 = st.columns([1, 3])
        with b1:
            if st.button("Find beginner issues", key="find_best_issues", type="primary", use_container_width=True):
                find_and_rank_issues_fast()
        with b2:
            st.caption("This ranking is instant and rule-based. AI runs only after you select an issue.")


def render_issue_list_item(issue: Dict[str, Any], idx: int) -> None:
    selected = idx == st.session_state.selected_issue_idx
    score = int(issue.get("fast_score", 0))
    summary = truncate(issue.get("summary") or issue.get("body") or issue.get("title"), 135)
    competition = issue.get("competition_level") or issue.get("competition", "N/A")
    saved = is_issue_saved(issue)

    with st.container(border=True):
        c1, c2 = st.columns([0.14, 0.86])

        with c1:
            st.metric("Score", score_badge(score))

        with c2:
            st.markdown(f"**{strip_markdown(issue.get('title', 'Untitled issue'))}**")
            st.caption(summary)
            st.caption(
                f"{issue.get('issue_type', 'General')} · "
                f"{issue.get('ml_area', 'General')} · "
                f"{issue.get('required_knowledge', 'Python only')} · "
                f"{competition} competition · "
                f"{issue.get('comments', 0)} comments"
            )

        b1, b2 = st.columns(2)

        with b1:
            label = "Selected" if selected else "Select"
            if st.button(label, key=f"select_issue_{idx}_{safe_key(issue.get('title', 'issue'))}", use_container_width=True):
                st.session_state.selected_issue_idx = idx
                st.rerun()

        with b2:
            save_label = "Unsave" if saved else "Save"
            if st.button(save_label, key=f"save_issue_{idx}_{safe_key(issue_key(issue))}", use_container_width=True):
                toggle_save_issue(issue)
                st.rerun()


def contribution_comment(issue: Dict[str, Any]) -> str:
    title = issue.get("title", "this issue")
    first_step = issue.get("first_step") or "I’ll start by reviewing the related files and understanding the expected change."

    return (
        f"Hi! I’d like to work on this issue.\n\n"
        f"I reviewed the issue: \"{strip_markdown(title)}\".\n\n"
        f"My first step will be: {strip_markdown(first_step)}\n\n"
        f"Please assign this to me if it is still available. Thank you!"
    )


def get_ai_breakdown(issue: Dict[str, Any]) -> Dict[str, Any]:
    key = issue_key(issue)
    stored = st.session_state.issue_ai_breakdowns.get(key)
    return stored or issue


def _stringify_list(value: Any) -> str:
    if not value:
        return "Not clear from issue."
    if isinstance(value, list):
        return "\n".join(f"- {strip_markdown(item)}" for item in value if str(item).strip())
    return strip_markdown(value)


def _default_comment(issue: Dict[str, Any]) -> str:
    title = strip_markdown(issue.get("title", "this issue"))
    first_step = strip_markdown(issue.get("first_step") or "I’ll first read the issue carefully and reproduce/inspect the relevant part of the project.")
    return (
        f"Hi! I’d like to work on this issue.\n\n"
        f"I understand the task is related to: {title}.\n\n"
        f"My first step will be: {first_step}\n\n"
        f"Please assign this to me if it is still available. Thank you!"
    )


def render_issue_detail(issue: Dict[str, Any]) -> None:
    key = issue_key(issue)
    enriched = get_ai_breakdown(issue)

    score = int(issue.get("fast_score", 0))
    labels = unique_clean(enriched.get("labels", []))
    summary = truncate(enriched.get("summary") or enriched.get("body") or enriched.get("title"), 260)
    competition = enriched.get("competition_level") or enriched.get("competition", "N/A")
    saved = is_issue_saved(issue)

    has_ai = key in st.session_state.issue_ai_breakdowns

    core_problem = enriched.get("core_problem") or "Generate AI breakdown to extract the actual core problem from the full issue body."
    expected_change = enriched.get("expected_change") or "Generate AI breakdown to understand what the maintainer expects to be changed."
    why_it_matters = enriched.get("why_it_matters") or ""
    what_to_do = enriched.get("what_to_do") or enriched.get("explanation") or "Generate AI breakdown to get a clear step-by-step explanation."
    likely_files = enriched.get("files_likely_needed") or "Generate AI breakdown to estimate likely files or project areas."
    first_step = enriched.get("first_step") or "Open the issue on GitHub and read the latest maintainer comments."
    plan = enriched.get("step_by_step_plan") or []
    risks = enriched.get("risks_or_unknowns") or []

    with st.container(border=True):
        top_left, top_right = st.columns([0.75, 0.25])

        with top_left:
            if labels:
                st.caption(" · ".join(labels[:6]))
            st.header(strip_markdown(enriched.get("title", "Untitled issue")))

        with top_right:
            st.metric("Scout score", score_badge(score))

        st.write(summary)

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Issue type", enriched.get("issue_type", "General"))
        d2.metric("ML area", enriched.get("ml_area", "General"))
        d3.metric("Comments", enriched.get("comments", enriched.get("comments_count", 0)))
        d4.metric("Competition", competition)

        st.divider()

        action_1, action_2 = st.columns(2)

        with action_1:
            if not has_ai:
                if st.button("Understand this issue with AI", key=f"generate_ai_{safe_key(key)}", type="primary", use_container_width=True):
                    generate_ai_breakdown_for_selected()
                    st.rerun()
            else:
                st.success("AI breakdown generated.")

        with action_2:
            save_label = "Unsave issue" if saved else "Save issue"
            if st.button(save_label, key=f"save_selected_{safe_key(key)}", use_container_width=True):
                toggle_save_issue(issue)
                st.rerun()

        st.caption("GitScout uses the issue body as the source of truth. Comments are treated only as extra context.")

        st.markdown("**🎯 Core problem**")
        st.write(truncate(core_problem, 700))

        st.markdown("**🛠 Expected change**")
        st.write(truncate(expected_change, 700))

        if why_it_matters:
            st.markdown("**💡 Why it matters**")
            st.write(truncate(why_it_matters, 500))

        st.markdown("**⚡ What you'll likely do**")
        st.write(truncate(what_to_do, 700))

        st.markdown("**📁 Files / areas likely involved**")
        st.code(_stringify_list(likely_files), language=None)

        if plan:
            st.markdown("**🧭 Step-by-step starting plan**")
            for i, step in enumerate(plan[:6], start=1):
                st.write(f"{i}. {strip_markdown(step)}")

        st.markdown("**🚀 First step**")
        st.write(truncate(first_step, 450))

        if risks:
            with st.expander("Risks or unclear parts"):
                for item in risks[:5]:
                    st.write(f"- {strip_markdown(item)}")

        with st.expander("Original GitHub issue body", expanded=False):
            st.write(strip_markdown(enriched.get("body", "No issue body available.")))

        st.divider()
        st.markdown("**📋 Ready-to-copy comment**")

        style_key = f"comment_style_{safe_key(key)}"
        style = st.selectbox(
            "Comment style",
            ["Short and polite", "Beginner-friendly", "Confident technical", "Detailed plan"],
            key=style_key,
        )

        comment_lookup_key = f"{key}:{style}"
        existing_comment = st.session_state.generated_comments.get(comment_lookup_key)

        if existing_comment:
            comment_text = existing_comment
        elif has_ai and style == "Short and polite" and enriched.get("comment_short"):
            comment_text = enriched.get("comment_short")
        elif has_ai and style == "Detailed plan" and enriched.get("comment_detailed"):
            comment_text = enriched.get("comment_detailed")
        else:
            comment_text = _default_comment(enriched)

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Improve comment with AI", key=f"improve_comment_{safe_key(comment_lookup_key)}", use_container_width=True):
                try:
                    with st.spinner("Writing a better GitHub comment..."):
                        generated = cached_contribution_comment(enriched, style)
                    st.session_state.generated_comments[comment_lookup_key] = generated.get("comment", comment_text)
                    st.rerun()
                except Exception as exc:
                    fallback = _default_comment(enriched)
                    st.session_state.generated_comments[comment_lookup_key] = fallback
                    st.warning(f"Comment AI fallback used: {exc}")
                    st.rerun()

        with c2:
            if st.button("Reset comment", key=f"reset_comment_{safe_key(comment_lookup_key)}", use_container_width=True):
                st.session_state.generated_comments.pop(comment_lookup_key, None)
                st.rerun()

        st.code(comment_text, language=None)

    st.link_button("Open issue on GitHub ↗", enriched.get("url", "#"), use_container_width=True)

def issues_page() -> None:
    repo = st.session_state.active_repo_detail or st.session_state.active_repo

    if not repo:
        st.warning("Select a repository first.")
        return

    display_name = get_repo_display_name(repo)

    with st.container(border=True):
        left, right = st.columns([3, 2])

        with left:
            if st.button("← Back to project", key="back_to_project"):
                go("queue")

            st.subheader("Issue Coach")
            st.caption(f"{display_name} · {st.session_state.skill_level} mode · max {st.session_state.max_comments} comments")

        with right:
            st.markdown("**Flow:** Found → Understand → Confirm → Comment")
            st.progress(0.5 if st.session_state.ranked_issues else 0.25)

    render_issue_refine_panel()

    if not st.session_state.ranked_issues:
        st.info("Click **Find beginner issues** to rank open issues. Then select one and use **Understand this issue with AI**.")
        return

    left_col, right_col = st.columns([0.9, 1.1])

    with left_col:
        st.subheader("Ranked issues")
        for idx, issue in enumerate(st.session_state.ranked_issues):
            render_issue_list_item(issue, idx)

    with right_col:
        st.subheader("Understand this issue")
        selected_idx = min(st.session_state.selected_issue_idx, len(st.session_state.ranked_issues) - 1)
        render_issue_detail(st.session_state.ranked_issues[selected_idx])


# ─────────────────────────────────────────────────────────────
# SAVED PAGE
# ─────────────────────────────────────────────────────────────

def saved_page() -> None:
    st.subheader("🧭 My Roadmap")
    st.caption("Your saved contribution path. Session-based for now; database can come later.")

    with st.container(border=True):
        st.markdown("**Roadmap progress**")
        st.write("1. Choose skills → 2. Pick repo → 3. Understand issue → 4. Comment → 5. PR")
        progress_value = 0.2
        if st.session_state.selected_repos:
            progress_value = 0.4
        if st.session_state.ranked_issues:
            progress_value = 0.6
        if st.session_state.saved_issues:
            progress_value = 0.8
        st.progress(progress_value)

    if not st.session_state.saved_issues:
        with st.container(border=True):
            st.write("No saved issues yet.")
            st.write("Save issues from the Issue Coach to build your contribution roadmap.")
        return

    for idx, issue in enumerate(st.session_state.saved_issues):
        with st.container(border=True):
            st.markdown(f"**{strip_markdown(issue.get('title', 'Untitled issue'))}**")
            st.caption(issue.get("_repo_name", "Saved repo"))
            st.write(truncate(issue.get("summary") or issue.get("body") or issue.get("title"), 180))

            c1, c2, c3 = st.columns(3)

            with c1:
                st.link_button("Open issue ↗", issue.get("url", "#"), use_container_width=True)

            with c2:
                if st.button("Mark in progress", key=f"progress_saved_{idx}_{safe_key(issue_key(issue))}", use_container_width=True):
                    st.toast("Marked as in progress for this session.")

            with c3:
                if st.button("Remove", key=f"remove_saved_{idx}_{safe_key(issue_key(issue))}", use_container_width=True):
                    st.session_state.saved_issues.pop(idx)
                    st.rerun()


# ─────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────

def create_app() -> None:
    configure_page()
    init_session_state()
    inject_css()
    render_nav()

    page = st.session_state.page

    if page == "discover":
        discover_page()
    elif page == "queue":
        queue_page()
    elif page == "issues":
        issues_page()
    elif page == "saved":
        saved_page()
    else:
        discover_page()

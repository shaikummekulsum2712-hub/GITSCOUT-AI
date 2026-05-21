import streamlit as st

from src.ai_agent import analyze_issue, summarize_repository
from src.github_client import (
    extract_repo_full_name,
    fetch_open_issues,
    get_gssoc_filter_options,
    get_repository_metadata,
    get_repository_readme,
    search_gssoc_projects,
)
from src.issue_ranker import rank_issues


def configure_page():
    st.set_page_config(page_title="GitScout AI", page_icon="🚀", layout="wide")

    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(124,58,237,0.20), transparent 30%),
        radial-gradient(circle at top right, rgba(6,182,212,0.12), transparent 28%),
        #0F1117;
    color: #E5E7EB;
}

.block-container {
    padding: 2rem 3rem 3rem 3rem;
    max-width: 1500px;
}

section[data-testid="stSidebar"] {
    background: rgba(17, 24, 39, 0.92);
    border-right: 1px solid rgba(148, 163, 184, 0.14);
}

section[data-testid="stSidebar"] * {
    color: #E5E7EB;
}

h1, h2, h3 {
    letter-spacing: -0.03em;
}

.hero {
    padding: 2rem;
    border-radius: 28px;
    background: rgba(17, 24, 39, 0.74);
    border: 1px solid rgba(148, 163, 184, 0.14);
    box-shadow: 0 24px 80px rgba(0,0,0,0.25);
    margin-bottom: 1.5rem;
}

.hero-title {
    font-size: 3rem;
    font-weight: 800;
    color: #F8FAFC;
    line-height: 1.05;
}

.hero-subtitle {
    color: #94A3B8;
    font-size: 1.05rem;
    max-width: 760px;
    margin-top: 0.8rem;
    line-height: 1.7;
}

.top-nav {
    display: flex;
    gap: 0.6rem;
    margin-bottom: 1.3rem;
}

.stat-card {
    background: rgba(17, 24, 39, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 20px;
    padding: 1rem;
}

.stat-number {
    font-size: 2rem;
    font-weight: 800;
    color: #F8FAFC;
}

.stat-label {
    color: #94A3B8;
    font-size: 0.88rem;
}

.repo-card, .issue-card, .detail-card {
    background: rgba(17, 24, 39, 0.78);
    border: 1px solid rgba(148, 163, 184, 0.14);
    border-radius: 24px;
    padding: 1.25rem;
    box-shadow: 0 16px 50px rgba(0,0,0,0.18);
    margin-bottom: 1rem;
}

.repo-card:hover, .issue-card:hover {
    border-color: rgba(124, 58, 237, 0.5);
}

.card-title {
    color: #F8FAFC;
    font-size: 1.1rem;
    font-weight: 700;
    text-decoration: none;
}

.muted {
    color: #94A3B8;
    font-size: 0.9rem;
}

.pill {
    display: inline-block;
    padding: 0.28rem 0.65rem;
    border-radius: 999px;
    background: rgba(124, 58, 237, 0.18);
    color: #DDD6FE;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 0.15rem 0.15rem 0.15rem 0;
}

.green-pill {
    background: rgba(34,197,94,0.16);
    color: #86EFAC;
}

.cyan-pill {
    background: rgba(6,182,212,0.16);
    color: #67E8F9;
}

.score {
    display: inline-block;
    padding: 0.38rem 0.8rem;
    border-radius: 999px;
    background: linear-gradient(90deg, #7C3AED, #06B6D4);
    color: white;
    font-weight: 800;
    font-size: 0.82rem;
}

.stButton > button {
    border-radius: 14px;
    border: 1px solid rgba(148,163,184,0.16);
    background: linear-gradient(90deg, #7C3AED, #06B6D4);
    color: white;
    font-weight: 700;
    min-height: 2.75rem;
}

.stButton > button:hover {
    border-color: rgba(255,255,255,0.35);
    filter: brightness(1.08);
}

.stTextInput input,
.stSelectbox div[data-baseweb="select"],
.stMultiSelect div[data-baseweb="select"],
.stNumberInput input {
    background: #0B1020 !important;
    border-radius: 14px !important;
    border: 1px solid rgba(148,163,184,0.18) !important;
    color: #E5E7EB !important;
}

hr {
    border-color: rgba(148,163,184,0.15);
}

.empty-box {
    border: 1px dashed rgba(148,163,184,0.22);
    border-radius: 22px;
    padding: 2rem;
    text-align: center;
    color: #94A3B8;
    background: rgba(17, 24, 39, 0.45);
}

.topbar{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:2rem;
    padding-bottom:1rem;
    border-bottom:1px solid rgba(255,255,255,0.06);
}

.brand{
    display:flex;
    align-items:center;
    gap:0.7rem;
}

.brand-logo{
    color:#8b5cf6;
    font-size:1.4rem;
}

.brand-text{
    font-size:1.05rem;
    font-weight:700;
    color:white;
}

.nav-links{
    display:flex;
    gap:2rem;
}

.nav-links a{
    text-decoration:none;
    color:#94a3b8;
    font-size:0.95rem;
    font-weight:500;
}

.nav-links a:hover{
    color:white;
}

.mini-hero{
    margin-bottom:2rem;
}

.mini-title{
    font-size:2rem;
    font-weight:800;
    color:white;
    letter-spacing:-0.04em;
}

.mini-sub{
    margin-top:0.4rem;
    color:#94a3b8;
    font-size:0.95rem;
}

.repo-card-new{
    background:#111827;
    border:1px solid rgba(255,255,255,0.06);
    border-radius:20px;
    padding:1.1rem;
    margin-bottom:1rem;
    min-height:260px;
}

.repo-top{
    display:flex;
    gap:1rem;
    align-items:center;
    margin-bottom:1rem;
}

.repo-avatar{
    width:42px;
    height:42px;
    border-radius:12px;
    background:#1f2937;
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight:700;
}

.repo-name{
    font-weight:700;
    color:white;
    font-size:1rem;
}

.repo-meta{
    font-size:0.82rem;
    color:#94a3b8;
    margin-top:0.15rem;
}

.repo-summary{
    color:#d1d5db;
    line-height:1.6;
    font-size:0.92rem;
    margin-bottom:1rem;
}

.repo-tags{
    display:flex;
    flex-wrap:wrap;
    gap:0.45rem;
}

.tag{
    background:#1e293b;
    color:#cbd5e1;
    padding:0.28rem 0.65rem;
    border-radius:999px;
    font-size:0.74rem;
}

.issue-modern{
    background:#111827;
    border-radius:22px;
    padding:1.3rem;
    border:1px solid rgba(255,255,255,0.06);
    margin-bottom:1rem;
}

.issue-header{
    display:flex;
    justify-content:space-between;
    gap:1rem;
}

.issue-title a{
    color:white;
    font-size:1rem;
    font-weight:700;
    text-decoration:none;
}

.issue-summary{
    color:#cbd5e1;
    margin-top:0.6rem;
    line-height:1.6;
}

.issue-chips{
    display:flex;
    gap:0.5rem;
    flex-wrap:wrap;
    margin-top:1rem;
}

.issue-chips span{
    background:#1e293b;
    padding:0.3rem 0.65rem;
    border-radius:999px;
    font-size:0.74rem;
    color:#cbd5e1;
}

.score-ring{
    min-width:72px;
    height:72px;
    border-radius:999px;
    border:5px solid;
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight:800;
    color:white;
    font-size:1.1rem;
}

</style>
""",
        unsafe_allow_html=True,
    )


def init_session():
    defaults = {
        "page": "discover",
        "repo_results": [],
        "selected_repos": [],
        "ranked_issues": [],
        "saved_issues": [],
        "active_repo": None,
        "keywords": "",
        "tech_stack": "",
        "language": "",
        "difficulty": "",
        "sort_by": "Most Open Issues",
        "skill_level": "Beginner",
        "issue_keywords": "",
        "custom_labels": "",
        "issue_labels": ["good first issue", "help wanted"],
        "assignee_filter": "Only unassigned",
        "max_comments": 5,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def nav_button(label, page):
    if st.button(label, key=f"nav_{page}"):
        st.session_state.page = page
        st.rerun()

def render_top_nav():
    st.markdown(
        """
        <div class="topbar">
            <div class="brand">
                <span class="brand-logo">●</span>
                <span class="brand-text">GitScout AI</span>
            </div>

            <div class="nav-links">
                <a href="?page=discover" target="_self">Discover</a>
                <a href="?page=shortlist" target="_self">Shortlist</a>
                <a href="?page=issues" target="_self">Issues</a>
                <a href="?page=saved" target="_self">Saved</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    query_params = st.query_params

    if "page" in query_params:
        st.session_state.page = query_params["page"]


def render_sidebar():
    if st.session_state.page != "discover":
        return

    filters = get_gssoc_filter_options()

    with st.sidebar:
        st.markdown("## Discover")

        st.text_input(
            "Search repositories",
            key="keywords",
            placeholder="AI, backend, ML, docs..."
        )

        st.selectbox(
            "Tech Stack",
            [""] + filters["tech_stacks"],
            key="tech_stack"
        )

        st.selectbox(
            "Language",
            [""] + filters["languages"],
            key="language"
        )

        st.selectbox(
            "Difficulty",
            [""] + filters["difficulties"],
            key="difficulty"
        )

        st.selectbox(
            "Sort",
            [
                "Most Open Issues",
                "Most Good First Issues",
                "Beginner Friendly First",
                "Name A-Z"
            ],
            key="sort_by"
        )

        st.selectbox(
            "Your Skill Level",
            ["Beginner", "Intermediate", "Advanced"],
            key="skill_level"
        )

        st.markdown("")

        if st.button("Search Projects", use_container_width=True):
            search_projects()



def is_selected(repo):
    full_name = extract_repo_full_name(repo.get("repo_url") or repo.get("url"))
    return any(
        extract_repo_full_name(r.get("repo_url") or r.get("url")) == full_name
        for r in st.session_state.selected_repos
    )


def select_repo(repo):
    if not is_selected(repo):
        st.session_state.selected_repos.append(repo)
        st.toast("Added to shortlist ✅")


def search_projects():
    with st.spinner("Scouting matching repositories..."):
        projects = search_gssoc_projects(
            keywords=st.session_state.keywords,
            tech_stack=st.session_state.tech_stack,
            language=st.session_state.language,
            difficulty=st.session_state.difficulty,
            sort_by=st.session_state.sort_by,
        )

        final = []

        for repo in projects:
            try:
                full_name = extract_repo_full_name(repo.get("repo_url") or repo.get("url"))
                metadata = get_repository_metadata(full_name)

                repo["stars"] = metadata.get("stars", 0)
                repo["open_issues"] = metadata.get("open_issues_count", 0)

                if not repo.get("language"):
                    repo["language"] = metadata.get("language", "")

                repo["readme"] = get_repository_readme(full_name)

                try:
                    repo["summary"] = summarize_repository(repo).get("summary", "")
                except Exception:
                    repo["summary"] = repo.get("description", "")
            except Exception:
                repo["summary"] = repo.get("description", "")

            final.append(repo)

        st.session_state.repo_results = final
        st.session_state.page = "discover"

def render_hero():
    st.markdown(
        f"""
        <div class="mini-hero">
            <div class="mini-title">
                Discover low-competition open-source opportunities
            </div>

            <div class="mini-sub">
                {len(st.session_state.repo_results)} projects ·
                {len(st.session_state.selected_repos)} shortlisted ·
                {len(st.session_state.ranked_issues)} ranked issues
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_repo_card(repo):
    url = repo.get("url") or repo.get("repo_url") or "#"
    name = repo.get("name", "Unknown Repo")
    summary = repo.get("summary") or repo.get("description") or ""

    short_summary = summary[:140] + "..." if len(summary) > 140 else summary

    st.markdown(
        f"""
        <div class="repo-card-new">

            <div class="repo-top">
                <div class="repo-avatar">
                    {name[:1].upper()}
                </div>

                <div>
                    <div class="repo-name">{name}</div>
                    <div class="repo-meta">
                        ⭐ {repo.get("stars", 0)} ·
                        {repo.get("language", "Unknown")} ·
                        {repo.get("open_issues", 0)} issues
                    </div>
                </div>
            </div>

            <div class="repo-summary">
                {short_summary}
            </div>

            <div class="repo-tags">
                {"".join([f'<span class="tag">{x}</span>' for x in repo.get("tech_stack", [])[:4]])}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 1])

    with c1:
        st.link_button("Open Repo", url, use_container_width=True)

    with c2:
        if is_selected(repo):
            st.button(
                "Saved ✓",
                disabled=True,
                key=f"saved_{name}"
            )
        else:
            if st.button(
                "Shortlist",
                key=f"repo_{name}",
                use_container_width=True
            ):
                select_repo(repo)
                st.rerun()



def render_discover():
    render_hero()

    st.markdown("## Recommended Projects")
    st.caption("Search results are shown as scannable cards so you can compare quickly.")

    if not st.session_state.repo_results:
        st.markdown(
            """
<div class="empty-box">
    <h3>Your scout feed is empty</h3>
    <p>Use the filters on the left and click <b>Search Projects</b> to discover repos.</p>
</div>
""",
            unsafe_allow_html=True,
        )
        return

    cols = st.columns(3, gap="large")
    for i, repo in enumerate(st.session_state.repo_results):
        with cols[i % 3]:
            render_repo_card(repo)

    if st.session_state.selected_repos:
        st.markdown("---")
        if st.button("Continue to Shortlist →"):
            st.session_state.page = "shortlist"
            st.rerun()


def render_shortlist():
    st.markdown("## Your Contribution Queue")
    st.caption("Pick one shortlisted repository to analyze issues.")

    if not st.session_state.selected_repos:
        st.markdown('<div class="empty-box">No repos shortlisted yet.</div>', unsafe_allow_html=True)
        return

    cols = st.columns(2, gap="large")

    for i, repo in enumerate(st.session_state.selected_repos):
        with cols[i % 2]:
            st.markdown('<div class="repo-card">', unsafe_allow_html=True)
            st.markdown(f"### {repo.get('name')}")
            st.write(repo.get("summary", repo.get("description", "")))
            st.markdown(
                f'<div class="muted">⭐ {repo.get("stars", 0)} · 📋 {repo.get("open_issues", 0)} issues</div>',
                unsafe_allow_html=True,
            )

            if st.button("Analyze Issues", key=f"analyze_{repo.get('name')}"):
                st.session_state.active_repo = repo
                st.session_state.ranked_issues = []
                st.session_state.page = "issues"
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)


def issue_matches(issue):
    labels = [label.lower() for label in issue.get("labels", [])]

    selected = [x.lower() for x in st.session_state.issue_labels]
    custom = [x.strip().lower() for x in st.session_state.custom_labels.split(",") if x.strip()]
    all_labels = selected + custom

    if all_labels and not any(label in labels for label in all_labels):
        return False

    if st.session_state.assignee_filter == "Only unassigned" and issue.get("assignee"):
        return False

    if st.session_state.assignee_filter == "Assigned only" and not issue.get("assignee"):
        return False

    if issue.get("comments", 0) > st.session_state.max_comments:
        return False

    keyword = st.session_state.issue_keywords.lower().strip()
    if keyword:
        text = f"{issue.get('title', '')} {issue.get('body', '')}".lower()
        if keyword not in text and not any(keyword in label for label in labels):
            return False

    return True


def find_and_rank_issues():
    repo = st.session_state.active_repo
    if not repo:
        st.warning("Select a repo first.")
        return

    full_name = extract_repo_full_name(repo.get("repo_url") or repo.get("url"))

    with st.spinner("Analyzing issues with AI..."):
        raw_issues = fetch_open_issues(full_name)
        final = []

        for issue in raw_issues:
            if not issue_matches(issue):
                continue

            try:
                ai = analyze_issue(issue, st.session_state.skill_level)
                issue.update(ai)
            except Exception:
                issue["summary"] = issue.get("body", "")[:180] or "No summary available."
                issue["difficulty"] = "Intermediate"
                issue["competition"] = min(10, issue.get("comments", 0) + 1)
                issue["skill_match"] = 7
                issue["what_to_do"] = "Review the issue and inspect the related files."
                issue["why_good_match"] = "This looks suitable based on labels and low activity."
                issue["files_likely_needed"] = "Not clear from issue."
                issue["estimated_time"] = "Not sure"

            issue["repo_name"] = repo.get("name")
            final.append(issue)

        st.session_state.ranked_issues = rank_issues(final, {"skill_level": st.session_state.skill_level})


def render_issue_filters():
    st.markdown('<div class="detail-card">', unsafe_allow_html=True)
    st.markdown("### Filter Issues")

    st.multiselect(
        "Popular labels",
        ["good first issue", "help wanted", "bug", "documentation", "enhancement"],
        key="issue_labels",
    )

    st.text_input("Custom labels", key="custom_labels", placeholder="frontend, backend, auth...")
    st.selectbox("Assignee", ["Only unassigned", "Any", "Assigned only"], key="assignee_filter")
    st.number_input("Max comments", min_value=0, max_value=50, value=5, key="max_comments")
    st.text_input("Keyword", key="issue_keywords", placeholder="api, docs, login...")

    if st.button("Find Best Issues"):
        find_and_rank_issues()

    st.markdown("</div>", unsafe_allow_html=True)


def contribution_comment(issue):
    title = issue.get("title", "this issue")
    first_step = issue.get("first_step") or "I’ll first review the related files and understand the expected change."

    return f"""Hi! I’d like to work on this issue.

I have reviewed the issue: "{title}".

My first step will be: {first_step}

Please assign this to me if it is still available. Thank you!"""

def render_issue_card(issue):
    scout_score = issue.get("scout_score", 0)

    score_color = "#22c55e"

    if scout_score < 80:
        score_color = "#f59e0b"

    if scout_score < 50:
        score_color = "#ef4444"

    st.markdown(
        f"""
        <div class="issue-modern">

            <div class="issue-header">

                <div class="issue-main">
                    <div class="issue-title">
                        <a href="{issue.get("url")}" target="_blank">
                            {issue.get("title")}
                        </a>
                    </div>

                    <div class="issue-summary">
                        {issue.get("summary", "")}
                    </div>

                    <div class="issue-chips">
                        <span>{issue.get("difficulty")}</span>
                        <span>{issue.get("competition_level")}</span>
                        <span>{issue.get("comments", 0)} comments</span>
                        <span>{issue.get("skill_match", 0)}/10 skill fit</span>
                    </div>
                </div>

                <div class="score-ring" style="border-color:{score_color}">
                    {scout_score}
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### AI Breakdown")

    st.markdown(
        f"""
- **What you'll do:** {issue.get("what_to_do", "")}

- **Why it matches:** {issue.get("why_good_match", "")}

- **Likely files:** {issue.get("files_likely_needed", "")}

- **Estimated time:** {issue.get("estimated_time", "")}

- **First step:** {issue.get("first_step", "")}
"""
    )

    st.code(
        contribution_comment(issue),
        language="markdown"
    )



def render_issues():
    repo = st.session_state.active_repo

    if not repo:
        st.markdown('<div class="empty-box">Choose a repository from your shortlist first.</div>', unsafe_allow_html=True)
        return

    st.markdown(f"## Issue Explorer")
    st.caption(f"Analyzing: {repo.get('name')}")

    left, right = st.columns([2.2, 1], gap="large")

    with right:
        render_issue_filters()

    with left:
        if not st.session_state.ranked_issues:
            st.markdown(
                '<div class="empty-box">Set filters and click <b>Find Best Issues</b>.</div>',
                unsafe_allow_html=True,
            )
            return

        for issue in st.session_state.ranked_issues:
            render_issue_card(issue)


def render_saved():
    st.markdown("## Saved Issues")
    st.markdown('<div class="empty-box">Saved issue workflow can be added next.</div>', unsafe_allow_html=True)


def create_app():
    configure_page()
    init_session()
    render_sidebar()
    render_top_nav()

    page = st.session_state.page

    if page == "discover":
        render_discover()
    elif page == "shortlist":
        render_shortlist()
    elif page == "issues":
        render_issues()
    elif page == "saved":
        render_saved()
    else:
        render_discover()
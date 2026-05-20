# # import streamlit as st

# # from src.ai_agent import GeminiAPIError, summarize_repository
# # from src.github_client import (
# #     GitHubClientError,
# #     get_gssoc_filter_options,
# #     get_repository_readme,
# #     search_gssoc_projects,
# #     fetch_gssoc_projects,
# # )


# # def configure_page():
# #     st.set_page_config(
# #         page_title="GitScout AI",
# #         page_icon="🧭",
# #         layout="wide",
# #     )
# #     st.markdown(
# #         """
# #         <style>
# #             .css-1d391kg {background-color: #0d1117;}
# #             .css-1g3m7r5 {color: #c9d1d9;}
# #             .stButton>button {background-color: #238636; color: white;}
# #             .stTextInput>div>div>input {background: #161b22; color: #c9d1d9;}
# #             .stSelectbox>div>div>div>span {color: #c9d1d9;}
# #         </style>
# #         """,
# #         unsafe_allow_html=True,
# #     )


# # def init_session_state():
# #     defaults = {
# #         "keywords": "",
# #         "tech_stack": "",
# #         "category": "",
# #         "beginner_friendly": False,
# #         "sort_by": "most_open_issues",
# #         "skill_level": "Beginner",
# #         "filter_options": {},
# #         "repo_results": [],
# #         "selected_repos": [],
# #         "ranked_issues": [],
# #         "language": "",
# #         "difficulty": ""
# #     }
# #     for key, value in defaults.items():
# #         if key not in st.session_state:
# #             st.session_state[key] = value


# # def render_sidebar():
# #     with st.sidebar:
# #         st.title("GitScout AI")
# #         st.write("Discover GSSoC projects and rank starter issues.")
# #         st.markdown("---")

# #         st.text_input(
# #             "Search",
# #             key="keywords",
# #             placeholder="Search projects, tech stack, admin...",
# #         )

# #         options = st.session_state.get("filter_options", {})
# #         tech_options = options.get("tech_stack", [])
# #         language_options = options.get("language", [])
# #         difficulty_options = options.get("difficulty", [])

# #         if tech_options:
# #             st.selectbox(
# #                 "Tech Stack",
# #                 [""] + tech_options,
# #                 key="tech_stack",
# #             )
# #         else:
# #             st.selectbox("Tech Stack", ["Loading..."], disabled=True)

# #         if language_options:
# #             st.selectbox(
# #                 "Language",
# #                 [""] + language_options,
# #                 key="language",
# #             )
# #         else:
# #             st.selectbox("Language", ["Loading..."], disabled=True)

# #         if difficulty_options:
# #             st.selectbox(
# #                 "Difficulty",
# #                 [""] + difficulty_options,
# #                 key="difficulty",
# #             )
# #         else:
# #             st.selectbox("Difficulty", ["Loading..."], disabled=True)

# #         st.selectbox(
# #             "Sort by",
# #             [
# #                 ("Most Open Issues", "most_open_issues"),
# #                 ("Most Good First Issues", "most_good_first"),
# #                 ("Beginner Friendly First", "beginner_friendly"),
# #                 ("Name A-Z", "name_asc"),
# #             ],
# #             key="sort_by",
# #             format_func=lambda x: x[0] if isinstance(x, tuple) else x,
# #             index=0,
# #         )

# #         st.markdown("---")
# #         st.subheader("Your level")
# #         st.selectbox(
# #             "Skill level",
# #             ["Beginner", "Intermediate", "Advanced"],
# #             key="skill_level",
# #         )
# #         st.markdown("---")
# #         return st.button("Search GSSoC projects", type="primary")


# # def _init_filter_options():
# #     """Load available filter options from GSSoC projects on first load."""
# #     if st.session_state.get("filter_options"):
# #         return
# #     try:
# #         with st.spinner("Loading GSSoC projects..."):
# #             projects = fetch_gssoc_projects()
# #             st.session_state.filter_options = get_gssoc_filter_options(projects)
# #     except GitHubClientError as exc:
# #         st.error(f"Failed to load projects: {exc}")
# #         st.session_state.filter_options = {}


# # def _search_and_prepare_repositories():
# #     try:
# #         with st.spinner("Searching GSSoC projects and summarizing..."):
# #             projects = search_gssoc_projects(
# #                 keywords=st.session_state.keywords,
# #                 tech_stack=st.session_state.tech_stack,
# #                 beginner_friendly=st.session_state.beginner_friendly,
# #                 category=st.session_state.category,
# #                 sort_by=st.session_state.sort_by,
# #             )
# #             final_repos = []
# #             for repo in projects:
# #                 try:
# #                     repo_readme = get_repository_readme(repo["name"]) if repo.get("name") and "/" in repo["name"] else ""
# #                 except (GitHubClientError, ValueError):
# #                     repo_readme = ""
# #                 repo["readme"] = repo_readme

# #                 try:
# #                     summary_response = summarize_repository(repo)
# #                     repo["summary"] = summary_response.get("summary", "No summary available.")
# #                 except GeminiAPIError as exc:
# #                     repo["summary"] = "AI summary unavailable."
# #                     st.warning(f"Gemini summary failed for {repo['name']}: {exc}")

# #                 final_repos.append(repo)

# #             st.session_state.repo_results = final_repos
# #     except (GitHubClientError, GeminiAPIError) as exc:
# #         st.error(str(exc))
# #     except Exception as exc:
# #         st.error(f"Search failed: {exc}")


# # def render_repo_card(repo):
# #     with st.container():
# #         cols = st.columns([4, 1])
# #         with cols[0]:
# #             st.markdown(f"### [{repo['name']}]({repo['url']})")
# #             tech_display = " · ".join(repo.get("tech_stack", [repo.get("language", "Unknown")])[:3])
# #             good_first = repo.get("good_first_issues", 0)
# #             open_issues = repo.get("open_issues_count", 0)
# #             st.caption(f"{tech_display} · 📋 {open_issues} issues · 🎯 {good_first} good first issues")
# #             st.write(repo.get("summary", repo.get("description", "No summary available.")))
# #         with cols[1]:
# #             button_key = f"select_{repo['name'].replace('/', '_')}"
# #             if st.button("Select", key=button_key):
# #                 select_repo(repo)


# # def render_issue_card(issue):
# #     with st.container():
# #         header_cols = st.columns([4, 1])
# #         with header_cols[0]:
# #             st.markdown(f"### [{issue['title']}]({issue['url']})")
# #             st.write(issue.get("summary", "No summary provided."))
# #         with header_cols[1]:
# #             st.markdown(f"**{issue.get('freshness', 'New')}**")

# #         stats_cols = st.columns([1, 1, 1, 1])
# #         stats_cols[0].metric("Difficulty", issue.get("difficulty", "N/A"))
# #         stats_cols[1].metric("Competition", issue.get("competition", "N/A"))
# #         stats_cols[2].metric("Skill fit", issue.get("skill_match", "N/A"))
# #         stats_cols[3].metric("Comments", issue.get("comments", 0))


# # def select_repo(repo):
# #     current = st.session_state.selected_repos
# #     if repo not in current:
# #         st.session_state.selected_repos = current + [repo]


# # def render_repo_results():
# #     with st.container():
# #         st.subheader("Repository search results")
# #         if not st.session_state.repo_results:
# #             st.info("Search for repositories to see AI-generated summaries.")
# #             return
# #         for repo in st.session_state.repo_results:
# #             st.markdown("---")
# #             render_repo_card(repo)


# # def render_selected_repos():
# #     with st.container():
# #         st.subheader("Selected repositories")
# #         if not st.session_state.selected_repos:
# #             st.info("Select repositories to fetch ranked issues.")
# #             return
# #         for repo in st.session_state.selected_repos:
# #             st.markdown(f"- [{repo['name']}]({repo['url']})")


# # def render_ranked_issues():
# #     with st.container():
# #         st.subheader("Ranked issues")
# #         if not st.session_state.ranked_issues:
# #             st.info("Issue cards will appear after repository selection.")
# #             return
# #         for issue in st.session_state.ranked_issues:
# #             st.markdown("---")
# #             render_issue_card(issue)


# # def create_app():
# #     configure_page()
# #     init_session_state()
# #     _init_filter_options()

# #     search_clicked = render_sidebar()

# #     if search_clicked:
# #         st.session_state.repo_results = []
# #         st.session_state.selected_repos = []
# #         st.session_state.ranked_issues = []
# #         _search_and_prepare_repositories()

# #     st.title("GitScout AI")
# #     st.write("Discover GSSoC projects and rank starter issues with AI assistance.")

# #     results_col, detail_col = st.columns([3, 1])
# #     with results_col:
# #         render_repo_results()
# #     with detail_col:
# #         render_selected_repos()
# #         st.markdown("---")
# #         render_ranked_issues()









# import re
# import streamlit as st

# from src.ai_agent import (
#     GeminiAPIError,
#     analyze_issue,
#     summarize_repository,
# )

# from src.github_client import (
#     GitHubClientError,
#     fetch_open_issues,
#     get_gssoc_filter_options,
#     get_repository_metadata,
#     get_repository_readme,
#     search_gssoc_projects,
# )

# from src.issue_ranker import rank_issues


# def configure_page():
#     st.set_page_config(
#         page_title="GitScout AI",
#         page_icon="🚀",
#         layout="wide",
#     )

#     st.markdown(
#         """
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

# html, body, [class*="css"] {
#     font-family: 'Inter', sans-serif;
# }

# .stApp {
#     background: #0B1020;
#     color: #F9FAFB;
# }

# section[data-testid="stSidebar"] {
#     background: #111827;
#     border-right: 1px solid rgba(255,255,255,0.06);
# }

# .block-container {
#     padding-top: 2rem;
# }

# .main-title {
#     font-size: 3rem;
#     font-weight: 700;
#     background: linear-gradient(90deg,#8B5CF6,#22C55E);
#     -webkit-background-clip: text;
#     -webkit-text-fill-color: transparent;
#     margin-bottom: 0.2rem;
# }

# .subtitle {
#     color: #9CA3AF;
#     font-size: 1.05rem;
#     margin-bottom: 2rem;
# }

# .repo-card {
#     background: #111827;
#     padding: 1.4rem;
#     border-radius: 20px;
#     border: 1px solid rgba(255,255,255,0.06);
#     margin-bottom: 1rem;
# }

# .issue-card {
#     background: #121A2B;
#     padding: 1.2rem;
#     border-radius: 18px;
#     border: 1px solid rgba(255,255,255,0.06);
#     margin-bottom: 1rem;
# }

# .small-muted {
#     color: #9CA3AF;
#     font-size: 0.9rem;
# }

# .rank-badge {
#     background: linear-gradient(90deg,#8B5CF6,#22C55E);
#     padding: 0.35rem 0.8rem;
#     border-radius: 999px;
#     font-weight: 600;
#     display: inline-block;
# }

# .stButton>button {
#     width: 100%;
#     border-radius: 12px;
#     background: linear-gradient(90deg,#8B5CF6,#22C55E);
#     border: none;
#     color: white;
#     font-weight: 600;
# }

# .stTextInput input,
# .stSelectbox div[data-baseweb="select"],
# .stMultiSelect div[data-baseweb="select"] {
#     background: #111827 !important;
#     border-radius: 12px !important;
# }

# </style>
# """,
#         unsafe_allow_html=True,
#     )


# def init_session_state():
#     defaults = {
#         "keywords": "",
#         "tech_stack": "",
#         "language": "",
#         "difficulty": "",
#         "sort_by": "Most Open Issues",
#         "skill_level": "Beginner",
#         "repo_results": [],
#         "selected_repos": [],
#         "ranked_issues": [],
#         "issue_keywords": "",
#         "custom_labels": "",
#         "issue_labels": [
#             "good first issue",
#             "help wanted",
#         ],
#         "assignee_filter": "Only unassigned",
#         "max_comments": 5,
#     }

#     for key, value in defaults.items():
#         if key not in st.session_state:
#             st.session_state[key] = value


# def _get_repo_full_name(repo):
#     value = (
#         repo.get("repo_url")
#         or repo.get("url")
#         or repo.get("name", "")
#     )

#     match = re.search(
#         r"github\.com/([^/]+/[^/#?]+)",
#         value,
#     )

#     if match:
#         return match.group(1).replace(".git", "")

#     if "/" in value:
#         return value

#     return ""


# def _is_selected(repo):
#     repo_name = _get_repo_full_name(repo)

#     return any(
#         _get_repo_full_name(r) == repo_name
#         for r in st.session_state.selected_repos
#     )


# def render_sidebar():
#     with st.sidebar:
#         st.markdown("## 🚀 GitScout AI")
#         st.caption("AI-powered open source discovery")

#         st.markdown("---")

#         filters = get_gssoc_filter_options()

#         st.text_input(
#             "Search",
#             key="keywords",
#             placeholder="AI, data science, frontend...",
#         )

#         st.selectbox(
#             "Tech Stack",
#             [""] + filters["tech_stacks"],
#             key="tech_stack",
#         )

#         st.selectbox(
#             "Language",
#             [""] + filters["languages"],
#             key="language",
#         )

#         st.selectbox(
#             "Difficulty",
#             [""] + filters["difficulties"],
#             key="difficulty",
#         )

#         st.selectbox(
#             "Sort by",
#             [
#                 "Most Open Issues",
#                 "Most Good First Issues",
#                 "Beginner Friendly First",
#                 "Name A-Z",
#             ],
#             key="sort_by",
#         )

#         st.markdown("---")

#         st.markdown("### 👤 Your Level")

#         st.selectbox(
#             "Skill level",
#             ["Beginner", "Intermediate", "Advanced"],
#             key="skill_level",
#         )

#         st.markdown("---")

#         return st.button("Search Projects")


# def _search_projects():
#     try:
#         with st.spinner("Finding projects..."):

#             projects = search_gssoc_projects(
#                 keywords=st.session_state.keywords,
#                 tech_stack=st.session_state.tech_stack,
#                 language=st.session_state.language,
#                 difficulty=st.session_state.difficulty,
#                 sort_by=st.session_state.sort_by,
#             )

#             final_projects = []

#             for repo in projects[:12]:

#                 try:
#                     full_name = _get_repo_full_name(repo)

#                     metadata = get_repository_metadata(
#                         full_name
#                     )

#                     repo["open_issues"] = metadata.get(
#                         "open_issues_count",
#                         0,
#                     )

#                     repo["stars"] = metadata.get(
#                         "stars",
#                         0,
#                     )

#                     readme = get_repository_readme(
#                         full_name
#                     )

#                     repo["readme"] = readme

#                     try:
#                         summary = summarize_repository(repo)
#                         repo["summary"] = summary["summary"]

#                     except:
#                         repo["summary"] = repo.get(
#                             "description",
#                             "No summary available.",
#                         )

#                 except:
#                     pass

#                 final_projects.append(repo)

#             st.session_state.repo_results = final_projects

#     except Exception as exc:
#         st.error(str(exc))


# def select_repo(repo):
#     if not _is_selected(repo):
#         st.session_state.selected_repos.append(repo)


# def render_repo_card(repo):
#     selected = _is_selected(repo)

#     with st.container():
#         st.markdown('<div class="repo-card">', unsafe_allow_html=True)

#         col1, col2 = st.columns([5, 1])

#         with col1:
#             st.markdown(
#                 f"### [{repo['name']}]({repo['url']})"
#             )

#             tech = " · ".join(
#                 repo.get("tech_stack", [])[:3]
#             )

#             st.markdown(
#                 f"<div class='small-muted'>⭐ {repo.get('stars',0)} · 📋 {repo.get('open_issues',0)} open issues · {tech}</div>",
#                 unsafe_allow_html=True,
#             )

#             st.write(
#                 repo.get(
#                     "summary",
#                     repo.get("description", ""),
#                 )
#             )

#         with col2:
#             if selected:
#                 st.success("Selected ✅")
#             else:
#                 if st.button(
#                     "Select",
#                     key=f"repo_{repo['name']}",
#                 ):
#                     select_repo(repo)
#                     st.rerun()

#         st.markdown("</div>", unsafe_allow_html=True)


# def _issue_matches(issue):
#     labels = [
#         label.lower()
#         for label in issue.get("labels", [])
#     ]

#     selected_labels = [
#         label.lower()
#         for label in st.session_state.issue_labels
#     ]

#     custom = [
#         x.strip().lower()
#         for x in st.session_state.custom_labels.split(",")
#         if x.strip()
#     ]

#     all_labels = selected_labels + custom

#     if all_labels:
#         if not any(label in labels for label in all_labels):
#             return False

#     if (
#         st.session_state.assignee_filter
#         == "Only unassigned"
#         and issue.get("assignee")
#     ):
#         return False

#     if (
#         st.session_state.assignee_filter
#         == "Assigned only"
#         and not issue.get("assignee")
#     ):
#         return False

#     if (
#         issue.get("comments", 0)
#         > st.session_state.max_comments
#     ):
#         return False

#     keyword = (
#         st.session_state.issue_keywords
#         .strip()
#         .lower()
#     )

#     if keyword:
#         combined = (
#             issue.get("title", "")
#             + " "
#             + issue.get("body", "")
#         ).lower()

#         if keyword not in combined:
#             return False

#     return True


# def _find_and_rank_issues():
#     try:
#         all_issues = []

#         with st.spinner("Ranking issues with AI..."):

#             for repo in st.session_state.selected_repos:

#                 full_name = _get_repo_full_name(repo)

#                 issues = fetch_open_issues(full_name)

#                 for issue in issues:

#                     if not _issue_matches(issue):
#                         continue

#                     try:
#                         ai = analyze_issue(
#                             issue,
#                             st.session_state.skill_level,
#                         )

#                         issue.update(ai)

#                     except:
#                         issue["difficulty"] = "Intermediate"
#                         issue["competition"] = min(
#                             issue.get("comments", 0),
#                             10,
#                         )
#                         issue["skill_match"] = 7
#                         issue["summary"] = issue.get(
#                             "body",
#                             "",
#                         )[:160]

#                     issue["repo_name"] = full_name

#                     all_issues.append(issue)

#             ranked = rank_issues(
#                 all_issues,
#                 {
#                     "skill_level":
#                     st.session_state.skill_level
#                 },
#             )

#             st.session_state.ranked_issues = ranked

#     except Exception as exc:
#         st.error(f"Ranking failed: {exc}")


# def render_selected_repos():
#     st.markdown("## Selected Repositories")

#     if not st.session_state.selected_repos:
#         st.info("Select repositories to continue.")
#         return

#     for repo in st.session_state.selected_repos:
#         st.markdown(
#             f"- [{repo['name']}]({repo['url']})"
#         )

#     st.markdown("---")

#     st.markdown("### 🎯 Issue Filters")

#     st.multiselect(
#         "Popular Labels",
#         [
#             "good first issue",
#             "help wanted",
#             "bug",
#             "documentation",
#             "enhancement",
#         ],
#         key="issue_labels",
#     )

#     st.text_input(
#         "Custom Labels",
#         key="custom_labels",
#         placeholder="frontend, backend, ml, api...",
#     )

#     st.selectbox(
#         "Assignee Filter",
#         [
#             "Only unassigned",
#             "Any",
#             "Assigned only",
#         ],
#         key="assignee_filter",
#     )

#     st.number_input(
#         "Maximum Comments",
#         min_value=0,
#         max_value=50,
#         value=5,
#         key="max_comments",
#     )

#     st.text_input(
#         "Issue Keyword Search",
#         key="issue_keywords",
#         placeholder="auth, docs, bug...",
#     )

#     if st.button(
#         "Find & Rank Issues",
#         type="primary",
#     ):
#         _find_and_rank_issues()


# def render_ranked_issues():
#     st.markdown("## 🔥 Ranked Issues")

#     if not st.session_state.ranked_issues:
#         st.info("Issues will appear here.")
#         return

#     for issue in st.session_state.ranked_issues:

#         st.markdown(
#             '<div class="issue-card">',
#             unsafe_allow_html=True,
#         )

#         st.markdown(
#             f"### [{issue['title']}]({issue['url']})"
#         )

#         st.markdown(
#             f"<div class='small-muted'>{issue.get('repo_name')}</div>",
#             unsafe_allow_html=True,
#         )

#         st.write(issue.get("summary", ""))

#         c1, c2, c3, c4 = st.columns(4)

#         c1.metric(
#             "Difficulty",
#             issue.get("difficulty", "N/A"),
#         )

#         c2.metric(
#             "Competition",
#             issue.get(
#                 "competition_level",
#                 "Unknown",
#             ),
#         )

#         c3.metric(
#             "Comments",
#             issue.get("comments", 0),
#         )

#         c4.metric(
#             "Skill Match",
#             issue.get("skill_match", 0),
#         )

#         st.markdown(
#             f"<div class='rank-badge'>Rank Score: {issue.get('rank_score')}</div>",
#             unsafe_allow_html=True,
#         )

#         st.markdown(
#             "</div>",
#             unsafe_allow_html=True,
#         )


# def create_app():
#     configure_page()

#     init_session_state()

#     clicked = render_sidebar()

#     if clicked:
#         _search_projects()

#     st.markdown(
#         "<div class='main-title'>GitScout AI</div>",
#         unsafe_allow_html=True,
#     )

#     st.markdown(
#         "<div class='subtitle'>Find the best open-source issues before everyone else.</div>",
#         unsafe_allow_html=True,
#     )

#     col1, col2 = st.columns([2.3, 1])

#     with col1:
#         st.markdown("## 📦 Projects")

#         for repo in st.session_state.repo_results:
#             render_repo_card(repo)

#     with col2:
#         render_selected_repos()
#         st.markdown("---")
#         render_ranked_issues()





import re
import streamlit as st

from src.ai_agent import (
    analyze_issue,
    summarize_repository,
)

from src.github_client import (
    fetch_open_issues,
    get_gssoc_filter_options,
    get_repository_metadata,
    get_repository_readme,
    search_gssoc_projects,
    extract_repo_full_name,
)

from src.issue_ranker import rank_issues


# ---------------- PAGE CONFIG ---------------- #

def configure_page():
    st.set_page_config(
        page_title="GitScout AI",
        page_icon="🚀",
        layout="wide",
    )

    st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #F8FAFC;
    color: #0F172A;
}

section[data-testid="stSidebar"] {
    background: #0F172A;
    border-right: 1px solid #1E293B;
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

.main-title {
    font-size: 3rem;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 0.3rem;
}

.subtitle {
    color: #64748B;
    margin-bottom: 2rem;
}

.repo-card {
    background: white;
    border-radius: 22px;
    padding: 1.2rem;
    border: 1px solid #E2E8F0;
    box-shadow: 0px 4px 18px rgba(15,23,42,0.05);
    margin-bottom: 1rem;
    min-height: 300px;
}

.issue-card {
    background: white;
    border-radius: 22px;
    padding: 1.2rem;
    border: 1px solid #E2E8F0;
    box-shadow: 0px 4px 18px rgba(15,23,42,0.05);
    margin-bottom: 1rem;
}

.small-muted {
    color: #64748B;
    font-size: 0.92rem;
}

.tech-pill {
    display: inline-block;
    padding: 0.3rem 0.7rem;
    border-radius: 999px;
    background: #EEF2FF;
    color: #4338CA;
    font-size: 0.78rem;
    margin-right: 0.35rem;
    margin-top: 0.3rem;
    font-weight: 600;
}

.scout-score {
    background: linear-gradient(90deg,#7C3AED,#06B6D4);
    color: white;
    padding: 0.35rem 0.8rem;
    border-radius: 999px;
    display: inline-block;
    font-weight: 700;
}

.repo-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #0F172A;
    text-decoration: none;
}

.stButton>button {
    border-radius: 14px;
    border: none;
    background: linear-gradient(90deg,#7C3AED,#06B6D4);
    color: white;
    font-weight: 600;
    height: 2.8rem;
}

.stTextInput input,
.stSelectbox div[data-baseweb="select"],
.stMultiSelect div[data-baseweb="select"],
.stNumberInput input {
    border-radius: 14px !important;
    border: 1px solid #CBD5E1 !important;
}

</style>
""", unsafe_allow_html=True)


# ---------------- SESSION ---------------- #

def init_session():
    defaults = {
        "page": "discover",
        "repo_results": [],
        "selected_repos": [],
        "ranked_issues": [],
        "active_repo": None,

        "keywords": "",
        "tech_stack": "",
        "language": "",
        "difficulty": "",

        "sort_by": "Most Open Issues",
        "skill_level": "Beginner",

        "issue_keywords": "",
        "custom_labels": "",
        "issue_labels": [
            "good first issue",
            "help wanted",
        ],

        "assignee_filter": "Only unassigned",
        "max_comments": 5,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------- HELPERS ---------------- #

def is_selected(repo):
    full = extract_repo_full_name(
        repo.get("repo_url") or repo.get("url")
    )

    return any(
        extract_repo_full_name(
            r.get("repo_url") or r.get("url")
        ) == full
        for r in st.session_state.selected_repos
    )


def select_repo(repo):
    if not is_selected(repo):
        st.session_state.selected_repos.append(repo)


# ---------------- SIDEBAR ---------------- #

def render_sidebar():

    filters = get_gssoc_filter_options()

    with st.sidebar:

        st.markdown("## 🚀 GitScout AI")
        st.caption("AI-powered issue scouting")

        st.markdown("---")

        st.text_input(
            "Search",
            key="keywords",
            placeholder="AI, ML, backend..."
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
            "Sort by",
            [
                "Most Open Issues",
                "Most Good First Issues",
                "Beginner Friendly First",
                "Name A-Z",
            ],
            key="sort_by"
        )

        st.markdown("---")

        st.selectbox(
            "Your Skill Level",
            ["Beginner", "Intermediate", "Advanced"],
            key="skill_level"
        )

        st.markdown("---")

        if st.button("Search Projects"):
            search_projects()


# ---------------- SEARCH ---------------- #

def search_projects():

    with st.spinner("Finding projects..."):

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
                full_name = extract_repo_full_name(
                    repo.get("repo_url") or repo.get("url")
                )

                metadata = get_repository_metadata(full_name)

                repo["stars"] = metadata.get("stars", 0)
                repo["open_issues"] = metadata.get("open_issues_count", 0)

                if not repo.get("language"):
                    repo["language"] = metadata.get("language", "")

                readme = get_repository_readme(full_name)

                repo["readme"] = readme

                try:
                    summary = summarize_repository(repo)
                    repo["summary"] = summary["summary"]
                except:
                    repo["summary"] = repo.get("description", "")

            except:
                pass

            final.append(repo)

        st.session_state.repo_results = final


# ---------------- REPO GRID ---------------- #

def render_repo_grid():

    repos = st.session_state.repo_results

    if not repos:
        st.info("Search projects to begin.")
        return

    cols = st.columns(3)

    for index, repo in enumerate(repos):

        with cols[index % 3]:

            st.markdown('<div class="repo-card">', unsafe_allow_html=True)

            st.markdown(
                f'<a class="repo-title" href="{repo["url"]}" target="_blank">{repo["name"]}</a>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f"<div class='small-muted'>⭐ {repo.get('stars',0)} · 📋 {repo.get('open_issues',0)} issues</div>",
                unsafe_allow_html=True,
            )

            st.write(
                repo.get(
                    "summary",
                    repo.get("description", "")
                )
            )

            for tech in repo.get("tech_stack", [])[:4]:
                st.markdown(
                    f"<span class='tech-pill'>{tech}</span>",
                    unsafe_allow_html=True,
                )

            st.markdown("<br>", unsafe_allow_html=True)

            if is_selected(repo):
                st.success("Added to Shortlist ✅")
            else:
                if st.button(
                    "Add to Shortlist",
                    key=f"repo_{repo['name']}"
                ):
                    select_repo(repo)
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)


# ---------------- SHORTLIST ---------------- #

def render_shortlist_page():

    st.markdown("## 📌 Your Shortlisted Projects")

    repos = st.session_state.selected_repos

    if not repos:
        st.info("No repositories shortlisted yet.")
        return

    cols = st.columns(2)

    for idx, repo in enumerate(repos):

        with cols[idx % 2]:

            st.markdown('<div class="repo-card">', unsafe_allow_html=True)

            st.markdown(f"### {repo['name']}")

            st.write(repo.get("summary", ""))

            st.markdown(
                f"<div class='small-muted'>⭐ {repo.get('stars',0)} · 📋 {repo.get('open_issues',0)} issues</div>",
                unsafe_allow_html=True,
            )

            if st.button(
                "Analyze Issues",
                key=f"analyze_{repo['name']}"
            ):
                st.session_state.active_repo = repo
                st.session_state.page = "issues"
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)


# ---------------- ISSUE FILTERS ---------------- #

def render_issue_filters():

    st.markdown("### 🎯 Issue Filters")

    st.multiselect(
        "Popular Labels",
        [
            "good first issue",
            "help wanted",
            "bug",
            "documentation",
            "enhancement",
        ],
        key="issue_labels"
    )

    st.text_input(
        "Custom Labels",
        key="custom_labels",
        placeholder="frontend, backend, auth..."
    )

    st.selectbox(
        "Assignee Filter",
        [
            "Only unassigned",
            "Any",
            "Assigned only",
        ],
        key="assignee_filter"
    )

    st.number_input(
        "Maximum Comments",
        min_value=0,
        max_value=50,
        value=5,
        key="max_comments"
    )

    st.text_input(
        "Keyword Search",
        key="issue_keywords",
        placeholder="api, docs, login..."
    )

    if st.button("Find Best Issues"):
        find_and_rank_issues()


# ---------------- ISSUE MATCHING ---------------- #

def issue_matches(issue):

    labels = [
        label.lower()
        for label in issue.get("labels", [])
    ]

    custom = [
        x.strip().lower()
        for x in st.session_state.custom_labels.split(",")
        if x.strip()
    ]

    selected = [
        x.lower()
        for x in st.session_state.issue_labels
    ]

    all_labels = custom + selected

    if all_labels:
        if not any(label in labels for label in all_labels):
            return False

    if (
        st.session_state.assignee_filter
        == "Only unassigned"
        and issue.get("assignee")
    ):
        return False

    if (
        st.session_state.assignee_filter
        == "Assigned only"
        and not issue.get("assignee")
    ):
        return False

    if issue.get("comments", 0) > st.session_state.max_comments:
        return False

    keyword = st.session_state.issue_keywords.lower().strip()

    if keyword:

        text = (
            issue.get("title", "")
            + " "
            + issue.get("body", "")
        ).lower()

        if keyword not in text:
            return False

    return True


# ---------------- FIND ISSUES ---------------- #

def find_and_rank_issues():

    repo = st.session_state.active_repo

    full_name = extract_repo_full_name(
        repo.get("repo_url") or repo.get("url")
    )

    with st.spinner("Analyzing issues with AI..."):

        raw_issues = fetch_open_issues(full_name)

        final = []

        for issue in raw_issues:

            if not issue_matches(issue):
                continue

            try:
                ai = analyze_issue(
                    issue,
                    st.session_state.skill_level,
                )

                issue.update(ai)

            except:
                pass

            issue["repo_name"] = repo["name"]

            final.append(issue)

        ranked = rank_issues(
            final,
            {
                "skill_level":
                st.session_state.skill_level
            },
        )

        st.session_state.ranked_issues = ranked


# ---------------- ISSUE PAGE ---------------- #

def render_issue_page():

    repo = st.session_state.active_repo

    st.markdown(f"## 🔥 {repo['name']}")

    st.write(repo.get("summary", ""))

    render_issue_filters()

    st.markdown("---")

    issues = st.session_state.ranked_issues

    if not issues:
        st.info("No ranked issues yet.")
        return

    for issue in issues:

        st.markdown('<div class="issue-card">', unsafe_allow_html=True)

        st.markdown(
            f"### [{issue['title']}]({issue['url']})"
        )

        st.markdown(
            f"<span class='scout-score'>Scout Score: {issue.get('scout_score',0)}</span>",
            unsafe_allow_html=True,
        )

        st.markdown("<br><br>", unsafe_allow_html=True)

        st.write(issue.get("summary", ""))

        st.markdown("#### 🛠 What you'll likely do")
        st.write(issue.get("what_to_do", ""))

        st.markdown("#### 📂 Files likely involved")
        st.write(issue.get("files_likely_needed", ""))

        st.markdown("#### 🎯 Why this matches you")
        st.write(issue.get("why_good_match", ""))

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Difficulty",
            issue.get("difficulty", "N/A")
        )

        c2.metric(
            "Competition",
            issue.get("competition_level", "Unknown")
        )

        c3.metric(
            "Comments",
            issue.get("comments", 0)
        )

        c4.metric(
            "Skill Match",
            issue.get("skill_match", 0)
        )

        st.markdown(
            f"<div class='small-muted'>Estimated Time: {issue.get('estimated_time','Unknown')}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------- MAIN ---------------- #

def create_app():

    configure_page()

    init_session()

    render_sidebar()

    st.markdown(
        '<div class="main-title">GitScout AI</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">Find low-competition open-source opportunities before everyone else.</div>',
        unsafe_allow_html=True,
    )

    top1, top2 = st.columns([6, 1])

    with top1:
        pass

    with top2:

        if st.session_state.page != "discover":
            if st.button("← Back"):
                st.session_state.page = "discover"
                st.rerun()

    page = st.session_state.page

    if page == "discover":

        render_repo_grid()

        if st.session_state.selected_repos:
            st.markdown("---")

            if st.button("Continue to Shortlist →"):
                st.session_state.page = "shortlist"
                st.rerun()

    elif page == "shortlist":

        render_shortlist_page()

    elif page == "issues":

        render_issue_page()
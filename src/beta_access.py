import re
from typing import Any, Dict, Optional

import streamlit as st
from supabase import create_client, Client


MAX_FREE_AI_USES = 2


@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))


def get_beta_user(email: str) -> Optional[Dict[str, Any]]:
    email = normalize_email(email)
    if not email:
        return None

    supabase = get_supabase()
    result = (
        supabase.table("beta_users")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None


def create_or_get_beta_user(name: str, email: str) -> Dict[str, Any]:
    email = normalize_email(email)
    name = (name or "").strip()

    existing = get_beta_user(email)
    if existing:
        return existing

    supabase = get_supabase()
    result = (
        supabase.table("beta_users")
        .insert(
            {
                "name": name,
                "email": email,
                "ai_uses_used": 0,
                "ai_uses_limit": MAX_FREE_AI_USES,
            }
        )
        .execute()
    )

    return result.data[0]


def ai_uses_left(email: str) -> int:
    user = get_beta_user(email)
    if not user:
        return 0

    used = int(user.get("ai_uses_used", 0))
    limit = int(user.get("ai_uses_limit", MAX_FREE_AI_USES))
    return max(limit - used, 0)


def can_use_ai(email: str) -> bool:
    return ai_uses_left(email) > 0


def consume_ai_use(
    email: str,
    action: str,
    issue_url: Optional[str] = None,
    repo_name: Optional[str] = None,
) -> bool:
    """
    Returns True if use was consumed.
    Returns False if user has no AI uses left.
    """
    email = normalize_email(email)
    user = get_beta_user(email)

    if not user:
        return False

    used = int(user.get("ai_uses_used", 0))
    limit = int(user.get("ai_uses_limit", MAX_FREE_AI_USES))

    if used >= limit:
        return False

    supabase = get_supabase()

    supabase.table("beta_users").update(
        {"ai_uses_used": used + 1}
    ).eq("email", email).execute()

    supabase.table("ai_usage_events").insert(
        {
            "email": email,
            "action": action,
            "issue_url": issue_url,
            "repo_name": repo_name,
        }
    ).execute()

    return True


def save_feedback(
    email: str,
    rating: int,
    feedback: str,
    confusing_part: str,
    would_use_again: bool,
) -> None:
    supabase = get_supabase()
    supabase.table("beta_feedback").insert(
        {
            "email": normalize_email(email),
            "rating": rating,
            "feedback": feedback,
            "confusing_part": confusing_part,
            "would_use_again": would_use_again,
        }
    ).execute()


def render_beta_gate() -> bool:
    """
    Returns True if user is allowed into app.
    Returns False if user has not entered email yet.
    """
    if "beta_email" not in st.session_state:
        st.session_state.beta_email = ""

    if "beta_name" not in st.session_state:
        st.session_state.beta_name = ""

    if st.session_state.beta_email:
        return True

    st.title("GitScout AI Beta")
    st.write(
        "Find beginner-friendly open-source issues, understand what they mean, "
        "and generate a proper comment to ask for assignment."
    )

    st.info("Beta limit: 2 free AI generations per person.")

    name = st.text_input("Your name")
    email = st.text_input("Your email")

    if st.button("Start beta", type="primary"):
        email = normalize_email(email)

        if not is_valid_email(email):
            st.error("Enter a valid email.")
            return False

        user = create_or_get_beta_user(name=name, email=email)

        st.session_state.beta_email = user["email"]
        st.session_state.beta_name = user.get("name", "")
        st.rerun()

    return False


def render_usage_status() -> None:
    email = st.session_state.get("beta_email", "")
    if not email:
        return

    left = ai_uses_left(email)

    if left > 0:
        st.success(f"AI uses left: {left}/{MAX_FREE_AI_USES}")
    else:
        # Prominent feedback banner matching the sleek dark theme
        st.markdown(
            """
            <div style='background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); padding: 20px; border-radius: 12px; margin-bottom: 20px;'>
                <h3 style='margin: 0; color: #F59E0B; font-size: 1.1rem; font-weight: 700;'>⚠️ Beta limit reached</h3>
                <p style='margin: 6px 0 0 0; color: #E2E8F0; font-size: 0.95rem;'>You have used your 2 free AI generations. Please fill out the feedback form below to help us improve GitScout!</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Show feedback form immediately below the banner
        render_feedback_form()


def render_feedback_form() -> None:
    email = st.session_state.get("beta_email", "")

    if not email:
        return

    if ai_uses_left(email) > 0:
        return

    st.divider()
    st.subheader("Quick feedback")

    rating = st.slider("How useful was GitScout?", 1, 5, 3)
    confusing_part = st.text_area("What confused you?")
    feedback = st.text_area("What should I improve?")
    would_use_again = st.radio("Would you use this again?", [True, False], format_func=lambda x: "Yes" if x else "No")

    if st.button("Submit feedback", type="primary"):
        save_feedback(
            email=email,
            rating=rating,
            feedback=feedback,
            confusing_part=confusing_part,
            would_use_again=would_use_again,
        )
        st.success("Thank you! Feedback saved.")
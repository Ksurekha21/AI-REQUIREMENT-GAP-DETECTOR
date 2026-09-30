from typing import List, Dict, Any
import streamlit as st
from ai_analyzer import (
    analyze_requirement,
    AIAnalyzerError,
    MissingAPIKeyError,
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
    NetworkError
)

# ─── Display Helper Functions ─────────────────────────────────────────────────

def display_bullet_list(emoji_title: str, items: List[str], key: str, check_items: bool = False):
    """Render a result category in a consistently styled card."""
    with st.container(border=True, key=key):
        st.markdown(f"### {emoji_title}")
        if items:
            for item in items:
                prefix = "✓" if check_items else "•"
                st.markdown(f"{prefix} {item}")
        else:
            st.markdown("*None identified.*")


def display_ambiguity_section(ambiguities: List[Dict[str, str]]):
    """Render each ambiguity with its issue, explanation, and clarification."""
    with st.container(border=True, key="result-ambiguity"):
        st.markdown("### 🔍 Ambiguity Detection")
        if not ambiguities:
            st.markdown("No significant ambiguity detected.")
        else:
            for idx, item in enumerate(ambiguities, 1):
                st.markdown(f"**Ambiguity {idx}**")
                st.markdown(f"**Issue:** {item.get('issue', '')}")
                st.markdown(f"**Explanation:** {item.get('explanation', '')}")
                st.markdown(f"**Suggested Clarification:** {item.get('suggested_clarification', '')}")
                if idx < len(ambiguities):
                    st.divider()


def display_clarification_questions(questions: List[str]):
    """Render clarification questions as a numbered list."""
    with st.container(border=True, key="result-clarification-questions"):
        st.markdown("### ❓ Clarification Questions")
        if questions:
            for idx, question in enumerate(questions, 1):
                st.markdown(f"{idx}. {question}")
        else:
            st.markdown("*No clarification questions generated.*")


def display_improved_requirement(improved: str):
    """Give the suggested requirement a distinct, readable presentation."""
    with st.container(border=True, key="result-improved-requirement"):
        st.markdown("### ✨ AI-Suggested Improved Requirement")
        if improved:
            st.markdown(improved)
        else:
            st.markdown("*No improved requirement generated.*")

def render_results(analysis):
    """
    Renders all 9 analysis sections in the required display order.
    """
    data = analysis.to_dict()

    st.subheader("Analysis Results")

    # 1. High Priority Gaps
    display_bullet_list("🔴 High Priority Gaps", data["high_priority_gaps"], "result-high-priority")

    # 2. Medium Priority Gaps
    display_bullet_list("🟡 Medium Priority Gaps", data["medium_priority_gaps"], "result-medium-priority")

    # 3. Low Priority Gaps
    display_bullet_list("🟢 Low Priority Gaps", data["low_priority_gaps"], "result-low-priority")

    # 4. Missing Details
    display_bullet_list("⚠️ Missing Details", data["missing_details"], "result-missing-details")

    # 5. Ambiguity Detection
    display_ambiguity_section(data["ambiguity_detection"])

    # 6. Edge-Case Detection
    display_bullet_list("🧪 Edge-Case Detection", data["edge_cases"], "result-edge-cases")

    # 7. Clarification Questions
    display_clarification_questions(data["clarification_questions"])

    # 8. Improved Requirement
    display_improved_requirement(data["improved_requirement"])

    # 9. Recommendations
    display_bullet_list("💡 Recommendations", data["recommendations"], "result-recommendations", check_items=True)


# ─── Main Application ─────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="AI Requirement Gap Detector",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        """
        <style>
        :root {
            --page-bg: #f6f8fc;
            --ink: #1c2b44;
            --muted: #66758a;
            --line: #e5eaf1;
            --blue: #5576d1;
        }
        [data-testid="stAppViewContainer"] { background: var(--page-bg); color: var(--ink); }
        [data-testid="stHeader"] { background: rgba(246, 248, 252, 0.92); }
        .main .block-container { max-width: 940px; padding: 2.25rem 1.25rem 4rem; }
        h1, h2, h3 { color: var(--ink); }
        .hero-header { text-align: center; padding: 0.6rem 0 1.5rem; }
        .hero-header h1 { margin: 0; font-size: 2.15rem; font-weight: 700; }
        .hero-header p { color: var(--muted); font-size: 1.02rem; margin: 0.6rem 0 0; }
        .st-key-requirement-input,
        .st-key-result-high-priority,
        .st-key-result-medium-priority,
        .st-key-result-low-priority,
        .st-key-result-missing-details,
        .st-key-result-ambiguity,
        .st-key-result-edge-cases,
        .st-key-result-clarification-questions,
        .st-key-result-improved-requirement,
        .st-key-result-recommendations {
            background: #fff;
            border: 1px solid var(--line);
            border-radius: 12px;
            box-shadow: 0 3px 12px rgba(28, 43, 68, 0.045);
            padding: 1rem 1.2rem;
            margin-bottom: 0.9rem;
        }
        .st-key-result-high-priority { border-left: 4px solid #d96b78; }
        .st-key-result-medium-priority { border-left: 4px solid #d7a83d; }
        .st-key-result-low-priority { border-left: 4px solid #5d9b76; }
        .st-key-result-missing-details { border-left: 4px solid #9181c9; }
        .st-key-result-ambiguity { border-left: 4px solid #9b7bc7; }
        .st-key-result-edge-cases { border-left: 4px solid #d99055; }
        .st-key-result-clarification-questions { border-left: 4px solid #5c91ce; }
        .st-key-result-improved-requirement {
            border-left: 4px solid #4b9b86;
            background: #f5fbf8;
        }
        .st-key-result-recommendations { border-left: 4px solid #638bd0; }
        [data-testid="stAlertContentWarning"] {
            color: #704f00 !important;
            text-align: center;
        }
        [data-testid="stAlertContentWarning"] p { color: #704f00 !important; }
        [data-testid="stTextArea"] textarea {
            background: #fff;
            color: var(--ink);
            border: 1px solid #d9e0ea;
            border-radius: 9px;
            padding: 0.85rem 1rem;
            line-height: 1.55;
        }
        [data-testid="stTextArea"] textarea:focus { border-color: var(--blue); box-shadow: 0 0 0 1px var(--blue); }
        .stButton > button {
            min-height: 2.8rem;
            border-radius: 9px;
            border: 1px solid #5576d1;
            background: #5576d1;
            color: #fff;
            font-weight: 600;
            transition: background-color 120ms ease, border-color 120ms ease;
        }
        .stButton > button:hover { background: #4565bd; border-color: #4565bd; color: #fff; }
        [data-testid="stAlert"] {
            max-width: 560px;
            margin: 0 auto;
            border-radius: 9px;
        }
        @media (max-width: 640px) {
            .main .block-container { padding: 1.4rem 0.9rem 2.5rem; }
            .hero-header h1 { font-size: 1.75rem; }
            .hero-header p { font-size: 0.95rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="hero-header">
            <h1>AI Requirement Gap Detector</h1>
            <p>Identify potential gaps in software requirements before development begins.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Requirement Input
    with st.container(border=True, key="requirement-input"):
        st.markdown("### Enter Your Requirement")
        requirement_text = st.text_area(
            label="Requirement",
            placeholder="Example: Users should be able to order food through the application.",
            height=170,
            label_visibility="collapsed",
        )

    # Analyze Button
    button_left, button_center, button_right = st.columns([1, 2, 1])
    with button_center:
        analyze_clicked = st.button("Analyze Requirement", type="primary", use_container_width=True)

    if analyze_clicked:
        clean_input = requirement_text.strip()

        if not clean_input:
            st.warning("Enter any requirement to analyze.")
        else:
            with st.spinner("Analyzing your requirement..."):
                try:
                    st.caption("AI is identifying potential gaps, ambiguities, edge cases, and missing details.")
                    result = analyze_requirement(clean_input)
                    render_results(result)

                except MissingAPIKeyError as e:
                    st.error(f"Configuration Error: {e}")
                except AuthenticationError as e:
                    st.error(f"Authentication Error: {e}")
                except RateLimitError as e:
                    st.warning(f"Rate Limit: {e}")
                except ServiceUnavailableError as e:
                    st.warning(f"Service Notice: {e}")
                except NetworkError as e:
                    st.error(f"Connection Error: {e}")
                except AIAnalyzerError as e:
                    st.error(str(e))
                except Exception:
                    st.error("Unable to analyze the requirement at the moment. Please try again.")


if __name__ == "__main__":
    main()

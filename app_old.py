"""
Co-op Job Application Tracker & Matcher
Run with: streamlit run app.py
"""
import streamlit as st
from src import db, matcher

st.set_page_config(page_title="Co-op Job Matcher", layout="wide")
db.init_db()

st.title("Co-op Job Application Tracker & Matcher")

def score_emoji(score):
    if score is None:
        return "white_circle"
    elif score >= 70:
        return "green_circle"
    elif score >= 40:
        return "yellow_circle"
    else:
        return "red_circle"

EMOJI_MAP = {
    "green_circle": chr(0x1F7E2),
    "yellow_circle": chr(0x1F7E1),
    "red_circle": chr(0x1F534),
    "white_circle": chr(0x26AA),
}

# --- Sidebar stats ---
all_postings = db.get_all_postings()
with st.sidebar:
    st.header("Stats")
    st.metric("Total postings", len(all_postings))
    applied = sum(1 for p in all_postings if p["status"] != "Not Applied")
    st.metric("Applied", applied)
    scored = [p for p in all_postings if p["score"] is not None]
    if scored:
        avg = sum(p["score"] for p in scored) / len(scored)
        st.metric("Avg fit score", f"{avg:.1f}")

# --- Add posting form ---
with st.expander("Add a new posting", expanded=False):
    with st.form("add_posting_form", clear_on_submit=True):
        title = st.text_input("Job title")
        company = st.text_input("Company")
        description = st.text_area("Full posting text (paste it here)", height=200)
        deadline = st.text_input("Deadline (e.g. 2026-10-01)")
        link = st.text_input("Link to posting")
        submitted = st.form_submit_button("Save posting")
        if submitted:
            if title and company and description:
                db.add_posting(title, company, description, deadline, link)
                st.success("Saved " + title + " at " + company)
                st.rerun()
            else:
                st.error("Title, company, and description are required.")

# --- Score button ---
unscored = db.get_unscored_postings()
if unscored:
    st.info(f"{len(unscored)} posting(s) not yet scored.")
    if st.button("Score all unscored postings"):
        resume_text = matcher.load_resume_text()
        progress = st.progress(0)
        for i, posting in enumerate(unscored):
            result = matcher.score_posting(posting["description"], resume_text)
            db.save_score(
                posting["id"],
                result.get("score"),
                ", ".join(result.get("matching_skills", [])),
                ", ".join(result.get("gaps", [])),
                result.get("reasoning", ""),
            )
            progress.progress((i + 1) / len(unscored))
        st.success("Scoring complete!")
        st.rerun()

# --- Postings table ---
st.subheader("Postings")

col_filter, col_sort = st.columns(2)
with col_filter:
    status_filter = st.selectbox(
        "Filter by status", ["All", "Not Applied", "Applied", "Interview", "Rejected", "Offer"]
    )
with col_sort:
    sort_option = st.selectbox(
        "Sort by", ["Score (High to Low)", "Score (Low to High)", "Company (A-Z)", "Deadline"]
    )

postings = db.get_all_postings()
if status_filter != "All":
    postings = [p for p in postings if p["status"] == status_filter]

if sort_option == "Score (High to Low)":
    postings = sorted(postings, key=lambda p: (p["score"] is None, -(p["score"] or 0)))
elif sort_option == "Score (Low to High)":
    postings = sorted(postings, key=lambda p: (p["score"] is None, p["score"] or 0))
elif sort_option == "Company (A-Z)":
    postings = sorted(postings, key=lambda p: p["company"].lower())
elif sort_option == "Deadline":
    postings = sorted(postings, key=lambda p: p["deadline"] or "9999-99-99")

if not postings:
    st.write("No postings yet - add one above to get started.")

for p in postings:
    emoji_key = score_emoji(p["score"])
    dot = EMOJI_MAP[emoji_key]

    if p["score"] is not None:
        score_label = "Score: " + str(p["score"]) + "/100"
    else:
        score_label = "Not scored"

    header_text = dot + " " + p["title"] + " @ " + p["company"] + " - " + score_label

    with st.expander(header_text):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("**Deadline:** " + (p["deadline"] or "N/A"))
            if p["link"]:
                st.write("**Link:** " + p["link"])
            if p["score"] is not None:
                st.write("**Matching skills:** " + str(p["matching_skills"]))
                st.write("**Gaps:** " + str(p["gaps"]))
                st.write("**Reasoning:** " + str(p["reasoning"]))
            with st.expander("Full posting text"):
                st.write(p["description"])
        with col2:
            new_status = st.selectbox(
                "Status",
                ["Not Applied", "Applied", "Interview", "Rejected", "Offer"],
                index=["Not Applied", "Applied", "Interview", "Rejected", "Offer"].index(
                    p["status"]
                ),
                key="status_" + str(p["id"]),
            )
            if new_status != p["status"]:
                db.update_status(p["id"], new_status)
                st.rerun()

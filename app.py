"""Run with python -m streamlit run app.py."""
import csv
import io
import os
from urllib.parse import urlparse
import streamlit as st
from src import db, matcher
from src.workflow import deadline_days, score_batch
from src.demo_context import is_demo

st.set_page_config(page_title='Co-op Job Matcher', page_icon='🎯', layout='wide')
db.init_db()
st.title('Co-op Job Matcher')
st.caption('Find your strongest opportunities. Keep your applications moving.')
if is_demo():
    st.info('Interactive demo · Fictional sample data · Your changes stay in this browser session and may reset when you reload. Scoring is free, offline skill matching. Use sample text rather than personal information.')
    if st.sidebar.button('Reset demo'):
        st.session_state['_demo_session']['connection'].close()
        st.session_state.clear()
        st.rerun()
if 'notice' in st.session_state:
    st.success(st.session_state.pop('notice'))
if 'scoring_errors' in st.session_state:
    for error in st.session_state.pop('scoring_errors'):
        st.error(error)

all_postings = db.get_all_postings()
with st.sidebar:
    st.header('Your search')
    st.metric('Total postings', len(all_postings))
    st.metric('Applications started', sum(p['status'] != 'Not Applied' for p in all_postings))
    due = [p for p in all_postings if p['status'] == 'Not Applied' and (days := deadline_days(p['deadline'])) is not None and 0 <= days <= 7]
    st.metric('Due within 7 days', len(due))
    ai_scores = [p['score'] for p in all_postings if p['score'] is not None and p['score_source'] == 'claude']
    if ai_scores:
        st.metric('Average Claude fit', f'{sum(ai_scores)/len(ai_scores):.0f}/100')
    mode_label = st.selectbox('Scoring method', ['Offline skill overlap'] if is_demo() else ['Offline skill overlap', 'Claude AI'], index=1 if not is_demo() and os.getenv('ANTHROPIC_API_KEY') else 0)
    mode = 'claude' if mode_label == 'Claude AI' else 'offline'
    if mode == 'claude':
        st.caption('Sends your resume and selected postings to Anthropic. API charges apply.')
        if not os.getenv('ANTHROPIC_API_KEY'):
            st.warning('Add ANTHROPIC_API_KEY to .env, then restart.')
    else:
        st.caption('Free, local keyword matching. Scores measure mentions of your listed skills, not hiring likelihood.')

resume_text = None
try:
    resume_text = matcher.load_resume_text()
except (OSError, ValueError):
    st.warning('Add or repair your resume profile in the Resume tab before scoring.')
can_score = resume_text is not None and (mode == 'offline' or bool(os.getenv('ANTHROPIC_API_KEY')))
board, add, resume = st.tabs(['Opportunities', 'Add posting', 'Resume'])

with resume:
    st.subheader('Your resume profile')
    st.caption('Use a JSON object with a skills list. Add experience, projects, and education for better AI assessments.')
    with st.form('resume_form'):
        edited_resume = st.text_area('Resume JSON', value=resume_text or '{"skills": ["Python"], "experience": [], "projects": [], "education": ""}', height=380)
        if st.form_submit_button('Save resume'):
            try:
                matcher.save_resume_text(edited_resume)
                st.session_state.notice = 'Resume saved. Existing scores keep their original assessment; rescore them to use this profile.'
                st.rerun()
            except (ValueError, OSError) as error:
                st.error(f'Could not save resume: {error}')

with add:
    st.subheader('Add an opportunity')
    with st.form('add_posting_form'):
        title = st.text_input('Job title')
        company = st.text_input('Company')
        description = st.text_area('Full posting text', height=220)
        deadline = st.text_input('Deadline (YYYY-MM-DD, optional)')
        link = st.text_input('Link to posting (optional)')
        if st.form_submit_button('Save posting', type='primary'):
            try:
                db.add_posting(title, company, description, deadline, link)
                st.session_state.notice = f'Saved {title.strip()} at {company.strip()}.'
                st.rerun()
            except ValueError as error:
                st.error(str(error))


def run_scores(postings):
    progress = st.progress(0)
    successes, errors = score_batch(postings, resume_text, mode, progress.progress)
    st.session_state.notice = f'Saved {successes} score(s). {len(errors)} failed; previous results were preserved.'
    st.session_state.scoring_errors = errors
    st.rerun()


with board:
    if due:
        st.info(f"{len(due)} unapplied opportunity(s) close within 7 days: " + ', '.join(p['title'] for p in due))
    cols = st.columns([2, 1, 1])
    query = cols[0].text_input('Search title, company, or description')
    status_filter = cols[1].selectbox('Status filter', ['All'] + db.STATUSES)
    sort_option = cols[2].selectbox('Sort by', ['Score: high to low', 'Score: low to high', 'Deadline', 'Company', 'Newest'])
    due_only = st.checkbox('Only unapplied postings due within 7 days')
    postings = [p for p in all_postings if (status_filter == 'All' or p['status'] == status_filter) and query.casefold() in ' '.join([p['title'], p['company'], p['description']]).casefold()]
    if due_only:
        postings = [p for p in postings if p in due]
    if sort_option.startswith('Score'):
        direction = -1 if sort_option == 'Score: high to low' else 1
        postings.sort(key=lambda p: (p['score'] is None, direction * (p['score'] or 0)))
    elif sort_option == 'Deadline':
        postings.sort(key=lambda p: (deadline_days(p['deadline']) is None, deadline_days(p['deadline']) or 0))
    elif sort_option == 'Company':
        postings.sort(key=lambda p: p['company'].casefold())
    else:
        postings.sort(key=lambda p: p['id'], reverse=True)
    st.caption(f'{len(postings)} of {len(all_postings)} opportunities shown. Scores from different methods are not directly comparable.')
    pending = [p for p in postings if p['score'] is None]
    if pending:
        limit = st.number_input('Maximum postings to score this batch', min_value=1, max_value=len(pending), value=min(10, len(pending)), step=1)
        if st.button(f'Score unscored results ({min(limit, len(pending))})', disabled=not can_score, type='primary'):
            run_scores(pending[:limit])
    if postings:
        output = io.StringIO()
        fields = ['id', 'title', 'company', 'deadline', 'link', 'status', 'notes', 'score', 'score_source', 'matching_skills', 'gaps', 'reasoning']
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for p in postings:
            writer.writerow({k: ("'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v) for k, v in p.items()})
        st.download_button('Export shown postings (CSV)', output.getvalue(), 'coop-postings.csv', 'text/csv')
    else:
        st.info('No matching opportunities. Add a posting or adjust your filters.')
    for p in postings:
        pid = p['id']
        source = p['score_source'] or 'legacy / unknown'
        label = f"{p['score']}/100 · {source}" if p['score'] is not None else 'Not scored'
        with st.expander(f"{p['title']} @ {p['company']} — {label} — {p['status']}"):
            days = deadline_days(p['deadline'])
            if days is not None and p['status'] == 'Not Applied' and days < 0:
                st.warning(f'Deadline passed {abs(days)} day(s) ago.')
            elif days is not None and 0 <= days <= 7:
                st.warning('Due today.' if days == 0 else f'Due in {days} day(s).')
            else:
                st.write('Deadline: ' + (p['deadline'] or 'Not provided'))
            parsed = urlparse(p['link'] or '')
            if parsed.scheme in ('https', 'http') and parsed.netloc:
                st.link_button('Open posting', p['link'])
            if p['score'] is not None:
                st.write('**Matching skills:** ' + (p['matching_skills'] or 'None identified'))
                st.write('**Gaps:** ' + (p['gaps'] or 'None identified'))
                st.write(p['reasoning'] or '')
                st.caption('Assessed: ' + (p['scored_at'] or 'Unknown (existing score)'))
            if st.button('Rescore' if p['score'] is not None else 'Score this posting', key=f'score_{pid}', disabled=not can_score):
                run_scores([p])
            st.text(p['description'])
            with st.form(f'track_{pid}'):
                status = st.selectbox('Application status', db.STATUSES, index=db.STATUSES.index(p['status']) if p['status'] in db.STATUSES else 0, key=f'status_{pid}')
                notes = st.text_area('Notes', value=p['notes'] or '', key=f'notes_{pid}')
                if st.form_submit_button('Save tracking'):
                    db.update_status(pid, status, notes)
                    st.session_state.notice = 'Application tracking saved.'
                    st.rerun()
            with st.popover('Edit posting'):
                with st.form(f'edit_{pid}'):
                    new_title = st.text_input('Job title', p['title'], key=f'title_{pid}')
                    new_company = st.text_input('Company', p['company'], key=f'company_{pid}')
                    new_description = st.text_area('Posting text', p['description'], key=f'desc_{pid}')
                    new_deadline = st.text_input('Deadline', p['deadline'] or '', key=f'deadline_{pid}')
                    new_link = st.text_input('Link', p['link'] or '', key=f'link_{pid}')
                    st.caption('Changing title, company, or description clears the old score.')
                    if st.form_submit_button('Save edits'):
                        try:
                            db.update_posting(pid, new_title, new_company, new_description, new_deadline, new_link)
                            st.session_state.notice = 'Posting updated.'
                            st.rerun()
                        except ValueError as error:
                            st.error(str(error))
            with st.popover('Delete posting'):
                confirmed = st.checkbox('Permanently delete this posting and its notes', key=f'confirm_{pid}')
                if st.button('Delete permanently', key=f'delete_{pid}', disabled=not confirmed):
                    db.delete_posting(pid)
                    st.session_state.notice = 'Posting deleted.'
                    st.rerun()

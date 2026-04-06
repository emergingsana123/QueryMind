# Deployment: Push to GitHub. Go to share.streamlit.io.
# Connect repo. Set main file to app.py.
# Add secret: ANTHROPIC_API_KEY = "sk-ant-..."
# App will be live at your-app-name.streamlit.app

import streamlit as st
import anthropic
import os
import pandas as pd
from datetime import datetime
import time
import re
from dotenv import load_dotenv

load_dotenv()

# ── Module imports ────────────────────────────────────────────────────────────
from modules.session import (
    init_session, reset_session, check_rate_limit,
    increment_query_count, add_to_history, store_db, store_results,
)
from modules.csv_handler import process_upload, process_upload_df
from modules.nl_to_sql import get_sql
from modules.sql_executor import run_query, format_results, get_preview, extract_stats
from modules.summarizer import generate_summary
from modules.chatbot import get_chat_response, update_chat_history

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QueryMind",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
with open("styles/main.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Force theme variables (Fix 4) ─────────────────────────────────────────────
st.markdown("""
<style>
:root {
    --primary-color: #6366F1 !important;
    --background-color: #F8F7FF !important;
    --secondary-background-color: #FFFFFF !important;
    --text-color: #1E1B4B !important;
}
[data-testid="stAppViewContainer"] {
    background-color: #F8F7FF !important;
}
[data-testid="stVerticalBlock"] {
    background-color: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session ───────────────────────────────────────────────────────────────────
init_session()


# ── API key ───────────────────────────────────────────────────────────────────
def get_api_key():
    key = None
    try:
        key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    if not key:
        key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found. Add it to Streamlit secrets or "
            "set it as an environment variable in .env"
        )
    return key


# ── Header (Change 2) ─────────────────────────────────────────────────────────
def render_header():
    st.markdown("""
    <div class="qm-header">
        <div class="qm-header-left">
            <div class="qm-logo">QueryMind</div>
            <div class="qm-tagline">Ask anything. Get instant answers from your data.</div>
        </div>
        <div class="qm-header-badge">✦ AI POWERED</div>
    </div>
    """, unsafe_allow_html=True)


# ── Empty state (Change 3) ────────────────────────────────────────────────────
def render_empty_state():
    st.markdown("""
    <div class="empty-state">
        <div class="empty-title">Your data. Your questions. Instant answers.</div>
        <div class="empty-sub">Upload a CSV file in the sidebar or use the sample dataset to get started.</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-card-icon">💬</span>
            <div class="feature-card-title">Natural Language Queries</div>
            <div class="feature-card-desc">Type questions in plain English. No SQL knowledge needed whatsoever.</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-card-icon">⚡</span>
            <div class="feature-card-title">Live Pipeline View</div>
            <div class="feature-card-desc">Watch your question transform into SQL in real time, step by step.</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="feature-card">
            <span class="feature-card-icon">🧠</span>
            <div class="feature-card-title">AI-Powered Analysis</div>
            <div class="feature-card-desc">Get a sharp plain English insight alongside every query result.</div>
        </div>
        """, unsafe_allow_html=True)


# ── Schema viewer ─────────────────────────────────────────────────────────────
def render_schema_viewer(schema):
    badge_class = {
        "INTEGER": "badge-integer",
        "REAL":    "badge-real",
        "TEXT":    "badge-text",
        "DATE":    "badge-date",
    }
    rows_html = ""
    for col_name, col_type in schema.items():
        cls = badge_class.get(col_type, "badge-text")
        rows_html += (
            f'<div class="schema-row">'
            f'  <span class="schema-col-name">{col_name}</span>'
            f'  <span class="schema-badge {cls}">{col_type}</span>'
            f'</div>'
        )
    st.markdown(rows_html, unsafe_allow_html=True)


# ── Query history ─────────────────────────────────────────────────────────────
def render_query_history():
    history = st.session_state.query_history
    if not history:
        st.markdown(
            '<div style="color:var(--text-muted);font-size:0.78rem;padding:0.3rem 0;">'
            'No queries yet</div>',
            unsafe_allow_html=True,
        )
        return
    for i, item in enumerate(reversed(history)):
        q_short = item["question"][:38] + ("…" if len(item["question"]) > 38 else "")
        if st.button(q_short, key=f"hist_{i}", use_container_width=True, help=item["question"]):
            st.session_state.active_question = item["question"]
            st.session_state.pending_question = item["question"]
            st.rerun()


# ── Rate limit ────────────────────────────────────────────────────────────────
def render_rate_limit():
    used  = st.session_state.query_count
    limit = st.session_state.rate_limit
    pct   = (used / limit) * 100
    if pct < 50:
        color = "linear-gradient(90deg, #6366F1, #0EA5E9)"
    elif pct < 80:
        color = "linear-gradient(90deg, #F59E0B, #D97706)"
    else:
        color = "linear-gradient(90deg, #F43F5E, #DC2626)"
    st.markdown(
        f'<div class="rate-label"><span>Queries used</span><span>{used} / {limit}</span></div>'
        f'<div class="rate-track">'
        f'  <div class="rate-fill" style="width:{pct}%;background:{color};"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── SQL block — returns HTML string ──────────────────────────────────────────
def render_sql_block(sql):
    keywords = [
        "SELECT", "FROM", "WHERE", "ORDER", "BY", "GROUP", "HAVING",
        "LIMIT", "OFFSET", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER",
        "ON", "AS", "AND", "OR", "NOT", "IN", "LIKE", "BETWEEN", "IS",
        "NULL", "COUNT", "SUM", "AVG", "MAX", "MIN", "DISTINCT",
        "CASE", "WHEN", "THEN", "ELSE", "END", "UNION", "WITH",
    ]
    highlighted = sql
    for kw in keywords:
        pattern = r"\b" + kw + r"\b"
        # Light purple on dark background
        replacement = f'<span style="color:#a5b4fc;font-weight:600">{kw}</span>'
        highlighted = re.sub(pattern, replacement, highlighted, flags=re.IGNORECASE)
    return (
        f'<div class="sql-section">'
        f'<div class="sql-label">Generated SQL</div>'
        f'<div class="sql-display">{highlighted}</div>'
        f'</div>'
    )


# ── Pipeline renderer ─────────────────────────────────────────────────────────
def render_pipeline(steps, placeholder):
    nodes_html = ""
    for idx, step in enumerate(steps):
        status = step.get("status", "waiting")
        icon   = step.get("icon", "●")
        name   = step.get("name", "")
        timing = step.get("timing")
        detail = step.get("detail")

        node_class = f"pipeline-node {status}"

        if status == "complete":
            icon_html = '<span class="pipeline-icon">✅</span>'
        elif status == "error":
            icon_html = '<span class="pipeline-icon">❌</span>'
        elif status == "active":
            icon_html = f'<span class="pipeline-icon"><span class="spinning">{icon}</span></span>'
        else:
            icon_html = f'<span class="pipeline-icon">{icon}</span>'

        timing_html = f'<span class="pipeline-timing">{timing}</span>' if timing else ""
        detail_html = f'<span class="pipeline-detail">{detail}</span>' if detail else ""

        nodes_html += (
            f'<div class="{node_class}">'
            f'  {icon_html}'
            f'  <span class="pipeline-label">{name}</span>'
            f'  {timing_html}{detail_html}'
            f'</div>'
        )
        if idx < len(steps) - 1:
            conn_class = "pipeline-connector"
            if status == "active":
                conn_class += " active"
            elif status == "complete":
                conn_class += " complete"
            nodes_html += f'<div class="{conn_class}"></div>'

    html = (
        f'<div class="pipeline-wrapper">'
        f'  <div class="pipeline-track">{nodes_html}</div>'
        f'</div>'
    )
    placeholder.markdown(html, unsafe_allow_html=True)


# ── Results (Change 5) ────────────────────────────────────────────────────────
def render_results(df, summary, stats):
    st.markdown('<div class="fade-slide-up">', unsafe_allow_html=True)

    # ── Results table (full width) ─────────────────────────────────────────────
    row_count_html = f'<span class="results-row-count">{len(df)} rows</span>'
    st.markdown(
        f'<div class="section-header">'
        f'  <span class="section-title">Query Results</span>'
        f'  {row_count_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

    display_rows = min(len(df), 5)
    st.dataframe(df.head(display_rows), use_container_width=True, height=min(240, 52 + display_rows * 36))

    col_exp, col_dl = st.columns([3, 1])
    with col_exp:
        if len(df) > 5:
            with st.expander(f"Show all {len(df)} rows"):
                st.dataframe(df, use_container_width=True)
    with col_dl:
        st.download_button(
            label="⬇ Export CSV",
            data=df.to_csv(index=False),
            file_name="queryMind_results.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

    # ── AI Analysis card (full width below) ────────────────────────────────────
    # Split summary into readable paragraphs (every 2 sentences)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', summary.strip()) if s.strip()]
    paragraphs = []
    for i in range(0, len(sentences), 2):
        chunk = " ".join(sentences[i:i+2])
        if chunk:
            paragraphs.append(chunk)
    if not paragraphs:
        paragraphs = [summary]

    summary_html = "".join(f'<p class="summary-para">{p}</p>' for p in paragraphs)
    stats_html   = "".join(f'<span class="stat-pill">{s}</span>' for s in stats)

    st.markdown(
        f'<div class="analysis-card">'
        f'  <div class="analysis-title">✦ AI Analysis</div>'
        f'  <div class="analysis-body">{summary_html}</div>'
        f'  <div class="stat-pills-row">{stats_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown('</div>', unsafe_allow_html=True)


# ── Suggestions ───────────────────────────────────────────────────────────────
# Hardcoded suggestions for the sample dataset — guaranteed to return results
_SAMPLE_SUGGESTIONS = [
    "Show total revenue by product category",
    "Who are the top 5 customers by total amount?",
    "How many orders were placed in each region?",
]

def maybe_generate_suggestions(schema, conn=None, table_name=None):
    schema_key = str(schema)
    if st.session_state.get("pills_schema") == schema_key and st.session_state.get("suggestions"):
        return

    # Use hardcoded suggestions for the sample dataset (instant + reliable)
    if st.session_state.get("using_sample"):
        st.session_state.suggestions = _SAMPLE_SUGGESTIONS
        st.session_state.pills_schema = schema_key
        return

    # Fetch a small data sample so Claude generates questions with correct values
    sample_context = ""
    if conn and table_name:
        try:
            sample_df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 4", conn)
            sample_context = f"\n\nSample rows (use these exact values in questions):\n{sample_df.to_csv(index=False)}"
        except Exception:
            pass

    try:
        api_key  = get_api_key()
        client   = anthropic.Anthropic(api_key=api_key)
        col_names = ", ".join(list(schema.keys())[:12])
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            system=(
                "Return exactly 3 short natural language questions, one per line. "
                "No numbering. No quotes. Use only exact values from the sample rows. "
                "Prefer aggregation questions (totals, counts, averages, top N) over filter questions."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Table columns: {col_names}{sample_context}\n"
                    f"Suggest 3 specific, answerable questions. Under 12 words each."
                ),
            }],
        )
        raw = response.content[0].text.strip()
        suggestions = [s.strip("- •*1234567890.").strip()
                       for s in raw.split("\n") if s.strip()][:3]
        while len(suggestions) < 3:
            suggestions.append("Show all records")
    except Exception:
        suggestions = ["Show the top 10 rows", "Count total records", "Show totals by category"]

    st.session_state.suggestions = suggestions
    st.session_state.pills_schema = schema_key


# ── Chatbot ───────────────────────────────────────────────────────────────────
def render_chatbot():
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-user">{msg["message"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-assistant">{msg["message"]}'
                f'<div class="chat-source">Source: QueryMind knowledge base</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    typing_placeholder = st.empty()
    user_input = st.chat_input("Ask about this tool…")

    if user_input:
        st.markdown(
            f'<div class="chat-user">{user_input}</div>',
            unsafe_allow_html=True,
        )
        update_chat_history("user", user_input)

        typing_placeholder.markdown(
            '<div class="typing-indicator">'
            '<span class="typing-dot"></span>'
            '<span class="typing-dot"></span>'
            '<span class="typing-dot"></span>'
            '</div>',
            unsafe_allow_html=True,
        )

        try:
            api_key = get_api_key()
            response = get_chat_response(user_input, api_key)
        except Exception as e:
            response = f"Sorry, couldn't answer right now: {str(e)}"

        typing_placeholder.empty()
        st.markdown(
            f'<div class="chat-assistant">{response}'
            f'<div class="chat-source">Source: QueryMind knowledge base</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        update_chat_history("assistant", response)
        st.rerun()


# ── Query submit orchestration ────────────────────────────────────────────────
def on_query_submit(question, schema, table_name, conn):
    api_key = get_api_key()

    if not check_rate_limit():
        st.error(
            f"You've reached the {st.session_state.rate_limit}-query limit. "
            "Refresh the page to start a new session."
        )
        return

    steps = [
        {"name": "Parsing",     "icon": "🔍", "status": "waiting", "timing": None, "detail": None},
        {"name": "SQL Gen",     "icon": "🧠", "status": "waiting", "timing": None, "detail": None},
        {"name": "Executing",   "icon": "⚡", "status": "waiting", "timing": None, "detail": None},
        {"name": "Summarizing", "icon": "✍️", "status": "waiting", "timing": None, "detail": None},
    ]

    pipeline_placeholder = st.empty()
    sql_placeholder      = st.empty()
    render_pipeline(steps, pipeline_placeholder)

    # Step 1 — Parsing
    steps[0]["status"] = "active"
    render_pipeline(steps, pipeline_placeholder)
    t0 = time.time()
    time.sleep(0.3)
    steps[0]["status"] = "complete"
    steps[0]["timing"] = f"{time.time() - t0:.2f}s"
    render_pipeline(steps, pipeline_placeholder)

    # Step 2 — SQL Generation
    steps[1]["status"] = "active"
    render_pipeline(steps, pipeline_placeholder)
    t1 = time.time()
    # Fetch sample rows so Claude sees exact values and generates correct SQL
    try:
        sample_df  = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
        data_sample = sample_df.to_csv(index=False)
    except Exception:
        data_sample = ""
    sql, sql_error = get_sql(question, schema, table_name, api_key, data_sample)
    if sql_error:
        steps[1]["status"] = "error"
        steps[1]["detail"] = sql_error[:55]
        render_pipeline(steps, pipeline_placeholder)
        st.error(f"SQL generation failed: {sql_error}")
        return
    steps[1]["status"] = "complete"
    steps[1]["timing"] = f"{time.time() - t1:.2f}s"
    steps[1]["detail"] = sql[:50] + ("…" if len(sql) > 50 else "")
    render_pipeline(steps, pipeline_placeholder)
    sql_placeholder.markdown(render_sql_block(sql), unsafe_allow_html=True)

    # Step 3 — Executing
    steps[2]["status"] = "active"
    render_pipeline(steps, pipeline_placeholder)
    t2 = time.time()
    df, exec_error = run_query(sql, conn)
    if exec_error:
        steps[2]["status"] = "error"
        steps[2]["detail"] = exec_error[:55]
        render_pipeline(steps, pipeline_placeholder)
        st.error(f"Query execution failed: {exec_error}")
        return
    df = format_results(df)
    steps[2]["status"] = "complete"
    steps[2]["timing"] = f"{time.time() - t2:.2f}s"
    steps[2]["detail"] = f"{len(df)} rows"
    render_pipeline(steps, pipeline_placeholder)

    if len(df) == 0:
        increment_query_count()
        add_to_history(question, sql, 0)
        st.info("Query returned 0 rows. Try rephrasing — check that filter values match your data.")
        return

    # Step 4 — Summarizing
    steps[3]["status"] = "active"
    render_pipeline(steps, pipeline_placeholder)
    t3 = time.time()
    summary = generate_summary(df, question, api_key)
    steps[3]["status"] = "complete"
    steps[3]["timing"] = f"{time.time() - t3:.2f}s"
    render_pipeline(steps, pipeline_placeholder)

    stats = extract_stats(df, question)
    store_results(sql, df, summary, question)
    increment_query_count()
    add_to_history(question, sql, len(df))

    time.sleep(0.3)
    render_results(df, summary, stats)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    render_header()

    # ── Sidebar (Change 6) ────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<div class="sidebar-logo">QueryMind</div>', unsafe_allow_html=True)

        # Sample dataset banner
        if st.session_state.get("using_sample"):
            st.markdown(
                '<div class="sample-banner">📊 Sample sales dataset · 50 rows</div>',
                unsafe_allow_html=True,
            )
            if st.button("Upload your own CSV", key="clear_sample", use_container_width=True):
                reset_session()
                st.rerun()

        # Data source section
        st.markdown('<div class="sidebar-label">Data Source</div>', unsafe_allow_html=True)

        if st.session_state.get("file_uploaded") and not st.session_state.get("using_sample"):
            filename = st.session_state.get("uploaded_filename", "file.csv")
            st.markdown(
                f'<div class="upload-success">✓ {filename}</div>',
                unsafe_allow_html=True,
            )
            if st.button("Upload different file", key="reupload", use_container_width=True):
                reset_session()
                st.rerun()
        else:
            uploaded_file = st.file_uploader(
                "Upload CSV",
                type=["csv"],
                label_visibility="collapsed",
            )
            if uploaded_file is not None:
                if uploaded_file.name != st.session_state.get("uploaded_filename"):
                    reset_session()
                    with st.spinner("Processing…"):
                        conn, schema, table_name, df, error = process_upload(uploaded_file)
                    if error:
                        st.error(error)
                    else:
                        store_db(conn, schema, table_name)
                        st.session_state.uploaded_filename = uploaded_file.name
                        st.session_state.using_sample = False
                        st.rerun()

            st.markdown(
                '<div style="text-align:center;color:var(--text-muted);'
                'font-size:0.72rem;margin:0.6rem 0;">— or —</div>',
                unsafe_allow_html=True,
            )

            if st.button("📊 Use sample dataset", key="load_sample", use_container_width=True):
                sample_df = pd.read_csv("data/default_dataset.csv")
                reset_session()
                conn, schema, table_name, df, error = process_upload_df(sample_df, "sales_data.csv")
                if error:
                    st.error(error)
                else:
                    store_db(conn, schema, table_name)
                    st.session_state.using_sample = True
                    st.session_state.uploaded_filename = "sample_sales_dataset.csv"
                    st.rerun()

        # Schema, history, rate limit — only when data is loaded
        if st.session_state.get("file_uploaded"):
            st.markdown('<div style="margin-top:1rem;"></div>', unsafe_allow_html=True)

            with st.expander("📋 Table Schema", expanded=True):
                render_schema_viewer(st.session_state.db_schema)

            with st.expander("🕐 Query History", expanded=False):
                render_query_history()

            st.markdown('<div class="sidebar-label">Usage</div>', unsafe_allow_html=True)
            render_rate_limit()

        # Chatbot at bottom in collapsible expander
        st.markdown('<div class="qm-divider"></div>', unsafe_allow_html=True)
        with st.expander("💬 Ask about QueryMind", expanded=False):
            render_chatbot()

    # ── Main area ─────────────────────────────────────────────────────────────
    if not st.session_state.get("file_uploaded"):
        render_empty_state()
        return

    # Generate suggestions once per schema (pass conn so Claude sees real values)
    maybe_generate_suggestions(
        st.session_state.db_schema,
        conn=st.session_state.db_conn,
        table_name=st.session_state.table_name,
    )

    # Apply pending_question BEFORE the widget renders (Streamlit rule)
    if "pending_question" in st.session_state:
        pq = st.session_state.pop("pending_question")
        st.session_state.active_question = pq
        st.session_state["query_input"] = pq
    elif "query_input" not in st.session_state:
        st.session_state["query_input"] = st.session_state.get("active_question", "")

    def _sync_question():
        st.session_state.active_question = st.session_state["query_input"]

    # ── Query section (Change 4) ──────────────────────────────────────────────
    st.markdown('<div class="qm-section-label">Ask your data a question</div>', unsafe_allow_html=True)

    col_input, col_btn = st.columns([5, 1])
    with col_input:
        st.text_input(
            label="question",
            label_visibility="collapsed",
            placeholder="e.g. Show me top 5 customers by total revenue",
            key="query_input",
            on_change=_sync_question,
        )
    with col_btn:
        run_clicked = st.button("Run Query", type="primary", use_container_width=True)

    # Suggestion pills
    if st.session_state.get("suggestions"):
        st.markdown('<div class="suggestion-label">Try asking</div>', unsafe_allow_html=True)
        suggestions = st.session_state.suggestions
        p1, p2, p3 = st.columns(3)
        for pcol, i in zip([p1, p2, p3], range(3)):
            if i < len(suggestions):
                sug = suggestions[i]
                with pcol:
                    if st.button(sug, key=f"pill_{i}", use_container_width=True):
                        st.session_state.active_question = sug
                        st.session_state.pending_question = sug
                        st.rerun()

    st.markdown('<div class="qm-divider"></div>', unsafe_allow_html=True)

    # Run query
    question_to_run = st.session_state.get("active_question", "").strip()

    if run_clicked and question_to_run:
        on_query_submit(
            question_to_run,
            st.session_state.db_schema,
            st.session_state.table_name,
            st.session_state.db_conn,
        )

    # ── Persistent results (Change 7) ─────────────────────────────────────────
    elif st.session_state.get("last_results") is not None:
        df      = st.session_state.last_results
        summary = st.session_state.get("last_summary", "")
        sql     = st.session_state.get("last_sql", "")
        question = st.session_state.get("last_question", "")

        if sql:
            st.markdown(render_sql_block(sql), unsafe_allow_html=True)

        stats = extract_stats(df, question)
        render_results(df, summary, stats)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__" or True:
    main()

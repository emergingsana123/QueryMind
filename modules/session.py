import streamlit as st
from datetime import datetime


def init_session():
    defaults = {
        "db_conn": None,
        "db_schema": None,
        "table_name": None,
        "query_history": [],
        "chat_history": [],
        "query_count": 0,
        "file_uploaded": False,
        "last_results": None,
        "last_sql": None,
        "last_summary": None,
        "last_question": None,
        "rate_limit": 20,
        "using_sample": False,
        "active_question": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_session():
    defaults = {
        "db_conn": None,
        "db_schema": None,
        "table_name": None,
        "query_history": [],
        "query_count": 0,
        "file_uploaded": False,
        "last_results": None,
        "last_sql": None,
        "last_summary": None,
        "last_question": None,
        "using_sample": False,
        "active_question": "",
    }
    for key, value in defaults.items():
        st.session_state[key] = value


def check_rate_limit():
    return st.session_state.query_count < st.session_state.rate_limit


def increment_query_count():
    st.session_state.query_count += 1


def add_to_history(question, sql, row_count):
    entry = {
        "question": question,
        "sql": sql,
        "row_count": row_count,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }
    st.session_state.query_history.append(entry)
    st.session_state.query_history = st.session_state.query_history[-10:]


def store_db(conn, schema, table_name):
    st.session_state.db_conn = conn
    st.session_state.db_schema = schema
    st.session_state.table_name = table_name
    st.session_state.file_uploaded = True


def store_results(sql, df, summary, question):
    st.session_state.last_sql = sql
    st.session_state.last_results = df
    st.session_state.last_summary = summary
    st.session_state.last_question = question

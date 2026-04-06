import streamlit as st
import anthropic
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from knowledge_base.kb import KB

_REFUSAL = (
    "I can only help with questions about how QueryMind works. "
    "For questions about your data, use the query input above!"
)

_TOPIC_SIGNALS = {
    "how", "what", "why", "does", "work", "upload", "csv", "query",
    "sql", "pipeline", "summary", "result", "export", "rate", "limit",
    "dataset", "sample", "column", "table", "chat", "feature", "use",
    "tool", "querymind", "error", "suggest", "run", "click", "button",
    "sidebar",
}


def _get_client(api_key):
    return anthropic.Anthropic(api_key=api_key)


def load_knowledge_base():
    return KB


STOP_WORDS = {
    "the", "a", "an", "is", "are", "what", "how", "does", "do",
    "it", "this", "that", "can", "i", "you", "me", "my", "your",
}


def is_queryMind_related(query):
    words = set(query.lower().split())
    matches = words & _TOPIC_SIGNALS
    return len(matches) >= 2


def find_relevant_docs(query, kb, top_n=2):
    words = set(query.lower().split()) - STOP_WORDS
    scored = []
    for entry in kb:
        content_lower = entry["content"].lower()
        topic_lower = entry["topic"].lower()
        combined = content_lower + " " + topic_lower
        score = sum(1 for w in words if w in combined)
        scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [e for _, e in scored[:top_n]]
    if not any(s > 0 for s, _ in scored[:top_n]):
        top = [e for _, e in scored[:top_n]] if scored else kb[:top_n]
    return top


def build_chat_prompt(query, docs, history):
    context_parts = ["CONTEXT:"]
    for doc in docs:
        context_parts.append(f"[{doc['topic']}] {doc['content']}")
    context_block = "\n".join(context_parts)

    history_parts = []
    for msg in history[-6:]:
        role = msg["role"].capitalize()
        history_parts.append(f"{role}: {msg['message']}")
    history_block = "\n".join(history_parts)

    prompt = (
        f"{context_block}\n\n"
        f"Conversation history:\n{history_block}\n\n"
        f"User: {query}"
    )
    return prompt


def get_chat_response(query, api_key):
    if not is_queryMind_related(query):
        return _REFUSAL

    try:
        kb = load_knowledge_base()
        docs = find_relevant_docs(query, kb, top_n=2)
        history = st.session_state.get("chat_history", [])
        prompt = build_chat_prompt(query, docs, history)

        client = _get_client(api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=(
                "You are a help assistant exclusively for QueryMind, a data analysis tool. "
                "You ONLY answer questions about QueryMind — how it works, how to use it, "
                "its features, its pipeline, its limitations, and how to get the best results from it. "
                "If a user asks anything outside of this scope — including general knowledge questions, "
                "coding questions, questions about their data, mathematical questions, or any topic not "
                "directly about QueryMind as a tool — you must politely decline and redirect them. "
                "Say something like: 'I can only help with questions about how QueryMind works. "
                "For data questions, use the query input above!' "
                "Keep all responses under 120 words. Be friendly and concise."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Sorry, I couldn't process your question right now. Error: {str(e)}"


def update_chat_history(role, message):
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    st.session_state.chat_history.append({"role": role, "message": message})
    st.session_state.chat_history = st.session_state.chat_history[-20:]

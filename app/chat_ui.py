import streamlit as st
import requests
import uuid
import os
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.config import get_settings

settings = get_settings()


API_URL = settings.API_URL

st.set_page_config(page_title="📚 Library Desk Agent", page_icon="📖", layout="wide")
st.markdown(
    """
    <style>
        .stChatMessage { font-size: 16px; line-height: 1.6; }
        .stTextInput > div > div > input {
            background-color: #f9f9f9;
            border-radius: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True
)


if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar – session control
st.sidebar.header("🧠 Chat Sessions")

if st.sidebar.button("🆕 New Session"):
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.sidebar.success("Started a new chat!")

# Load sessions (optional: from DB API)
try:
    sessions = requests.get(f"{API_URL.replace('/chat', '')}/sessions").json()
    session_list = [
    f"{s['session_id']} — 🕒 {s['last_activity'].split('T')[1][:5]} on {s['last_activity'].split('T')[0]}"
    for s in sessions
]
except Exception:
    session_list = []

if session_list:
    selected_label = st.sidebar.selectbox("📂 Load Previous Session", session_list)
    # Extract the real session_id from the label (in case it has date/time in label)
    selected_id = selected_label.split("—")[0].strip()

    if st.sidebar.button("Load"):
        try:
            logs = requests.get(f"{API_URL.replace('/chat', '')}/messages/{selected_id}").json()
            # Ensure we only keep valid message dicts
            messages = [m for m in logs if isinstance(m, dict) and "role" in m and "content" in m]

            st.session_state.session_id = selected_id
            st.session_state.messages = messages

            if messages:
                st.sidebar.success("Session loaded successfully.")
            else:
                st.sidebar.warning("No previous conversation found in this session.")
        except Exception as e:
            st.sidebar.error(f"Failed to load chat session: {e}")


st.sidebar.info(f"**Session ID:** `{st.session_state.session_id}`")


st.title("📚 Library Desk Agent")
st.caption("Your assistant for managing books, orders, and customers.")

chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        with st.chat_message(role):
            prefix = "🧑‍💻 You:" if role == "user" else "🤖 Assistant:"
            st.markdown(f"**{prefix}** {content}", unsafe_allow_html=True)


# -----------------------------
# -----------------------------
user_query = st.chat_input("Ask something about books, orders, or stock...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})

    payload = {
        "query": user_query,
        "session_id": st.session_state.session_id
    }

    with st.spinner("Thinking..."):
        try:
            res = requests.post(API_URL, json=payload)
            res.raise_for_status()
            data = res.json()

            response_text = data.get("summary") or data.get("response") or "No response."
            if isinstance(response_text, dict):
                response_text = str(response_text)

            st.session_state.messages.append({"role": "assistant", "content": response_text})

        except Exception as e:
            st.session_state.messages.append(
                {"role": "assistant", "content": f"⚠️ Error: {e}"}
            )

    st.rerun()

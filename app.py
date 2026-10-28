import os
from datetime import datetime

import streamlit as st

from guardrails import RateLimiter
from rag import load_chunks
from twin import respond

st.set_page_config(page_title='My Digital Twin', page_icon='🤖',
                   layout='centered', initial_sidebar_state='collapsed')

WELCOME = ("Hi! I'm your digital twin. Ask me anything, or try: "
           "'note: buy milk', 'task: finish module 4', or a sum like 25 * 4.")


def now_str():
    return datetime.now().strftime('%H:%M')


def get_secret_key():
    key = os.environ.get('GROQ_API_KEY', '')
    if not key:
        try:
            key = st.secrets.get('GROQ_API_KEY', '')
        except Exception:
            key = ''
    return key


# ---------- Session state ----------
if 'messages' not in st.session_state:
    st.session_state.messages = [{'role': 'assistant', 'content': WELCOME, 'time': now_str()}]
if 'tool_state' not in st.session_state:
    st.session_state.tool_state = {'notes': [], 'tasks': []}
if 'limiter' not in st.session_state:
    st.session_state.limiter = RateLimiter(max_requests=10, window_seconds=60)
if 'stats' not in st.session_state:
    st.session_state.stats = {'blocked': 0, 'pii': 0, 'errors': 0}

chunks = load_chunks('knowledge.txt')

# ---------- Sidebar ----------
with st.sidebar:
    st.header('👤 Profile')
    st.text_input('Your name', key='user_name')

    st.header('⚙️ Settings')
    typed_key = st.text_input('Groq API key', type='password',
                              help='Stays in this browser session only. Leave empty for demo mode.')
    api_key = typed_key or get_secret_key()
    model = st.text_input('Model', value='llama-3.3-70b-versatile',
                          help='Use the same model your Week 1 code used.')
    st.caption('🟢 LLM connected' if api_key else '🟡 Demo mode (no API key)')

    st.header('📊 Stats')
    user_count = sum(1 for m in st.session_state.messages if m['role'] == 'user')
    c1, c2 = st.columns(2)
    c1.metric('Messages', user_count)
    c2.metric('Blocked', st.session_state.stats['blocked'])
    c3, c4 = st.columns(2)
    c3.metric('PII hidden', st.session_state.stats['pii'])
    c4.metric('Errors', st.session_state.stats['errors'])

    with st.expander('📝 Notes & tasks'):
        st.write('**Notes:**', st.session_state.tool_state['notes'] or 'none yet')
        st.write('**Tasks:**', st.session_state.tool_state['tasks'] or 'none yet')

    if st.button('🗑️ Clear chat', use_container_width=True):
        st.session_state.messages = [{'role': 'assistant', 'content': WELCOME, 'time': now_str()}]
        st.rerun()

# ---------- Main chat ----------
st.title('🤖 Digital Twin')
if st.session_state.get('user_name'):
    st.write(f"Chatting as **{st.session_state.user_name}**")

for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.write(msg['content'])
        st.caption(msg['time'])

user_input = st.chat_input('Type your message...')

if user_input:
    if not st.session_state.limiter.allow('me'):
        st.warning("You're sending messages too fast. Please wait a moment.")
    else:
        history = list(st.session_state.messages)
        st.session_state.messages.append(
            {'role': 'user', 'content': user_input, 'time': now_str()})
        with st.chat_message('user'):
            st.write(user_input)

        with st.spinner('Thinking...'):
            try:
                reply, info = respond(user_input, history,
                                      st.session_state.tool_state,
                                      chunks, api_key, model)
            except Exception as e:
                print(f'LLM error: {e}')
                reply = ('Sorry, something went wrong talking to the model. '
                         'Check your API key and model name in Settings.')
                info = {}
                st.session_state.stats['errors'] += 1

        if info.get('blocked'):
            st.session_state.stats['blocked'] += 1
        if info.get('pii'):
            st.session_state.stats['pii'] += 1

        st.session_state.messages.append(
            {'role': 'assistant', 'content': reply, 'time': now_str()})
        st.rerun()

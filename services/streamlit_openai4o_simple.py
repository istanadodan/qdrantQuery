import streamlit as st
import streamlit_openai

st.set_page_config(page_title="GPT-4o 챗봇", page_icon="🤖", layout="centered")

st.title("💬 GPT-4o 챗봇")
st.markdown(
    """
    <style>
    .stChatMessage {background-color: #f0f2f6; border-radius: 10px; padding: 10px; margin-bottom: 10px;}
    .stChatInput {margin-top: 20px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# temperature 슬라이더
temperature = st.sidebar.slider(
    "Temperature (창의성 조절)", min_value=0.0, max_value=1.0, value=0.5, step=0.05
)

# 대화 히스토리 관리
if "chat" not in st.session_state:
    st.session_state.chat = streamlit_openai.Chat(
        model="gpt-4o",
        temperature=temperature,
        instructions="당신은 친절한 한국어 AI 비서입니다.",
    )

# temperature 변경 시 반영
if st.session_state.chat.temperature != temperature:
    st.session_state.chat.temperature = temperature

# 챗봇 실행 (대화 히스토리 자동 관리)
st.session_state.chat.run()

# """
# pip install streamlit streamlit-openai openai
# export OPENAI_API_KEY='sk-...'
# """

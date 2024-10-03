import os
import openai
import streamlit as st
from langchain.prompts import PromptTemplate

# 페이지 너비를 전체 화면으로 설정
st.set_page_config(layout="wide")

# OpenAI API 요청을 처리하는 backend 함수 정의
def call_openai_api(api_key, prompt):
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500
    )
    return response['choices'][0]['message']['content']

# 페이지의 네 개의 프레임 구성
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

# 1. OpenAI API 키 입력받기 프레임 (col1)
with col1:
    st.subheader("OpenAI API 키 입력")
    api_key_input = st.text_input("OpenAI API 키를 입력하세요", type="password")
    if st.button("API 키 저장"):
        if api_key_input:
            st.session_state["api_key"] = api_key_input
            os.environ["OPENAI_API_KEY"] = api_key_input
            st.success("API 키가 성공적으로 저장되었습니다!")
        else:
            st.error("API 키를 입력해야 합니다!")

# 2. 제목과 요청 사항 입력 프레임 (col2)
with col2:
    st.subheader("제목과 요청 사항 입력")
    title = st.text_input("제목을 입력하세요:")
    request = st.text_area("요청 사항을 입력하세요:")
    if title and request:
        st.session_state["prompt"] = f"다음과 같은 제목이 주어졌습니다: {title}\n요청 사항: {request}"

# 3. 실행 버튼 프레임 (col3)
with col3:
    st.subheader("실행")
    if st.button("실행"):
        if not st.session_state.get("api_key"):
            st.error("먼저 OpenAI API 키를 입력하고 저장하세요!")
        elif not st.session_state.get("prompt"):
            st.error("제목과 요청 사항을 입력해야 합니다!")
        else:
            st.session_state["response"] = call_openai_api(st.session_state["api_key"], st.session_state["prompt"])

# 4. 응답 출력 프레임 (col4)
with col4:
    st.subheader("응답 출력")
    if "response" in st.session_state:
        st.text_area("응답:", value=st.session_state["response"], height=300)

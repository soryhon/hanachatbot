import os
import openai
import streamlit as st
from langchain.prompts import PromptTemplate

# Streamlit 설정
st.title("LangChain 및 OpenAI GPT-3.5 연동 (Streamlit)")

# OpenAI API 키 입력받기
if "api_key" not in st.session_state:
    st.session_state["api_key"] = None

st.subheader("OpenAI API 키 설정")

# API 키 입력란 및 저장
api_key_input = st.text_input("OpenAI API 키를 입력하세요", type="password")

# API 키 저장 버튼
if st.button("API 키 저장"):
    if api_key_input:
        st.session_state["api_key"] = api_key_input
        os.environ["OPENAI_API_KEY"] = api_key_input
        st.success("API 키가 성공적으로 저장되었습니다!")
    else:
        st.error("API 키를 입력해야 합니다!")

# LLM 연동 화면
st.subheader("LLM 입력 폼")

# 제목과 요청 사항 입력
title = st.text_input("제목을 입력하세요:")
request = st.text_area("요청 사항을 입력하세요:")

# 실행 버튼 클릭 시 동작
if st.button("실행"):
    if not st.session_state["api_key"]:
        st.error("먼저 OpenAI API 키를 입력하고 저장하세요!")
    elif not title or not request:
        st.error("제목과 요청 사항을 입력해야 합니다!")
    else:
        try:
            # API 키 설정
            openai.api_key = st.session_state["api_key"]

            # 프롬프트 템플릿 생성
            prompt_template = PromptTemplate(
                input_variables=["title", "request"],
                template="""
                다음과 같은 제목이 주어졌습니다: {title}
                여기에는 상세한 요청 사항이 포함되어 있습니다: {request}
                
                이를 기반으로 관련된 잘 구성된 응답을 제공해주세요.
                """
            )

            # 프롬프트 생성
            prompt = prompt_template.format(title=title, request=request)

            # GPT-3.5 모델 호출
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )

            # 응답 출력 (응답 구조에 맞게 변경)
            message = response.choices[0].message["content"]

            st.subheader("LLM 응답:")
            st.write(message)
        
        except Exception as e:
            st.error(f"LLM 처리 중 오류 발생: {str(e)}")

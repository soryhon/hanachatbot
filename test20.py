import streamlit as st
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

# OpenAI API 키 저장 변수
st.title("LangChain 및 OpenAI GPT-4 연동 (Streamlit)")

# OpenAI API 키 입력받기
if "api_key" not in st.session_state:
    st.session_state["api_key"] = None

st.subheader("OpenAI API 키 설정")

api_key_input = st.text_input("OpenAI API 키를 입력하세요", type="password", value=st.session_state["api_key"])

# API 키 저장 버튼
if st.button("API 키 저장"):
    if api_key_input:
        st.session_state["api_key"] = api_key_input
        st.success("API 키가 성공적으로 저장되었습니다!")
    else:
        st.error("API 키가 필요합니다!")

# LLM 연동 화면
st.subheader("LLM 입력 폼")

title = st.text_input("제목을 입력하세요:")
request = st.text_area("요청 사항을 입력하세요:")

# 실행 버튼 클릭 시 동작
if st.button("실행"):
    if not st.session_state["api_key"]:
        st.error("먼저 OpenAI API 키를 입력하고 저장하세요!")
    elif not title or not request:
        st.error("제목과 요청 사항을 입력해야 합니다!")
    else:
        # LangChain과 OpenAI 연동
        try:
            # OpenAI GPT-4 LLM 인스턴스 생성
            llm = OpenAI(
                openai_api_key=st.session_state["api_key"],  # API 키를 직접 전달
                model_name="gpt-4"
            )

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
            
            # LLM에게 프롬프트 전달 및 응답 받기
            response = llm(prompt)

            # 응답 출력
            st.subheader("LLM 응답:")
            st.write(response)
        except Exception as e:
            st.error(f"LLM 처리 중 오류 발생: {str(e)}")

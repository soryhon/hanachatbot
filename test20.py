import streamlit as st
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

# OpenAI API 키 저장 변수
api_key = None

# OpenAI API 키 입력받기
st.title("LangChain & OpenAI Integration with Streamlit")

if "api_key" not in st.session_state:
    api_key_input = st.text_input("Enter your OpenAI API Key", type="password")
    
    if st.button("Save API Key"):
        if api_key_input:
            st.session_state["api_key"] = api_key_input
            st.success("API Key saved successfully!")
        else:
            st.error("API Key is required!")
else:
    api_key = st.session_state["api_key"]
    
    # 제목과 요청사항 입력받기
    title = st.text_input("Enter the title:")
    request = st.text_area("Enter the request details:")

    # 실행 버튼 클릭 시
    if st.button("Execute"):
        if not title or not request:
            st.error("Title and request details are required!")
        else:
            # LangChain과 OpenAI 연동
            try:
                # OpenAI LLM 인스턴스 생성
                llm = OpenAI(api_key=api_key)

                # 프롬프트 템플릿 생성
                prompt_template = PromptTemplate(
                    input_variables=["title", "request"],
                    template="""
                    You are given the following title: {title}
                    Here is the detailed request: {request}
                    
                    Based on this, provide a relevant and well-structured response.
                    """
                )

                # 프롬프트 생성
                prompt = prompt_template.format(title=title, request=request)
                
                # LLM에게 프롬프트 전달 및 응답 받기
                response = llm(prompt)

                # 응답 출력
                st.subheader("LLM Response:")
                st.write(response)
            except Exception as e:
                st.error(f"Error during LLM processing: {str(e)}")

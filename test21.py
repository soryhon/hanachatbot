import os
import openai
import streamlit as st
from langchain.prompts import PromptTemplate
import requests

# 페이지 너비를 전체 화면으로 설정
st.set_page_config(layout="wide")

# GitHub API 요청을 처리하는 함수
def get_github_files(repo, branch, token):
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        files = [item['path'] for item in response.json().get('tree', []) if item['type'] == 'blob']
        return files
    else:
        st.error("GitHub 파일 목록을 가져오지 못했습니다. 저장소 정보나 토큰을 확인하세요.")
        return []

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

# 1. 프레임
# GitHub 정보 저장 및 OpenAI API 키 저장 (가로로 이어서 50%씩 구성)
st.subheader("1. GitHub 정보 저장 및 OpenAI API 키 저장")

col1, col2 = st.columns(2)  # 두 개의 컬럼으로 나눔

# GitHub 정보 저장 프레임 (50%)
with col1:
    st.subheader("GitHub 정보 입력")
    repo_input = st.text_input("GitHub 저장소 (owner/repo 형식)", value="")  # 공백으로 설정
    branch_input = st.text_input("GitHub 브랜치", value="main")
    token_input = st.text_input("GitHub Token", type="password")

    if st.button("GitHub 정보 저장"):
        if repo_input and branch_input and token_input:
            st.session_state["github_repo"] = repo_input
            st.session_state["github_branch"] = branch_input
            st.session_state["github_token"] = token_input
            st.success("GitHub 정보가 성공적으로 저장되었습니다!")
        else:
            st.error("모든 GitHub 정보를 입력해야 합니다!")

# OpenAI API 키 저장 프레임 (50%)
with col2:
    st.subheader("OpenAI API 키 저장")
    api_key_input = st.text_input("OpenAI API 키를 입력하세요", type="password")
    if st.button("API 키 저장"):
        if api_key_input:
            st.session_state["api_key"] = api_key_input
            os.environ["OPENAI_API_KEY"] = api_key_input
            st.success("API 키가 성공적으로 저장되었습니다!")
        else:
            st.error("API 키를 입력해야 합니다!")

# 2. 프레임
# 요청사항 테이블 형식으로 구성 (테두리와 테이블 안에 객체들 포함)
st.subheader("2. 요청사항")

# 요청사항 테이블을 테두리 안에 포함하고, 가로 50%로 설정
st.markdown("""
<style>
    .scrollable-table {
        width: 50%;
        height: 300px;
        overflow-y: scroll;
        border: 2px solid #cccccc;
        border-radius: 5px;
        padding: 10px;
    }
    .scrollable-table div {
        padding: 5px;
    }
</style>
""", unsafe_allow_html=True)

# 테두리 안에 모든 객체를 포함
with st.container():
    st.markdown('<div class="scrollable-table">', unsafe_allow_html=True)

    col1, col2 = st.columns([0.2, 0.8])  # 타이틀과 입력 필드 비율 20%와 80%
    
    with col1:
        st.write("제목")
    with col2:
        title = st.text_input("", value="", disabled=False)

    col1, col2 = st.columns([0.2, 0.8])
    with col1:
        st.write("요청")
    with col2:
        request = st.text_area("", disabled=False)

    col1, col2 = st.columns([0.2, 0.8])
   

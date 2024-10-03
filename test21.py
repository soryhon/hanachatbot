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
# 작성 보고서 요청사항
st.subheader("2. 작성 보고서 요청사항")

title = st.text_input("제목을 입력하세요:")
request = st.text_area("요청 사항을 입력하세요:")

# 프롬프트를 세션 상태에 저장
if title and request:
    st.session_state["prompt"] = f"다음과 같은 제목이 주어졌습니다: {title}\n요청 사항: {request}"

# GitHub 토큰이 저장된 경우에만 파일 리스트 가져오기
if "github_token" in st.session_state:
    files = get_github_files(st.session_state["github_repo"], st.session_state["github_branch"], st.session_state["github_token"])
    
    if files:
        # 파일이 선택되지 않은 기본 상태로 '파일을 선택하세요' 표시
        selected_file = st.selectbox("GitHub 파일을 선택하세요", ["파일을 선택하세요"] + files, index=0)
        if selected_file and selected_file != "파일을 선택하세요":
            st.session_state["selected_file_path"] = selected_file
            st.text(f"선택한 파일 경로: {selected_file}")
    else:
        st.info("저장소에 파일이 없습니다.")
else:
    st.info("먼저 GitHub 토큰을 입력하고 저장하세요.")

# 3. 프레임
# 실행 버튼
st.subheader("3. 실행 버튼")
if st.button("실행"):
    if not st.session_state.get("api_key"):
        st.error("먼저 OpenAI API 키를 입력하고 저장하세요!")
    elif not st.session_state.get("prompt"):
        st.error("제목과 요청 사항을 입력해야 합니다!")
    else:
        st.session_state["response"] = call_openai_api(st.session_state["api_key"], st.session_state["prompt"])

# 4. 프레임
# 결과 보고서
st.subheader("4. 결과 보고서")
if "response" in st.session_state:
    st.text_area("응답:", value=st.session_state["response"], height=300)

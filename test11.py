import streamlit as st
import pandas as pd
import os
import requests
import urllib.parse  # URL 인코딩을 위한 라이브러리

# 서버 측에 파일 저장 디렉토리
UPLOAD_FOLDER = "uploaded_files"  # 서버에 파일을 저장할 디렉토리

# GitHub 저장소에서 파일 목록을 가져오는 함수
def get_github_files(repo, github_token, branch="main"):
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    headers = {
        "Authorization": f"token {github_token}"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        tree = response.json().get("tree", [])
        file_list = [item["path"] for item in tree if item["type"] == "blob"]  # 파일 경로만 추출
        return file_list
    else:
        st.error(f"GitHub 파일 목록을 가져오지 못했습니다: {response.status_code}")
        return []

# GitHub 파일의 URL을 생성하는 함수 (한글과 공백 처리)
def get_file_url(repo, branch, file_path):
    encoded_file_path = urllib.parse.quote(file_path)  # 파일 경로 인코딩 (한글 및 공백 처리)
    return f"https://github.com/{repo}/blob/{branch}/{encoded_file_path}"

# LLM에 요청하여 응답을 받는 함수 (LLM 연동 부분은 예시)
def send_to_llm(prompt, api_key):
    # LLM API에 프롬프트를 전달하고 응답을 받는 예시 (실제로는 OpenAI API나 다른 LLM API 호출)
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.post("https://api.openai.com/v1/completions", headers=headers, json=prompt)
    if response.status_code == 200:
        return response.json()["choices"][0]["text"]  # 응답 텍스트 반환
    else:
        st.error(f"LLM 요청 실패: {response.status_code} - {response.text}")
        return None

# 0. Streamlit 초기 구성 및 프레임 나누기
st.set_page_config(layout="wide")  # 페이지 가로길이를 모니터 전체 해상도로 설정
st.title("일일 업무 및 보고서 자동화 프로그램")

# API 키 및 GitHub 저장소 정보를 메모리에 저장하기 위한 변수 (세션 상태에 저장)
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = None
if 'github_repo' not in st.session_state:
    st.session_state['github_repo'] = None
if 'github_branch' not in st.session_state:
    st.session_state['github_branch'] = 'main'  # 기본 브랜치 main으로 설정

# Streamlit의 세로 프레임 구성
col1, col2, col3 = st.columns([0.39, 0.10, 0.49])

# 데이터 저장을 위한 임시 변수들
rows = []
llm_results = {}

# 1. 작성 보고서 요청사항
with col1:
    st.subheader("1. 작성 보고서 요청사항")
    df = pd.DataFrame(columns=["제목", "요청", "데이터"])

    # 기본 1행 추가
    if len(rows) == 0:
        rows.append({"제목": "titleValue1", "요청": "requestValue1", "데이터": ""})

    for idx, row in enumerate(rows):
        st.text(f"행 {idx+1}")
        row['제목'] = st.text_input(f"제목 (행 {idx+1})", row['제목'])

import streamlit as st
import pandas as pd
import os
import requests
import base64  # base64 인코딩을 위해 필요
import urllib.parse  # URL 인코딩을 위한 라이브러리

# GitHub 저장소에서 파일 또는 폴더가 존재하는지 확인하는 함수
def check_github_folder_exists(repo, folder_name, github_token, branch="main"):
    url = f"https://api.github.com/repos/{repo}/contents/{folder_name}?ref={branch}"
    headers = {
        "Authorization": f"token {github_token}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    return response.status_code == 200

# GitHub에 폴더를 생성하는 함수
def create_github_folder(repo, folder_name, github_token, branch="main"):
    url = f"https://api.github.com/repos/{repo}/contents/{folder_name}/.gitkeep"
    headers = {
        "Authorization": f"token {github_token}",
        "Content-Type": "application/json"
    }
    content_base64 = base64.b64encode(b"").decode("utf-8")  # 빈 파일 생성
    data = {
        "message": f"Create {folder_name} folder",
        "content": content_base64,
        "branch": branch
    }
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code == 201:
        st.success(f"{folder_name} 폴더가 생성되었습니다.")
    else:
        st.error(f"폴더 생성 실패: {response.status_code} - {response.text}")

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

# GitHub에 파일을 업로드하는 함수
def upload_file_to_github(repo, folder_name, file_name, content, github_token, branch="main"):
    url = f"https://api.github.com/repos/{repo}/contents/{folder_name}/{file_name}"
    headers = {
        "Authorization": f"token {github_token}",
        "Content-Type": "application/json"
    }
    # 파일 내용을 base64로 인코딩
    content_base64 = base64.b64encode(content).decode("utf-8")
    data = {
        "message": f"Upload {file_name}",
        "content": content_base64,
        "branch": branch
    }
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code == 201:
        st.success(f"파일이 GitHub 저장소에 성공적으로 업로드되었습니다: {file_name}")
    else:
        st.error(f"GitHub 업로드 실패: {response.status_code} - {response.text}")

# 파일을 GitHub에 업로드할 때 사용하는 함수
def save_uploaded_file(uploaded_file, repo, github_token, branch="main"):
    folder_name = "uploadFiles"
    
    # 폴더가 존재하는지 확인
    if not check_github_folder_exists(repo, folder_name, github_token, branch):
        # 폴더가 존재하지 않으면 생성
        create_github_folder(repo, folder_name, github_token, branch)
    
    # 파일을 GitHub에 저장
    upload_file_to_github(repo, folder_name, uploaded_file.name, uploaded_file.read(), github_token, branch)

# 0. Streamlit 초기 구성 및 프레임 나누기
st.set_page_config(layout="wide")  # 페이지 가로길이를 모니터 전체 해상도로 설정
st.title("일일 업무 및 보고서 자동화 프로그램")

# API 키 및 GitHub 저장소 정보를 메모리에 저장하기 위한 변수 (세션 상태에 저장)
if 'openai_api_key' not in st.session_state:
    st.session_state['openai_api_key'] = None
if 'github_token' not in st.session_state:
    st.session_state['github_token'] = None
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
        row['요청'] = st.text_input(f"요청 (행 {idx+1})", row['요청'])
        
        # GitHub에서 파일 선택
        if st.button(f"선택 (행 {idx+1})"):
            # GitHub 정보가 모두 설정되었는지 확인
            if st.session_state['github_repo'] and st.session_state['github_token']:
                # GitHub에서 파일 목록 가져오기
                file_list = get_github_files(st.session_state['github_repo'], st.session_state['github_token'], st.session_state['github_branch'])
                
                if file_list:
                    selected_file = st.selectbox(f"GitHub 파일 선택 (행 {idx+1})", options=file_list)
                    if selected_file:
                        file_url = get_file_url(st.session_state['github_repo'], st.session_state['github_branch'], selected_file)
                        row['데이터'] = file_url  # 선택된 파일의 URL 저장
                        st.success(f"선택한 파일: {selected_file}\nURL: {file_url}")
                else:
                    st.error("GitHub 파일 목록을 가져오지 못했습니다.")
            else:
                st.warning("GitHub 저장소 정보 또는 API 토큰이 설정되지 않았습니다. 정보를 먼저 입력해주세요.")
        
        # URL 정보 표시
        file_path = st.text_input(f"데이터 (행 {idx+1})", row['데이터'], disabled=True)

    # 행 추가 및 삭제 버튼
    if st.button("행 추가"):
        rows.append({"제목": f"titleValue{len(rows) + 1}", "요청": f"requestValue{len(rows) + 1}", "데이터": ""})
    if st.button("행 삭제"):
        rows = rows[:-1] if len(rows) > 1 else rows  # 최소 1행은 유지

# 2. 파일 업로드 기능 (GitHub 업로드)
with col1:
    st.subheader("2. 파일 업로드")
    uploaded_files = st.file_uploader("파일을 여러 개 드래그 앤 드롭하여 업로드하세요.", accept_multiple_files=True)

    if uploaded_files and st.session_state['github_repo'] and st.session_state['github_token']:
        for uploaded_file in uploaded_files:
            # 파일을 GitHub 저장소에 업로드
            save_uploaded_file(uploaded_file, st.session_state['github_repo'], st.session_state['github_token'])

# 3. GitHub 저장소 정보 입력
with col2:
    st.subheader("GitHub 저장소 정보 입력")

    # GitHub 저장소 경로 입력
    if st.session_state['github_repo'] is None:
        st.warning("GitHub 저장소 정보를 입력하세요.")
        github_repo = st.text_input("GitHub 저장소 경로 (예: username/repo)")
        if st.button("저장소 정보 저장"):
            if github_repo:
                st.session_state['github_repo'] = github_repo
                st.success("GitHub 저장소 경로가 저장되었습니다.")
    else:
        st.info(f"저장소: {st.session_state['github_repo']}")

    # GitHub API 토큰 입력
    if st.session_state['github_token'] is None:
        st.warning("GitHub API 토큰을 입력하세요.")
        github_token = st.text_input("GitHub API 토큰 입력", type="password")
        if st.button("GitHub API 토큰 저장"):
            if github_token:
                st.session_state['github_token'] = github_token
                st.success("GitHub API 토큰이 저장되었습니다.")
    else:
        st.info("GitHub API 토큰이 저장되어 있습니다.")

    # 브랜치 입력
    github_branch = st.text_input("브랜치 이름 (예: main 또는 master)", value=st.session_state['github_branch'])
    if st.button("브랜치 저장"):
        st.session_state['github_branch'] = github_branch
        st.success(f"브랜치가 '{github_branch}'로 설정되었습니다.")

# 3. 실행 버튼 및 OpenAI API 키 입력
with col2:
    st.subheader("3. 실행")

    # OpenAI API 키 입력 부분
    if st.session_state['openai_api_key'] is None:
        st.warning("OpenAI API 키가 필요합니다.")
        openai_api_key = st.text_input("OpenAI API 키를 입력하세요.", type="password")
        if st.button("OpenAI API 키 저장"):
            if openai_api_key.startswith("sk-"):  # OpenAI API 키는 보통 'sk-'로 시작합니다.
                st.session_state['openai_api_key'] = openai_api_key
                st.success("OpenAI API 키가 저장되었습니다.")
            else:
                st.error("올바른 OpenAI API 키를 입력하세요. 키는 'sk-'로 시작해야 합니다.")
    else:
        st.info("OpenAI API 키가 저장되어 있습니다.")

    # LLM 실행 버튼
    if st.button("실행"):
        if st.session_state['openai_api_key'] is None:
            st.error("OpenAI API 키를 입력해야 실행할 수 있습니다.")
        else:
            # 모든 행의 정보를 기반으로 프롬프트 구성
            for idx, row in enumerate(rows):
                # 각 행의 정보를 프롬프트 형식으로 구성
                prompt = [
                    {
                        "role": "system",
                        "content": "다음 파일을 분석하여 보고서를 작성하세요."
                    },
                    {
                        "role": "user",
                        "content": f"보고서 제목 : '{row['제목']}'\n요청 문구 : 이 파일을 분석해서 '{row['요청']}'에 맞춰 보고서를 작성해\n데이터 전달 : '{row['데이터']}'"
                    }
                ]
                
                # LLM에 프롬프트 전달하고 응답 받기
                llm_response = send_to_llm(prompt, st.session_state['openai_api_key'])
                
                if llm_response:
                    llm_results[idx] = llm_response  # 결과 저장
                else:
                    llm_results[idx] = "LLM 응답을 받지 못했습니다."

            st.success("LLM 요청이 완료되었습니다.")

# 4. 결과 보고서 화면
with col3:
    st.subheader("4. 결과 보고서")
    
    if llm_results:
        for idx, result in llm_results.items():
            st.text(f"제목: {rows[idx]['제목']}")
            st.text(f"LLM 응답 결과:\n{result}")
    
    # 결과 보고서 다운로드
    if st.button("Export"):
        file_type = st.selectbox("파일 형식 선택", options=["pdf", "docx", "xlsx", "txt"])
        st.success(f"{file_type} 형식으로 파일 다운로드 가능")

# 5. 참고 템플릿 미리보기
with col1:
    st.subheader("5. 참고 템플릿 미리보기")

    selected_template_file = st.selectbox("템플릿 파일 선택", options=["Template1", "Template2", "Template3"])
    if st.button("선택"):
        st.success(f"선택한 템플릿: {selected_template_file}")
        # 템플릿 미리보기 구현 (팝업창이나 별도의 영역에 표시)

# 6. 저장
with col3:
    st.subheader("6. 저장")
    
    # 결과 저장
    save_path = st.text_input("저장할 파일명 입력")
    if st.button("저장") and save_path:
        # rows 데이터프레임 저장
        df = pd.DataFrame(rows)
        df.to_csv(f"{save_path}.csv")
        st.success(f"{save_path}.csv 파일로 저장되었습니다.")

# 7. 불러오기
with col3:
    st.subheader("7. 불러오기")
    
    # CSV 파일 불러오기
    uploaded_save_file = st.file_uploader("저장된 CSV 파일 불러오기", type=["csv"])
    if uploaded_save_file is not None:
        loaded_data = pd.read_csv(uploaded_save_file)
        st.dataframe(loaded_data)
        st.success("데이터가 불러와졌습니다.")

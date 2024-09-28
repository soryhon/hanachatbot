import streamlit as st
import pandas as pd
import os
import requests
from io import BytesIO
import base64

# 서버 측에 파일 저장 디렉토리
UPLOAD_FOLDER = "uploaded_files"  # 서버에 파일을 저장할 디렉토리

# 서버에 파일 저장 함수
def save_file_to_server(uploaded_file):
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

# GitHub에 파일 업로드 함수
def upload_file_to_github(file_path, file_name, github_token, repo, branch):
    # 파일 내용 읽기
    with open(file_path, "rb") as f:
        content = f.read()
    
    # 파일 내용을 base64로 인코딩
    encoded_content = base64.b64encode(content).decode("utf-8")

    # GitHub API URL
    url = f"https://api.github.com/repos/{repo}/contents/{file_name}"

    # 요청 헤더
    headers = {
        "Authorization": f"token {github_token}",
        "Content-Type": "application/json"
    }

    # GitHub API에 보낼 데이터
    data = {
        "message": f"Uploading {file_name} via Streamlit app",
        "content": encoded_content,
        "branch": branch
    }

    # 파일 업로드 요청
    response = requests.put(url, json=data, headers=headers)
    
    if response.status_code == 201:
        st.success(f"{file_name}가 GitHub에 성공적으로 업로드되었습니다.")
    elif response.status_code == 401:
        st.error(f"GitHub 업로드 실패: {response.status_code} - 인증 오류 (Bad credentials). 올바른 Personal Access Token을 입력했는지 확인하세요.")
    elif response.status_code == 404:
        st.error(f"GitHub 업로드 실패: {response.status_code} - 저장소 경로를 찾을 수 없습니다. 저장소 경로를 확인해주세요.")
        st.write(f"GitHub API 응답: {response.json()}")  # API 응답 전체를 출력하여 디버깅
    else:
        st.error(f"GitHub 업로드 실패: {response.status_code} - {response.text}")

# GitHub API 사용량 제한 확인 함수
def check_github_rate_limit(github_token):
    url = "https://api.github.com/rate_limit"
    headers = {"Authorization": f"token {github_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        st.write("GitHub API 사용량 제한 정보:", response.json())
    else:
        st.error(f"API 사용량 제한 정보를 가져오는 데 실패했습니다: {response.status_code}")

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
uploaded_files = []
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
        file_path = st.text_input(f"데이터 (행 {idx+1})", row['데이터'], disabled=True)
        if st.button(f"선택 (행 {idx+1})"):
            uploaded_file = st.file_uploader("파일 업로드", type=['txt', 'csv', 'pdf', 'docx', 'xlsx', 'pptx'])
            if uploaded_file is not None:
                row['데이터'] = uploaded_file.name
                uploaded_files.append(uploaded_file)

    # 행 추가 및 삭제 버튼
    if st.button("행 추가"):
        rows.append({"제목": f"titleValue{len(rows) + 1}", "요청": f"requestValue{len(rows) + 1}", "데이터": ""})
    if st.button("행 삭제"):
        rows = rows[:-1] if len(rows) > 1 else rows  # 최소 1행은 유지

# 2. 파일 업로드 기능
with col1:
    st.subheader("2. 파일 업로드")
    uploaded_files = st.file_uploader("파일을 여러 개 드래그 앤 드롭하여 업로드하세요.", accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            # 서버에 파일 저장
            file_path = save_file_to_server(uploaded_file)
            
            # GitHub에 파일 업로드, GitHub 저장소 경로와 토큰을 입력받음
            if st.session_state['api_key'] and st.session_state['github_repo']:
                upload_file_to_github(file_path, uploaded_file.name, st.session_state['api_key'], st.session_state['github_repo'], st.session_state['github_branch'])
            else:
                st.warning("GitHub 저장소 정보 또는 API 토큰을 입력해야 합니다.")

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
    if st.session_state['api_key'] is None:
        st.warning("GitHub API 토큰을 입력하세요.")
        api_key = st.text_input("GitHub API 토큰 입력", type="password")
        if st.button("API 토큰 저장"):
            if api_key:
                st.session_state['api_key'] = api_key
                st.success("API 토큰이 저장되었습니다.")
                # 토큰 저장 후 GitHub 사용량 제한 확인
                check_github_rate_limit(st.session_state['api_key'])
    else:
        st.info("API 토큰이 저장되어 있습니다.")

# 5. 참고 템플릿 미리보기
with col1:
    st.subheader("5. 참고 템플릿 미리보기")
    selected_template_file = st.selectbox("템플릿 파일 선택", options=["Template1", "Template2", "Template3"])
    if st.button("선택"):
        if selected_template_file:
            st.write(f"선택한 템플릿: {selected_template_file}")
            # 파일 내용 미리보기 팝업창 구현은 Streamlit 제한 상 생략

# 3. 실행 버튼 및 OpenAPI 키 입력
with col2:
    st.subheader("3. 실행")

    # OpenAI API 키 입력 부분
    if st.session_state['api_key'] is None:
        st.warning("OpenAI API 키가 필요합니다.")
        api_key = st.text_input("OpenAI API 키를 입력하세요.", type="password")
        if st.button("API 키 저장"):
            if api_key:
                st.session_state['api_key'] = api_key
                st.success("API 키가 저장되었습니다.")
    else:
        st.info("OpenAI API 키가 이미 저장되어 있습니다.")

    # LLM 실행 버튼
    if st.button("실행"):
        if st.session_state['api_key'] is None:
            st.error("OpenAI API 키를 입력해야 실행할 수 있습니다.")
        else:
            for idx, row in enumerate(rows):
                # LLM 프롬프트 생성
                prompt = f"제목: {row['제목']}\n요청: {row['요청']}\n데이터 경로: {row['데이터']}"
                # GPT-4 모델에 프롬프트 전달 (예시, 실제로는 OpenAI API 호출 필요)
                llm_results[idx] = f"LLM 응답 결과 값 {idx + 1}"
            st.success("LLM 요청이 완료되었습니다.")

# 4. 결과 보고서 화면
with col3:
    st.subheader("4. 결과 보고서")
    if llm_results:
        for idx, result in llm_results.items():
            st.text(f"제목 {rows[idx]['제목']}")
            st.text(f"LLM 응답 결과: {result}")
    if st.button("Export"):
        file_type = st.selectbox("파일 형식 선택", options=["pdf", "docx", "xlsx", "txt"])
        st.success(f"{file_type} 형식으로 파일 다운로드 가능")

# 6. 저장
with col3:
    st.subheader("6. 저장")
    if st.button("저장"):
        save_path = st.text_input("저장할 파일명 입력")
        if save_path:
            df.to_csv(f"{save_path}.csv")
            st.success(f"{save_path}.csv 파일로 저장되었습니다.")

# 7. 불러오기
with col3:
    st.subheader("7. 불러오기")
    uploaded_save_file = st.file_uploader("저장된 CSV 파일 불러오기")
    if uploaded_save_file is not None:
        loaded_data = pd.read_csv(uploaded_save_file)
        st.dataframe(loaded_data)
        st.success("데이터가 불러와졌습니다.")

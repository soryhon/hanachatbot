import streamlit as st
import pandas as pd
import requests
import base64  # base64 인코딩 및 디코딩을 위한 라이브러리
import urllib.parse  # URL 인코딩을 위한 라이브러리

# GitHub 정보 (JSON 데이터에서 가져온 값)
github_info = {
    "github_repo": "soryhon/hanachatbot",
    "github_branch": "main",
    "github_token": "ghp_GJIM****************************EDdW"  # 원래 형식의 GitHub Personal Access Token (PAT)
}

# OpenAI에 LLM 요청을 보내는 함수
def send_to_llm(prompt, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    url = "https://api.openai.com/v1/chat/completions"
    data = {
        "model": "gpt-4",
        "messages": prompt,
        "max_tokens": 1000,
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"LLM 요청 실패: {response.status_code} - {response.text}")
        return None

# GitHub에 파일을 업로드하는 함수
def upload_file_to_github(repo, folder_name, file_name, content, token, branch="main"):
    url = f"https://api.github.com/repos/{repo}/contents/{folder_name}/{file_name}"
    headers = {
        "Authorization": f"token {token}",  # GitHub 토큰을 직접 사용
        "Content-Type": "application/json"
    }
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

# GitHub에서 파일 목록을 가져오는 함수
def get_github_files(repo, token, folder_name=None, branch="main"):
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    headers = {
        "Authorization": f"token {token}",  # GitHub 토큰을 직접 사용
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        tree = response.json().get("tree", [])
        if folder_name:
            file_list = [item["path"] for item in tree if folder_name in item["path"] and item["type"] == "blob"]
        else:
            file_list = [item["path"] for item in tree if item["type"] == "blob"]
        return file_list
    else:
        st.error(f"GitHub 파일 목록을 가져오지 못했습니다: {response.status_code}")
        return []

# GitHub 파일의 URL을 생성하는 함수 (한글과 공백 처리)
def get_file_url(repo, branch, file_path):
    """GitHub 파일의 URL을 생성하는 함수. 한글 및 공백을 처리하여 인코딩합니다."""
    encoded_file_path = urllib.parse.quote(file_path)  # 파일 경로 인코딩 (한글 및 공백 처리)
    return f"https://github.com/{repo}/blob/{branch}/{encoded_file_path}"

# 0. Streamlit 초기 구성 및 프레임 나누기
st.set_page_config(layout="wide")
st.title("일일 업무 및 보고서 자동화 프로그램")

# GitHub 저장소 정보 및 토큰을 JSON 데이터에서 각 변수로 저장
github_repo = github_info["github_repo"]
github_branch = github_info["github_branch"]
github_token = github_info["github_token"]  # Base64 복호화 없이 원래 토큰 값 그대로 사용

# Streamlit의 세로 프레임 구성
col1, col2, col3 = st.columns([0.39, 0.10, 0.49])

# 데이터 저장을 위한 임시 변수들
rows = []
llm_results = {}

# 1. 작성 보고서 요청사항
with col1:
    st.subheader("1. 작성 보고서 요청사항")
    df = pd.DataFrame(columns=["제목", "요청", "데이터"])

    if len(rows) == 0:
        rows.append({"제목": "titleValue1", "요청": "requestValue1", "데이터": ""})

    for idx, row in enumerate(rows):
        st.text(f"행 {idx+1}")
        row['제목'] = st.text_input(f"제목 (행 {idx+1})", row['제목'])
        row['요청'] = st.text_input(f"요청 (행 {idx+1})", row['요청'])

        # GitHub에서 파일 리스트를 가져옴
        file_list = []
        if github_repo and github_token:
            upload_files_exist = any("uploadFiles" in item for item in get_github_files(github_repo, github_token, branch=github_branch))
            if upload_files_exist:
                st.success("uploadFiles 폴더가 존재합니다.")
                file_list = get_github_files(github_repo, github_token, folder_name="uploadFiles", branch=github_branch)
            else:
                st.warning("uploadFiles 폴더가 존재하지 않습니다. 기본 폴더의 파일을 표시합니다.")
                file_list = get_github_files(github_repo, github_token, branch=github_branch)

        selected_file = st.selectbox(f"파일 선택 (행 {idx+1})", options=file_list, key=f"file_select_{idx}")

        if st.button(f"선택 (행 {idx+1})"):
            if selected_file:
                file_url = get_file_url(github_repo, github_branch, selected_file)
                rows[idx]['데이터'] = file_url
                st.success(f"선택한 파일: {selected_file}\nURL: {file_url}")

        file_path = st.text_input(f"데이터 (행 {idx+1})", row['데이터'], disabled=True, key=f"file_path_{idx}")

    if st.button("행 추가"):
        rows.append({"제목": f"titleValue{len(rows) + 1}", "요청": f"requestValue{len(rows) + 1}", "데이터": ""})
    if st.button("행 삭제"):
        rows = rows[:-1] if len(rows) > 1 else rows

# 2. 파일 업로드 및 GitHub 정보 표시
with col1:
    st.subheader("2. 파일 업로드")

    st.info(f"저장소: {github_repo}")
    st.info(f"브랜치: {github_branch}")

    uploaded_files = st.file_uploader("파일을 여러 개 드래그 앤 드롭하여 업로드하세요.", accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            upload_file_to_github(github_repo, 'uploadFiles', uploaded_file.name, uploaded_file.read(), github_token, github_branch)

# 3. 실행 버튼 및 OpenAI API 키 입력
with col2:
    st.subheader("3. 실행")

    if 'openai_api_key' not in st.session_state:
        st.session_state['openai_api_key'] = None

    if st.session_state['openai_api_key'] is None:
        st.warning("OpenAI API 키가 필요합니다.")
        openai_api_key = st.text_input("OpenAI API 키를 입력하세요.", type="password")
        if st.button("OpenAI API 키 저장"):
            if openai_api_key.startswith("sk-"):
                st.session_state['openai_api_key'] = openai_api_key
                st.success("OpenAI API 키가 저장되었습니다.")
            else:
                st.error("올바른 OpenAI API 키를 입력하세요.")
    else:
        st.info("OpenAI API 키가 저장되어 있습니다.")

    if st.button("실행"):
        if st.session_state['openai_api_key'] is None:
            st.error("OpenAI API 키를 입력해야 실행할 수 있습니다.")
        else:
            for idx, row in enumerate(rows):
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
                
                llm_response = send_to_llm(prompt, st.session_state['openai_api_key'])
                if llm_response:
                    llm_results[idx] = llm_response
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
    
    if st.button("Export"):
        file_type = st.selectbox("파일 형식 선택", options=["pdf", "docx", "xlsx", "txt"])
        st.success(f"{file_type} 형식으로 파일 다운로드 가능")

# 5. 참고 템플릿 미리보기
with col1:
    st.subheader("5. 참고 템플릿 미리보기")
    
    selected_template_file = st.selectbox("템플릿 파일 선택", options=["Template1", "Template2", "Template3"])
    if st.button("선택"):
        st.success(f"선택한 템플릿: {selected_template_file}")

# 6. 저장
with col3:
    st.subheader("6. 저장")
    
    save_path = st.text_input("저장할 파일명 입력")
    if st.button("저장") and save_path:
        df = pd.DataFrame(rows)
        df.to_csv(f"{save_path}.csv")
        st.success(f"{save_path}.csv 파일로 저장되었습니다.")

# 7. 불러오기
with col3:
    st.subheader("7. 불러오기")
    
    uploaded_save_file = st.file_uploader("저장된 CSV 파일 불러오기", type=["csv"])
    if uploaded_save_file:
        loaded_data = pd.read_csv(uploaded_save_file)
        st.dataframe(loaded_data)
        st.success("데이터가 불러와졌습니다.")

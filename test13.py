import streamlit as st
import pandas as pd
import requests
import urllib.parse  # URL 인코딩을 위한 라이브러리
import base64  # base64 인코딩 및 복호화를 위한 라이브러리

# 페이지 설정
st.set_page_config(layout="wide")  # 페이지 가로길이를 모니터 전체 해상도로 설정

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

# GitHub에서 파일의 sha 값을 가져오는 함수
def get_file_sha(repo, file_path, github_token, branch="main"):
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}"
    headers = {
        "Authorization": f"token {github_token}"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("sha")
    else:
        return None

# GitHub에 파일을 업로드하거나 덮어쓰는 함수
def upload_file_to_github(repo, folder_name, file_name, content, github_token, branch="main", sha=None):
    url = f"https://api.github.com/repos/{repo}/contents/{folder_name}/{file_name}"
    headers = {
        "Authorization": f"token {github_token}",
        "Content-Type": "application/json"
    }
    content_base64 = base64.b64encode(content).decode("utf-8")
    data = {
        "message": f"Upload {file_name}",
        "content": content_base64,
        "branch": branch
    }

    # sha 값이 있으면 덮어쓰기
    if sha:
        data["sha"] = sha

    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code == 201:
        st.success(f"파일이 GitHub 저장소에 성공적으로 업로드되었습니다: {file_name}")
    elif response.status_code == 200:  # 덮어쓰기 성공
        st.success(f"파일이 GitHub 저장소에 성공적으로 덮어쓰기되었습니다: {file_name}")
    else:
        st.error(f"GitHub 업로드 실패: {response.status_code} - {response.text}")

# GitHub에서 파일 목록을 가져오는 함수
def get_github_files(repo, github_token, folder_name=None, branch="main"):
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    headers = {
        "Authorization": f"token {github_token}"
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
    encoded_file_path = urllib.parse.quote(file_path)
    return f"https://github.com/{repo}/blob/{branch}/{encoded_file_path}"

# API 키 및 GitHub 저장소 정보를 메모리에 저장하기 위한 변수 (세션 상태에 저장)
if 'openai_api_key' not in st.session_state:
    st.session_state['openai_api_key'] = ""
if 'github_token' not in st.session_state:
    st.session_state['github_token'] = None  # GitHub 토큰을 수동으로 입력
if 'github_repo' not in st.session_state:
    st.session_state['github_repo'] = "soryhon/hanachatbot"
if 'github_branch' not in st.session_state:
    st.session_state['github_branch'] = "main"

# GitHub 저장소 정보 입력 기능
st.subheader("GitHub 저장소 정보 입력")

# GitHub 저장소 경로 입력
github_repo = st.text_input("GitHub 저장소 경로 (예: username/repo)", value=st.session_state['github_repo'])

# GitHub API 토큰 입력 (수동으로 입력)
github_token = st.text_input("GitHub API 토큰 입력", type="password")

# 브랜치 입력
github_branch = st.text_input("브랜치 이름 (예: main 또는 master)", value=st.session_state['github_branch'])

if st.button("GitHub 정보 저장"):
    st.session_state['github_repo'] = github_repo
    st.session_state['github_token'] = github_token
    st.session_state['github_branch'] = github_branch
    st.success("GitHub 정보가 성공적으로 저장되었습니다.")
    
    # GitHub 토큰이 제대로 저장되었는지 확인하는 메시지 추가
    if st.session_state['github_token']:
        st.info(f"GitHub 토큰이 저장되었습니다. 저장된 토큰: {st.session_state['github_token'][:5]}...")

# OpenAI API 키 입력 로직
st.subheader("OpenAI API 키 입력")

openai_api_key = st.text_input("OpenAI API 키를 입력하세요.", type="password")

if st.button("OpenAI API 키 저장"):
    st.session_state['openai_api_key'] = openai_api_key
    st.success("OpenAI API 키가 저장되었습니다.")

# 3개의 프레임 나누기
col1, col2, col3 = st.columns([0.39, 0.10, 0.49])  # 세로 구분선을 위해 가로 폭을 지정

# 1 프레임 (39%) - 스크롤 가능한 영역으로 구성, 세로 길이 50% 고정
with col1:
    st.subheader("1. 작성 보고서 요청사항")

    # 고정된 50% 높이로 스크롤 영역 구현
    with st.expander("요청사항 리스트", expanded=True):
        df = pd.DataFrame(columns=["제목", "요청", "데이터"])
        if 'rows' not in st.session_state:
            st.session_state['rows'] = [{"제목": "", "요청": "", "데이터": "", "checked": False}]  # 기본 행

        rows = st.session_state['rows']  # 세션 상태에 저장된 행 목록을 사용
        checked_rows = []  # 체크된 행들을 저장하기 위한 리스트

        # 행 목록을 순서대로 출력
        for idx, row in enumerate(rows):
            with st.container():
                # 요청사항1에 체크박스 추가 (삭제 용도)
                row_checked = st.checkbox(f"요청사항 {idx+1}", key=f"row_checked_{idx}", value=row.get("checked", False))
                
                # 제목 및 요청 입력란
                row['제목'] = st.text_input(f"제목 (요청사항 {idx+1})", row['제목'])
                row['요청'] = st.text_input(f"요청 (요청사항 {idx+1})", row['요청'])

                # 체크된 행들을 저장
                if row_checked:
                    checked_rows.append(idx)
                    row["checked"] = True  # 체크된 상태 저장
                else:
                    row["checked"] = False  # 체크 해제 상태 저장

                # GitHub 파일 선택
                file_list = []
                if st.session_state['github_repo'] and st.session_state['github_token']:
                    upload_files_exist = any("uploadFiles" in item for item in get_github_files(st.session_state['github_repo'], st.session_state['github_token'], branch=st.session_state['github_branch']))
                    
                    if upload_files_exist:
                        st.success("uploadFiles 폴더가 존재합니다.")
                        file_list = get_github_files(st.session_state['github_repo'], st.session_state['github_token'], folder_name="uploadFiles", branch=st.session_state['github_branch'])
                    else:
                        st.warning("uploadFiles 폴더가 존재하지 않습니다. 기본 폴더의 파일을 표시합니다.")
                        file_list = get_github_files(st.session_state['github_repo'], st.session_state['github_token'], branch=st.session_state['github_branch'])

                selected_file = st.selectbox(f"파일 선택 (요청사항 {idx+1})", options=file_list, key=f"file_select_{idx}")
                
                if st.button(f"선택 (요청사항 {idx+1})") and selected_file:
                    file_url = get_file_url(st.session_state['github_repo'], st.session_state['github_branch'], selected_file)
                    rows[idx]['데이터'] = file_url  # 선택한 파일 URL 저장
                    st.success(f"선택한 파일: {selected_file}\nURL: {file_url}")

                # URL 정보 표시
                st.text_input(f"데이터 (요청사항 {idx+1})", row['데이터'], disabled=True, key=f"file_path_{idx}")

        # 행 추가, 행 삭제, 새로고침 버튼을 같은 행에 배치
        col1_1, col1_2, col1_3 = st.columns([0.33, 0.33, 0.33])
        with col1_1:
            if st.button("행 추가"):
                rows.append({"제목": "", "요청": "", "데이터": "", "checked": True})  # 새 행 추가 및 자동 체크
                st.session_state['rows'] = rows  # 세션 상태 업데이트
        with col1_2:
            if st.button("행 삭제"):
                if checked_rows:
                    st.session_state['rows'] = [row for idx, row in enumerate(rows) if idx not in checked_rows]  # 체크된 행 삭제
                    st.success(f"체크된 {len(checked_rows)}개의 요청사항이 삭제되었습니다.")
                else:
                    st.warning("삭제할 요청사항을 선택해주세요.")
        with col1_3:
            if st.button("새로고침"):
                st.session_state['rows'] = st.session_state['rows']  # 단순히 상태 업데이트로 새로고침 효과

    # 2. 파일 업로드 (세로 길이 20% 고정)
    st.subheader("2. 파일 업로드")
    with st.expander("파일 업로드", expanded=True):
        uploaded_files = st.file_uploader("파일을 여러 개 드래그 앤 드롭하여 업로드하세요.", accept_multiple_files=True)

        if uploaded_files and st.session_state['github_repo'] and st.session_state['github_token']:
            for uploaded_file in uploaded_files:
                # 파일을 바이트 형식으로 읽어들임
                file_content = uploaded_file.read()
                file_name = uploaded_file.name
                folder_name = 'uploadFiles'

                # 기존 파일이 있는지 확인
                sha = get_file_sha(st.session_state['github_repo'], f"{folder_name}/{file_name}", st.session_state['github_token'], branch=st.session_state['github_branch'])

                if sha:
                    # 덮어쓰기 확인
                    if st.checkbox(f"'{file_name}' 파일이 이미 존재합니다. 덮어쓰시겠습니까?", key=f"overwrite_{file_name}"):
                        upload_file_to_github(st.session_state['github_repo'], folder_name, file_name, file_content, st.session_state['github_token'], branch=st.session_state['github_branch'], sha=sha)
                else:
                    # 새 파일 업로드
                    upload_file_to_github(st.session_state['github_repo'], folder_name, file_name, file_content, st.session_state['github_token'])

    # 5. 참고 템플릿 미리보기 (세로 길이 30% 고정)
    st.subheader("5. 참고 템플릿 미리보기")
    with st.expander("참고 템플릿 미리보기", expanded=True):
        selected_template_file = st.selectbox("템플릿 파일 선택", options=["Template1", "Template2", "Template3"])
        if st.button("선택"):
            st.success(f"선택한 템플릿: {selected_template_file}")

# 2 프레임 (10%)
with col2:
    st.subheader("3. 실행")
    if st.button("실행"):
        if st.session_state['openai_api_key'] == "":
            st.error("OpenAI API 키를 입력해야 실행할 수 있습니다.")
        else:
            llm_results = {}
            for idx, row in enumerate(st.session_state['rows']):
                prompt = [
                    {"role": "system", "content": "다음 파일을 분석하여 보고서를 작성하세요."},
                    {"role": "user", "content": f"보고서 제목 : '{row['제목']}'\n요청 문구 : '{row['요청']}'\n데이터 전달 : '{row['데이터']}'"}
                ]
                llm_response = send_to_llm(prompt, st.session_state['openai_api_key'])
                
                if llm_response:
                    llm_results[idx] = llm_response
                else:
                    llm_results[idx] = "LLM 응답을 받지 못했습니다."

            st.success("LLM 요청이 완료되었습니다.")

# 3 프레임 (49%) - 4. 결과 보고서 세로 70% 고정
with col3:
    st.subheader("4. 결과 보고서")

    # 고정된 70% 높이로 설정하고 스크롤 영역 구현
    st.markdown(
        """
        <style>
        div[data-testid="stExpander"] > div[role="group"] {
            height: 70vh;
            overflow-y: auto;
        }
        </style>
        """, unsafe_allow_html=True
    )

    with st.expander("결과 보고서", expanded=True):
        if 'llm_results' in locals() and llm_results:
            for idx, result in llm_results.items():
                st.text(f"제목: {st.session_state['rows'][idx]['제목']}")
                st.text(f"LLM 응답 결과:\n{result}")
        else:
            st.text("결과가 없습니다.")

# 6. 저장과 7. 불러오기 (분리된 영역)
with col3:
    st.subheader("6. 저장 및 7. 불러오기")

    # 6. 저장과 7. 불러오기 (각각 분리)
    col3_1, col3_2 = st.columns([0.5, 0.5])

    with col3_1:
        st.subheader("6. 저장")
        save_path = st.text_input("저장할 파일명 입력")
        if st.button("저장") and save_path:
            df = pd.DataFrame(st.session_state['rows'])
            df.to_csv(f"{save_path}.csv")
            st.success(f"{save_path}.csv 파일로 저장되었습니다.")

    with col3_2:
        st.subheader("7. 불러오기")
        uploaded_save_file = st.file_uploader("저장된 CSV 파일 불러오기", type=["csv"])
        if uploaded_save_file is not None:
            loaded_data = pd.read_csv(uploaded_save_file)
            st.dataframe(loaded_data)
            st.success("데이터가 불러와졌습니다.")

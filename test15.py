import streamlit as st
import pandas as pd
import requests
import os
import urllib.parse  # URL 인코딩을 위한 라이브러리
import base64  # base64 인코딩 및 복호화를 위한 라이브러리
import json

# 페이지 설정
st.set_page_config(layout="wide")  # 페이지 가로길이를 모니터 전체 해상도로 설정

# JSON 데이터 (github_token 삭제됨)
json_data = '''
{
    "github_repo": "soryhon/hanachatbot",
    "github_branch": "main"
}
'''

# JSON 데이터를 파싱하여 세션 상태에 저장
data = json.loads(json_data)

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

# GitHub에서 파일의 SHA 값을 가져오는 함수
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

# GitHub 파일의 서버 경로를 생성하는 함수
def get_file_server_path(repo, branch, file_path):
    server_base_path = "/mnt/data/github_files"  # 서버에 GitHub 파일이 저장된 기본 경로
    return os.path.join(server_base_path, file_path)

# 파일 미리보기 함수 (화면에 직접 출력)
def preview_file(file_path):
    try:
        file_extension = file_path.split('.')[-1].lower()
        # URL 인코딩 적용 (한글 파일 경로 문제 해결)
        encoded_file_path = urllib.parse.quote(file_path)

        # 경로 출력하여 확인
        st.write(f"미리보기 경로: {file_path}")

        if file_extension in ['png', 'jpg', 'jpeg']:
            st.image(file_path, caption="이미지 미리보기", use_column_width=True)
        elif file_extension == 'pdf':
            st.write(f"[PDF 보기]({file_path}) (PDF 파일은 직접 미리보기가 지원되지 않습니다.)", unsafe_allow_html=True)
        elif file_extension == 'html':
            st.markdown(f"[HTML 보기]({file_path})", unsafe_allow_html=True)
        else:
            st.warning("미리보기가 지원되지 않는 파일 형식입니다.")
    except Exception as e:
        st.error(f"파일 미리보기 오류: {e}")

# 세션 상태 초기화
if 'github_repo' not in st.session_state:
    st.session_state['github_repo'] = data.get('github_repo', "")
if 'github_token' not in st.session_state:
    st.session_state['github_token'] = ""  # GitHub API 토큰은 사용자가 입력하도록 수정
if 'github_branch' not in st.session_state:
    st.session_state['github_branch'] = data.get('github_branch', "main")
if 'openai_api_key' not in st.session_state:
    st.session_state['openai_api_key'] = ""
if 'github_saved' not in st.session_state:
    st.session_state['github_saved'] = False
if 'openai_saved' not in st.session_state:
    st.session_state['openai_saved'] = False
if 'show_info' not in st.session_state:
    st.session_state['show_info'] = True  # 기본적으로 정보 입력 화면을 표시
if 'rows' not in st.session_state:
    st.session_state['rows'] = [{"제목": "", "요청": "", "데이터": "", "checked": False}]  # 기본 행
if 'template_file_path' not in st.session_state:
    st.session_state['template_file_path'] = ""  # 탬플릿 파일 경로를 저장

# 저장 정보 숨기기/보이기 기능
def toggle_visibility():
    st.session_state['show_info'] = not st.session_state['show_info']

# GitHub 정보와 OpenAI 정보 모두 저장되었는지 확인
both_saved = st.session_state['github_saved'] and st.session_state['openai_saved']

# GitHub 및 OpenAI 정보 입력 폼
if not both_saved or st.session_state['show_info']:
    st.subheader("GitHub 저장소 정보 및 OpenAI API 키 입력")

    col_a, col_b = st.columns(2)

    # GitHub 정보 입력 영역
    with col_a:
        st.subheader("GitHub 정보 입력")
        github_repo = st.text_input("GitHub 저장소 경로 (예: username/repo)", value=st.session_state['github_repo'])
        github_token = st.text_input("GitHub API 토큰 입력", type="password")
        github_branch = st.text_input("브랜치 이름 (예: main 또는 master)", value=st.session_state['github_branch'])
        
        if st.button("GitHub 정보 저장"):
            if github_repo and github_token and github_branch:
                st.session_state['github_repo'] = github_repo
                st.session_state['github_token'] = github_token
                st.session_state['github_branch'] = github_branch
                st.session_state['github_saved'] = True
                st.success(f"GitHub 정보가 저장되었습니다!\nRepo: {github_repo}, Branch: {github_branch}")
            else:
                st.error("모든 GitHub 정보를 입력해주세요.")

    # OpenAI API 키 입력 영역
    with col_b:
        st.subheader("OpenAI API 키 입력")
        openai_api_key = st.text_input("OpenAI API 키를 입력하세요.", type="password", value=st.session_state['openai_api_key'])
        
        if st.button("OpenAI API 키 저장"):
            if openai_api_key:
                st.session_state['openai_api_key'] = openai_api_key
                st.session_state['openai_saved'] = True
                st.success("OpenAI API 키가 저장되었습니다.")
            else:
                st.error("OpenAI API 키를 입력해주세요.")

# "저장 정보 보기"와 "저장 정보 숨기기" 버튼 처리
if both_saved:
    if st.session_state['show_info']:
        if st.button("저장 정보 숨기기"):
            toggle_visibility()
    else:
        if st.button("저장 정보 보기"):
            toggle_visibility()

# 3개의 프레임 나누기
col1, col2, col3 = st.columns([0.39, 0.10, 0.49])

# 1 프레임 (39%) - 스크롤 가능한 영역으로 구성, 세로 길이 50% 고정
with col1:
    st.subheader("1. 작성 보고서 요청사항")

    with st.expander("요청사항 리스트", expanded=True):
        df = pd.DataFrame(columns=["제목", "요청", "데이터"])
        rows = st.session_state['rows']
        checked_rows = []

        for idx, row in enumerate(rows):
            with st.container():
                row_checked = st.checkbox(f"요청사항 {idx+1}", key=f"row_checked_{idx}", value=row.get("checked", False))
                row['제목'] = st.text_input(f"제목 (요청사항 {idx+1})", row['제목'])
                row['요청'] = st.text_input(f"요청 (요청사항 {idx+1})", row['요청'])

                if row_checked:
                    checked_rows.append(idx)
                    row["checked"] = True
                else:
                    row["checked"] = False

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
                    server_path = get_file_server_path(st.session_state['github_repo'], st.session_state['github_branch'], selected_file)
                    rows[idx]['데이터'] = server_path
                    st.success(f"선택한 파일: {selected_file}\n서버 경로: {server_path}")

                st.text_input(f"데이터 (요청사항 {idx+1})", row['데이터'], disabled=True, key=f"file_path_{idx}")

        col1_1, col1_2, col1_3 = st.columns([0.33, 0.33, 0.33])
        with col1_1:
            if st.button("행 추가"):
                rows.append({"제목": "", "요청": "", "데이터": "", "checked": True})
                st.session_state['rows'] = rows
        with col1_2:
            if st.button("행 삭제"):
                if checked_rows:
                    st.session_state['rows'] = [row for idx, row in enumerate(rows) if idx not in checked_rows]
                    st.success(f"체크된 {len(checked_rows)}개의 요청사항이 삭제되었습니다.")
                else:
                    st.warning("삭제할 요청사항을 선택해주세요.")
        with col1_3:
            if st.button("새로고침"):
                st.session_state['rows'] = st.session_state['rows']

    # 2. 파일 업로드 (세로 길이 20% 고정)
    st.subheader("2. 파일 업로드")
    with st.expander("파일 업로드", expanded=True):
        uploaded_files = st.file_uploader("파일을 여러 개 드래그 앤 드롭하여 업로드하세요.", accept_multiple_files=True)

        if uploaded_files and st.session_state['github_repo'] and st.session_state['github_token']:
            for uploaded_file in uploaded_files:
                file_content = uploaded_file.read()
                file_name = uploaded_file.name
                folder_name = 'uploadFiles'

                sha = get_file_sha(st.session_state['github_repo'], f"{folder_name}/{file_name}", st.session_state['github_token'], branch=st.session_state['github_branch'])

                if sha:
                    if st.checkbox(f"'{file_name}' 파일이 이미 존재합니다. 덮어쓰시겠습니까?", key=f"overwrite_{file_name}"):
                        upload_file_to_github(st.session_state['github_repo'], folder_name, file_name, file_content, st.session_state['github_token'], branch=st.session_state['github_branch'], sha=sha)
                else:
                    upload_file_to_github(st.session_state['github_repo'], folder_name, file_name, file_content, st.session_state['github_token'])

    # 5. 참고 탬플릿 미리보기 (세로 길이 30% 고정)
    st.subheader("5. 참고 탬플릿 미리보기")
    with st.expander("참고 탬플릿 미리보기", expanded=True):
        col5_1, col5_2 = st.columns([0.8, 0.2])
        with col5_1:
            file_path = st.text_input("탬플릿 파일 경로", value=st.session_state['template_file_path'])
        with col5_2:
            if st.button("미리보기"):
                if file_path:
                    preview_file(file_path)  # 미리보기
                else:
                    st.warning("파일 경로를 입력하세요.")

        template_folder = "templateFiles"
        if st.session_state['github_repo'] and st.session_state['github_token']:
            template_files = get_github_files(st.session_state['github_repo'], st.session_state['github_token'], folder_name=template_folder, branch=st.session_state['github_branch'])

        selected_template_file = st.selectbox("탬플릿 파일 선택", template_files)

        if st.button("파일 선택"):
            server_template_path = get_file_server_path(st.session_state['github_repo'], st.session_state['github_branch'], selected_template_file)
            st.session_state['template_file_path'] = server_template_path
            st.success(f"선택한 파일 경로: {server_template_path}")

        # GitHub에 탬플릿 파일 업로드
        uploaded_template_files = st.file_uploader("탬플릿 파일 업로드", accept_multiple_files=True, type=["png", "jpg", "pdf", "html"])

        if uploaded_template_files:
            for template_file in uploaded_template_files:
                template_file_content = template_file.read()
                template_file_name = template_file.name
                folder_name = 'templateFiles'

                sha = get_file_sha(st.session_state['github_repo'], f"{folder_name}/{template_file_name}", st.session_state['github_token'], branch=st.session_state['github_branch'])

                if sha:
                    if st.checkbox(f"'{template_file_name}' 파일이 이미 존재합니다. 덮어쓰시겠습니까?", key=f"overwrite_{template_file_name}"):
                        upload_file_to_github(st.session_state['github_repo'], folder_name, template_file_name, template_file_content, st.session_state['github_token'], branch=st.session_state['github_branch'], sha=sha)
                else:
                    upload_file_to_github(st.session_state['github_repo'], folder_name, template_file_name, template_file_content, st.session_state['github_token'])

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

import os
import openai
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain import LLMChain
import requests
import PyPDF2
import pandas as pd
import docx
import pptx
from PIL import Image
from io import BytesIO
import base64
import urllib.parse
from openai.error import RateLimitError
from langchain.chat_models import ChatOpenAI
import time
import json

# 전역변수로 프롬프트 저장
global_generated_prompt = []

# GitHub 정보 및 OpenAI API 키 자동 설정 또는 입력창을 통해 설정
def load_env_info():
    json_data = '''
    {
        "github_repo": "soryhon/hanachatbot",
        "github_branch": "main"
    }
    '''
    
    # JSON 데이터에서 정보 추출
    github_info = json.loads(json_data)
    github_repo = github_info['github_repo']
    github_branch = github_info['github_branch']
    
    # 환경 변수에서 GitHub Token 및 OpenAI API Key 가져오기
    github_token = os.getenv("GITHUB_TOKEN")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    github_set = False
    openai_set = False

    # 입력창을 가로로 배치 (각각 50%의 너비)
    col1, col2 = st.columns(2)

    with col1:
        if not github_token:
            github_token = st.text_input("GitHub Token을 입력하세요", type="password", key="github_token_input")
        else:
            github_set = True
            st.success("GitHub 정보가 자동으로 설정되었습니다!")
        st.session_state["github_token"] = github_token

    with col2:
        if not openai_api_key:
            openai_api_key = st.text_input("OpenAI API 키를 입력하세요", type="password", key="openai_api_key_input")
        else:
            openai_set = True
            st.success("OpenAI API 키가 자동으로 설정되었습니다!")
        st.session_state["openai_api_key"] = openai_api_key

    # GitHub 저장소 정보 세션에 저장
    st.session_state["github_repo"] = github_repo
    st.session_state["github_branch"] = github_branch

    # GitHub 정보가 설정되었는지 확인하고 세션 상태 반영
    return github_set

# GitHub에 폴더가 존재하는지 확인하고 없으면 생성하는 함수
def create_github_folder_if_not_exists(repo, folder_name, token, branch='main'):
    url = f"https://api.github.com/repos/{repo}/contents/{folder_name}?ref={branch}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 404:
        # 폴더가 존재하지 않으므로 생성
        st.warning(f"'{folder_name}' 폴더가 존재하지 않아 생성 중입니다.")
        create_folder_url = f"https://api.github.com/repos/{repo}/contents/{folder_name}"
        data = {
            "message": f"Create {folder_name} folder",
            "content": base64.b64encode(b'').decode('utf-8'),  # 빈 파일로 폴더 생성
            "branch": branch
        }
        requests.put(create_folder_url, json=data, headers=headers)
        st.success(f"'{folder_name}' 폴더가 성공적으로 생성되었습니다.")

# GitHub API 요청을 처리하는 함수 (파일 목록을 가져옴)
def get_github_files(repo, branch, token, folder_name='uploadFiles'):
    create_github_folder_if_not_exists(repo, folder_name, token, branch)  # 폴더가 없으면 생성
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        files = [item['path'] for item in response.json().get('tree', []) if item['type'] == 'blob' and item['path'].startswith(folder_name)]
        return files
    else:
        st.error("GitHub 파일 목록을 가져오지 못했습니다. 저장소 정보나 토큰을 확인하세요.")
        return []

# 파일에서 데이터를 추출하고 요청사항 리스트에서 선택한 엑셀 파일의 시트를 보여주는 로직
def handle_file_selection(file_path, file_content, file_type, idx):
    if file_type == 'xlsx':
        excel_data = pd.ExcelFile(file_content)
        sheet_count = len(excel_data.sheet_names)
        
        # 엑셀 파일 선택 시 바로 1번 시트 데이터를 가져오도록 설정
        file_data = handle_sheet_selection(file_content, sheet_count, idx)
        
        if file_data is not None and not file_data.empty:
            return file_data
        else:
            st.error("선택한 시트에 데이터가 없습니다.")
            return None
    else:
        return extract_data_from_file(file_content, file_type)

# 요청사항 리스트
def display_rows():
    rows = st.session_state['rows']
    checked_rows = []

    for idx, row in enumerate(rows):
        with st.container():
            col1, col2 = st.columns([0.05, 0.95])  # 체크박스와 제목 부분을 가로로 나눔
            with col1:
                row_checked = st.checkbox("", key=f"row_checked_{idx}", value=row.get("checked", False))  # 체크박스만 추가
            with col2:
                st.markdown(f"#### 요청사항 {idx+1}")  # 요청사항 타이틀과 나머지 UI 요소들 배치

            # 제목 입력창에 포커스를 설정하기 위한 key 사용
            row['제목'] = st.text_input(f"제목 (요청사항 {idx+1})", row['제목'], key=f"title_{idx}", placeholder="여기에 제목 입력", help="제목을 입력하세요")
            row['요청'] = st.text_area(f"요청 (요청사항 {idx+1})", row['요청'], key=f"request_{idx}")

            # 파일 선택과 데이터 처리 관련
            file_list = ['파일을 선택하세요.']
            if st.session_state.get('github_token') and st.session_state.get('github_repo'):
                file_list += get_github_files(st.session_state['github_repo'], st.session_state['github_branch'], st.session_state['github_token'])

            selected_file = st.selectbox(f"파일 선택 (요청사항 {idx+1})", options=file_list, key=f"file_select_{idx}")

            if selected_file != '파일을 선택하세요.':
                file_path = selected_file
                file_content = get_file_from_github(st.session_state["github_repo"], st.session_state["github_branch"], file_path, st.session_state["github_token"])
                
                if file_content:
                    file_type = file_path.split('.')[-1].lower()

                    if file_type not in ['xlsx', 'pptx', 'docx', 'csv', 'png', 'jpg', 'jpeg']:
                        st.error(f"지원하지 않는 파일입니다: {file_path}")
                        row['데이터'] = ""
                    else:
                        # 파일 데이터 처리
                        file_data = handle_file_selection(file_path, file_content, file_type, idx)
                        if file_data is not None and not file_data.empty:
                            row['파일'] = f"/{st.session_state['github_repo']}/{st.session_state['github_branch']}/{selected_file}"
                            row['데이터'] = file_data
                        else:
                            st.error(f"{selected_file} 파일의 데이터를 처리하지 못했습니다.")
                else:
                    st.error(f"{selected_file} 파일을 GitHub에서 불러오지 못했습니다.")
                
            st.text_input(f"파일 경로 (요청사항 {idx+1})", row['파일'], disabled=True, key=f"file_{idx}")

        if row_checked:
            checked_rows.append(idx)

    return checked_rows

# GitHub 정보가 있는지 확인하고 파일 업로드 객체를 출력
github_info_loaded = load_env_info()

# 업로드 가능한 파일 크기 제한 (100MB)
MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# 2 프레임: 파일 업로드
st.subheader("1. 파일 업로드")

# 지원되는 파일 형식 리스트
supported_file_types = ['xlsx', 'pptx', 'docx', 'csv', 'png', 'jpg', 'jpeg']

if github_info_loaded:
    with st.expander("파일 업로드", expanded=True):
        uploaded_files = st.file_uploader("파일을 여러 개 드래그 앤 드롭하여 업로드하세요. (최대 100MB)", accept_multiple_files=True)

        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_type = uploaded_file.name.split('.')[-1].lower()

                if file_type not in supported_file_types:
                    st.error(f"지원하지 않는 파일입니다: {uploaded_file.name}")
                    continue

                if uploaded_file.size > MAX_FILE_SIZE_BYTES:
                    st.warning(f"'{uploaded_file.name}' 파일은 {MAX_FILE_SIZE_MB}MB 제한을 초과했습니다. 파일 크기를 줄이거나 GitHub에 직접 푸시하세요.")
                else:
                    file_content = uploaded_file.read()
                    file_name = uploaded_file.name
                    folder_name = 'uploadFiles'

                    upload_file_to_github(st.session_state['github_repo'], folder_name, file_name, file_content, st.session_state['github_token'])
                    st.success(f"'{file_name}' 파일이 성공적으로 업로드되었습니다.")
else:
    st.warning("GitHub 정보가 저장되기 전에는 파일 업로드를 할 수 없습니다. 먼저 GitHub 정보를 입력해 주세요.")

# 3 프레임: 작성 보고서 요청사항 및 실행 버튼
st.subheader("3. 작성 보고서 요청사항 및 실행 버튼")

# 요청사항 리스트
with st.expander("요청사항 리스트", expanded=True):
    if 'rows' not in st.session_state:
        st.session_state['rows'] = [{"제목": "", "요청": "", "파일": "", "데이터": "", "checked": False}]

    # 요청사항 리스트를 보여줌
    checked_rows = display_rows()

    # 행 추가, 행 삭제, 새로고침 버튼을 가로로 배치, 가로길이 30%로 설정, 버튼 길이 60px로 설정
    col1, col2, col3 = st.columns([0.3, 0.3, 0.3])

    with col1:
        if st.button("행 추가", key="add_row"):
            new_row = {"제목": "", "요청": "", "파일": "", "데이터": "", "checked": False}
            st.session_state['rows'].append(new_row)

    with col2:
        if st.button("행 삭제", key="delete_row"):
            if checked_rows:
                st.session_state['rows'] = [row for idx, row in enumerate(st.session_state['rows']) if idx not in checked_rows]
                st.success(f"체크된 {len(checked_rows)}개의 요청사항이 삭제되었습니다.")
            else:
                st.warning("삭제할 요청사항을 선택해주세요.")

    with col3:
        if st.button("새로고침", key="refresh_page"):
            st.info("새로고침 하였습니다.")

# 보고서 작성 버튼을 따로 위에 위치
if st.button("보고서 작성", key="generate_report"):
    if not st.session_state.get("openai_api_key"):
        st.error("먼저 OpenAI API 키를 입력하고 저장하세요!")
    elif not st.session_state['rows'] or all(not row["제목"] or not row["요청"] or not row["데이터"] for row in st.session_state['rows']):
        st.error("요청사항의 제목, 요청, 파일을 모두 입력해야 합니다!")
    else:
        titles = [row['제목'] for row in st.session_state['rows']]
        requests = [row['요청'] for row in st.session_state['rows']]
        file_data_list = [row['데이터'] for row in st.session_state['rows']]

        responses = run_llm_with_file_and_prompt(
            st.session_state["openai_api_key"], 
            titles, 
            requests, 
            file_data_list
        )
        st.session_state["response"] = responses

# 양식 저장, 양식 불러오기 버튼을 같은 행에 배치, 가로 길이 50%, 버튼 길이 100px로 설정
col1, col2 = st.columns([0.5, 0.5])

with col1:
    if st.button("양식 저장", key="save_template", use_container_width=True):
        st.success("양식이 저장되었습니다.")

with col2:
    if st.button("양식 불러오기", key="load_template", use_container_width=True):
        st.success("양식이 불러와졌습니다.")

# HTML 변환 함수 (NaN 처리 포함)
def convert_data_to_html(file_data, title, idx):
    # NaN을 공백으로 대체
    file_data = file_data.fillna("")

    html_content = f"<h3>{idx + 1}. {title}</h3>"
    html_content += "<table style='border-collapse: collapse;'>"

    for i, row in file_data.iterrows():
        html_content += "<tr>"
        for j, col in enumerate(row):
            # 줄바꿈을 <br>로 변환
            col = str(col).replace("\n", "<br>")
            html_content += f"<td style='border: 1px solid black;'>{col}</td>"
        html_content += "</tr>"

    html_content += "</table>"
    return html_content

# HTML 데이터로 여러 요청사항 리스트 병합
def generate_html_report(rows):
    html_report = ""
    for idx, row in enumerate(rows):
        if row["데이터"] is not None and isinstance(row["데이터"], pd.DataFrame):
            html_report += convert_data_to_html(row["데이터"], row["제목"], idx)
    return html_report

# 4 프레임: 결과 보고서
st.subheader("4. 결과 보고서")

# 결과 보고서 데이터를 HTML으로 변환
st.write("결과 보고서 보기")
# HTML로 변환한 엑셀 시트 데이터를 화면에 출력 (프롬프트 아래에 위치)
html_report = generate_html_report(st.session_state['rows'])
if html_report:
    st.components.v1.html(html_report, height=1024, scrolling=True)

# 전달된 프롬프트
st.text_area("전달된 프롬프트:", value="\n\n".join(global_generated_prompt), height=150)

# LLM 응답 보기
st.write("LLM 응답 보기")
if "response" in st.session_state:
    for idx, response in enumerate(st.session_state["response"]):
        st.text_area(f"응답 {idx+1}:", value=response, height=300)
        
        st.components.v1.html(response, height=600, scrolling=True)

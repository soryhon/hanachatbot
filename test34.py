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
import openpyxl  # 셀 서식 정보를 추출하기 위해 추가

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

# GitHub에서 파일을 다운로드하는 함수
def get_file_from_github(repo, branch, filepath, token):
    encoded_filepath = urllib.parse.quote(filepath)  # URL 인코딩 추가
    url = f"https://api.github.com/repos/{repo}/contents/{encoded_filepath}?ref={branch}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return BytesIO(requests.get(response.json()['download_url']).content)
    else:
        st.error(f"{filepath} 파일을 가져오지 못했습니다. 상태 코드: {response.status_code}")
        return None

# 셀의 테두리 스타일을 HTML로 변환하는 함수
def get_border_style(cell):
    if cell.border:
        border = cell.border
        styles = []
        for side in ['left', 'right', 'top', 'bottom']:
            side_border = getattr(border, side)
            if side_border.style:
                styles.append(f'border-{side}: 1px solid black;')
        return ' '.join(styles)
    return ''

# 셀의 서식 정보를 추출하여 HTML로 변환하는 함수
def convert_data_to_html_with_formatting(file_content, sheet_name):
    workbook = openpyxl.load_workbook(file_content, data_only=True)
    sheet = workbook[sheet_name]
    html_content = "<table style='border-collapse: collapse;'>"
    
    for row in sheet.iter_rows():
        html_content += "<tr>"
        for cell in row:
            value = cell.value if cell.value is not None else ""
            # 셀의 서식 정보를 기반으로 테두리 스타일 적용
            border_style = get_border_style(cell)
            html_content += f"<td style='{border_style} padding: 5px;'>{value}</td>"
        html_content += "</tr>"
    
    html_content += "</table>"
    return html_content

# 엑셀 파일에서 시트 가져오기 및 데이터 추출
def extract_sheets_from_excel_with_formatting(file_content, selected_sheets):
    try:
        workbook = openpyxl.load_workbook(file_content, data_only=True)
        all_sheets = workbook.sheetnames
        
        # 사용자가 선택한 시트를 가져옴
        if selected_sheets == 'all':
            selected_sheets = all_sheets
        else:
            selected_sheets = [all_sheets[int(i)-1] for i in selected_sheets if int(i) <= len(all_sheets)]
        
        # 선택한 시트의 데이터를 HTML로 변환하여 반환
        html_data = ""
        for sheet in selected_sheets:
            html_data += convert_data_to_html_with_formatting(file_content, sheet)
        
        return html_data
    except Exception as e:
        st.error(f"엑셀 파일의 시트 데이터를 추출하는 중에 오류가 발생했습니다: {str(e)}")
        return None

# 시트 선택 로직 추가 (엑셀 파일 선택 시 기본적으로 1번 시트 데이터를 바로 가져오도록 설정)
def handle_sheet_selection_with_formatting(file_content, sheet_count, idx):
    # 시트 관련 UI를 표시
    col1, col2, col3, col4 = st.columns([0.25, 0.25, 0.25, 0.25])
    
    with col1:
        st.text_input(f"시트 갯수 ({idx})", value=f"{sheet_count}개", disabled=True)  # 시트 갯수 표시 (비활성화)
    
    with col2:
        all_sheets_checkbox = st.checkbox(f'전체 ({idx})', value=False, key=f"all_sheets_{idx}")

    with col3:
        # 시트 선택 텍스트 입력창 (전체 선택 시 비활성화, 기본값 1)
        sheet_selection = st.text_input(f"시트 선택(예: 1-3, 5) ({idx})", value="1", disabled=all_sheets_checkbox, key=f"sheet_selection_{idx}")

    # 전체 체크박스 체크 시 시트 선택 입력창에 1-총 시트 개수 값 입력
    if all_sheets_checkbox:
        sheet_selection = f"1-{sheet_count}"
        st.session_state[f'sheet_selection_{idx}'] = sheet_selection

    with col4:
        # 시트 선택 버튼
        select_button = st.button(f"선택 ({idx})")

    # 시트 선택 버튼이 눌렸거나 기본 값이 있을 경우 바로 데이터 가져오기
    if select_button or sheet_selection == "1":
        selected_sheets = parse_sheet_selection(sheet_selection, sheet_count)
        if selected_sheets:
            html_data = extract_sheets_from_excel_with_formatting(file_content, selected_sheets)
            return html_data
        else:
            st.error(f"선택한 시트가 잘못되었습니다. ({idx})")
    return None

# 시트 선택 입력값을 분석하는 함수
def parse_sheet_selection(selection, sheet_count):
    selected_sheets = []

    try:
        if '-' in selection:
            start, end = map(int, selection.split('-'))
            if start <= end <= sheet_count:
                selected_sheets.extend(list(range(start, end+1)))
        elif ',' in selection:
            selected_sheets = [int(i) for i in selection.split(',') if 1 <= int(i) <= sheet_count]
        else:
            selected_sheets = [int(selection)] if 1 <= int(selection) <= sheet_count else []
    except ValueError:
        st.error("잘못된 시트 선택 입력입니다.")
        return None

    return selected_sheets

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

                    sha = get_file_sha(st.session_state['github_repo'], f"{folder_name}/{file_name}", st.session_state['github_token'], branch=st.session_state['github_branch'])

                    if sha:
                        st.warning(f"'{file_name}' 파일이 이미 존재합니다. 덮어쓰시겠습니까?")
                        col1, col2 = st.columns(2)

                        with col1:
                            if st.button(f"'{file_name}' 덮어쓰기", key=f"overwrite_{file_name}"):
                                upload_file_to_github(st.session_state['github_repo'], folder_name, file_name, file_content, st.session_state['github_token'], branch=st.session_state['github_branch'], sha=sha)
                                st.success(f"'{file_name}' 파일이 성공적으로 덮어쓰기 되었습니다.")
                                uploaded_files = None
                                break

                        with col2:
                            if st.button("취소", key=f"cancel_{file_name}"):
                                st.info("덮어쓰기가 취소되었습니다.")
                                uploaded_files = None
                                break
                    else:
                        upload_file_to_github(st.session_state['github_repo'], folder_name, file_name, file_content, st.session_state['github_token'])
                        st.success(f"'{file_name}' 파일이 성공적으로 업로드되었습니다.")
                        
                        # 엑셀 파일 선택 시 기본적으로 1번 시트 데이터를 가져오도록 함
                        if file_type == 'xlsx':
                            # 세션에 파일 데이터 저장
                            st.session_state['file_content'] = file_content
                            st.session_state['sheet_count'] = 1  # 기본값 설정
                        uploaded_files = None
else:
    st.warning("GitHub 정보가 저장되기 전에는 파일 업로드를 할 수 없습니다. 먼저 GitHub 정보를 입력해 주세요.")

# 3 프레임: 작성 보고서 요청사항 및 실행 버튼
st.subheader("3. 작성 보고서 요청사항 및 실행 버튼")

# 요청사항 리스트
with st.expander("요청사항 리스트", expanded=True):
    if 'rows' not in st.session_state:
        st.session_state['rows'] = [{"제목": "", "요청": "", "파일": "", "데이터": "", "checked": False}]

    rows = st.session_state['rows']
    checked_rows = []

    for idx, row in enumerate(rows):
        with st.container():
            col1, col2 = st.columns([0.05, 0.95])  # 체크박스와 제목 부분을 가로로 나눔
            with col1:
                row_checked = st.checkbox("", key=f"row_checked_{idx}", value=row.get("checked", False))  # 체크박스만 추가
            with col2:
                st.markdown(f"#### 요청사항 {idx+1}")  # 요청사항 타이틀과 나머지 UI 요소들 배치

            row['제목'] = st.text_input(f"제목 (요청사항 {idx+1})", row['제목'], key=f"title_{idx}")
            row['요청'] = st.text_area(f"요청 (요청사항 {idx+1})", row['요청'], key=f"request_{idx}")

            file_list = ['파일을 선택하세요.']
            if st.session_state.get('github_token') and st.session_state.get('github_repo'):
                file_list += get_github_files(st.session_state['github_repo'], st.session_state['github_branch'], st.session_state['github_token'])

            selected_file = st.selectbox(f"파일 선택 (요청사항 {idx+1})", options=file_list, key=f"file_select_{idx}")

            if selected_file != '파일을 선택하세요.':
                file_path = selected_file
                file_content = get_file_from_github(st.session_state["github_repo"], st.session_state["github_branch"], file_path, st.session_state["github_token"])
                
                if file_content:
                    file_type = file_path.split('.')[-1].lower()

                    # 파일 형식 검증 (지원되는 파일만 처리)
                    if file_type not in supported_file_types:
                        st.error(f"지원하지 않는 파일입니다: {file_path}")
                        row['데이터'] = ""
                    else:
                        # 엑셀 파일인 경우 기본적으로 1번 시트 데이터를 가져오도록 설정
                        file_data = handle_file_selection(file_path, file_content, file_type, idx)
                        
                        if file_data is not None and not file_data.empty:  # 수정된 부분
                            row['파일'] = f"/{st.session_state['github_repo']}/{st.session_state['github_branch']}/{selected_file}"
                            row['데이터'] = file_data
                        else:
                            st.error(f"{selected_file} 파일의 데이터를 처리하지 못했습니다.")
                else:
                    st.error(f"{selected_file} 파일을 GitHub에서 불러오지 못했습니다.")
                
            st.text_input(f"파일 경로 (요청사항 {idx+1})", row['파일'], disabled=True, key=f"file_{idx}")

        if row_checked:
            checked_rows.append(idx)

    # 행 추가 및 삭제 버튼을 가로로 배치하고 가로 길이를 100px로 설정
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("행 추가", key="add_row", help="새 행을 추가합니다.", use_container_width=True):
            new_row = {"제목": "", "요청": "", "파일": "", "데이터": "", "checked": False}
            st.session_state['rows'].append(new_row)
            # 행추가 후 새로고침 호출
            st.experimental_rerun()

    with col2:
        if st.button("행 삭제", key="delete_row", help="선택된 행을 삭제합니다.", use_container_width=True):
            if checked_rows:
                st.session_state['rows'] = [row for idx, row in enumerate(rows) if idx not in checked_rows]
                st.success(f"체크된 {len(checked_rows)}개의 요청사항이 삭제되었습니다.")
            else:
                st.warning("삭제할 요청사항을 선택해주세요.")

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

# 양식 저장, 양식 불러오기, 새로고침 버튼을 같은 행에 배치
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("양식 저장", key="save_template"):
        st.success("양식이 저장되었습니다.")

with col2:
    if st.button("양식 불러오기", key="load_template"):
        st.success("양식이 불러와졌습니다.")

with col3:
    if st.button("새로고침", key="refresh_page"):
        st.experimental_rerun()

# 4 프레임: 결과 보고서
st.subheader("4. 결과 보고서")

# 세션에서 파일 데이터와 시트 개수를 가져옴
if 'file_content' in st.session_state and 'sheet_count' in st.session_state:
    html_report = handle_sheet_selection_with_formatting(st.session_state['file_content'], st.session_state['sheet_count'], 0)
    if html_report:
        st.components.v1.html(html_report, height=1024, scrolling=True)
else:
    st.error("파일 데이터 또는 시트 정보가 없습니다. 파일을 업로드하고 시트를 선택하세요.")

# 전달된 프롬프트
st.text_area("전달된 프롬프트:", value="\n\n".join(global_generated_prompt), height=150)

# LLM 응답 보기
st.write("LLM 응답 보기")
if "response" in st.session_state:
    for idx, response in enumerate(st.session_state["response"]):
        st.text_area(f"응답 {idx+1}:", value=response, height=300)
        
        st.components.v1.html(response, height=600, scrolling=True)

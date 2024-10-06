import os
import openai
import streamlit as st
import pandas as pd
from io import BytesIO
import base64
import urllib.parse
from openai.error import RateLimitError
import time
import json

# 지원되는 파일 형식 정의
supported_file_types = ['xlsx', 'csv', 'png', 'jpg', 'jpeg', 'pdf']

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
        st.warning(f"'{folder_name}' 폴더가 존재하지 않아 생성 중입니다.")
        create_folder_url = f"https://api.github.com/repos/{repo}/contents/{folder_name}"
        data = {
            "message": f"Create {folder_name} folder",
            "content": base64.b64encode(b'').decode('utf-8'),  # 빈 파일로 폴더 생성
            "branch": branch
        }
        put_response = requests.put(create_folder_url, json=data, headers=headers)
        if put_response.status_code == 201:
            st.success(f"'{folder_name}' 폴더가 성공적으로 생성되었습니다.")
        else:
            st.error(f"폴더 생성에 실패했습니다: {put_response.status_code}")
    elif response.status_code != 200:
        st.error(f"폴더 확인에 실패했습니다: {response.status_code}")

# GitHub API 요청을 처리하는 함수 (파일 목록을 가져옴)
def get_github_files(repo, branch, token, folder_name='uploadFiles'):
    create_github_folder_if_not_exists(repo, folder_name, token, branch)
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        files = [item['path'] for item in response.json().get('tree', []) if item['type'] == 'blob' and item['path'].startswith(folder_name)]
        return files
    else:
        st.error("GitHub 파일 목록을 가져오지 못했습니다. 저장소 정보나 토큰을 확인하세요.")
        return []

# GitHub에서 파일의 SHA 값을 가져오는 함수
def get_file_sha(repo, file_path, token, branch='main'):
    encoded_file_path = urllib.parse.quote(file_path)
    url = f"https://api.github.com/repos/{repo}/contents/{encoded_file_path}?ref={branch}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get('sha', None)
    else:
        return None

# GitHub에 파일 업로드 함수
def upload_file_to_github(repo, folder_name, file_name, file_content, token, branch='main', sha=None):
    create_github_folder_if_not_exists(repo, folder_name, token, branch)
    encoded_file_name = urllib.parse.quote(file_name)
    url = f"https://api.github.com/repos/{repo}/contents/{folder_name}/{encoded_file_name}"
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json"
    }

    content_encoded = base64.b64encode(file_content).decode('utf-8')

    data = {
        "message": f"Upload {file_name}",
        "content": content_encoded,
        "branch": branch
    }

    if sha:
        data["sha"] = sha

    response = requests.put(url, json=data, headers=headers)

    if response.status_code == 201:
        st.success(f"{file_name} 파일이 성공적으로 업로드되었습니다.")
    elif response.status_code == 200:
        st.success(f"{file_name} 파일이 성공적으로 덮어쓰기 되었습니다.")
    else:
        st.error(f"파일 업로드에 실패했습니다: {response.status_code}")
        st.error(response.json())

# GitHub에서 파일을 다운로드하는 함수
def get_file_from_github(repo, branch, filepath, token):
    encoded_filepath = urllib.parse.quote(filepath)
    url = f"https://api.github.com/repos/{repo}/contents/{encoded_filepath}?ref={branch}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return BytesIO(requests.get(response.json()['download_url']).content)
    else:
        st.error(f"{filepath} 파일을 가져오지 못했습니다. 상태 코드: {response.status_code}")
        return None

# 엑셀 파일에서 시트를 HTML 테이블로 변환하는 함수
def convert_excel_to_html_with_styles(file_content, selected_sheets):
    try:
        # 엑셀 파일을 BytesIO 객체로 읽음
        excel_data = pd.ExcelFile(BytesIO(file_content))
        sheet_names = excel_data.sheet_names
        
        # 선택한 시트들만 가져옴
        data = pd.DataFrame()
        for sheet in selected_sheets:
            data = pd.concat([data, pd.read_excel(excel_data, sheet_name=sheet)], ignore_index=True)

        # 데이터를 HTML 테이블 형식으로 변환
        html_content = "<table style='border-collapse: collapse;'>"
        for _, row in data.iterrows():
            html_content += "<tr>"
            for cell in row:
                cell_value = str(cell) if pd.notna(cell) else ""
                html_content += f"<td>{cell_value}</td>"
            html_content += "</tr>"
        html_content += "</table>"

        return html_content

    except Exception as e:
        st.error(f"엑셀 파일 변환 중 오류가 발생했습니다: {str(e)}")
        return None

# 시트 선택 로직 추가
def handle_sheet_selection(file_content, sheet_count, idx):
    col1, col2, col3 = st.columns([0.25, 0.5, 0.25])
    
    with col1:
        st.text_input(f"시트 갯수 ({idx})", value=f"예) 시트: {sheet_count}개", disabled=True)
    
    with col2:
        sheet_selection = st.text_input(f"시트 선택(예: 1-3, 5) ({idx})", value="1", key=f"sheet_selection_{idx}")

    with col3:
        select_button = st.button(f"선택 ({idx})")

    return sheet_selection if select_button else None

# 엑셀 파일 시트 데이터를 파싱하는 함수
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

# 파일을 업로드하고 엑셀 파일을 HTML로 변환하는 부분
github_info_loaded = load_env_info()

if github_info_loaded:
    with st.expander("파일 업로드", expanded=True):
        uploaded_files = st.file_uploader("파일을 여러 개 드래그 앤 드롭하여 업로드하세요. (최대 100MB)", accept_multiple_files=True)

        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_type = uploaded_file.name.split('.')[-1].lower()

                if file_type not in supported_file_types:
                    st.error(f"지원하지 않는 파일입니다: {uploaded_file.name}")
                    continue

                if uploaded_file.size > (100 * 1024 * 1024):
                    st.warning(f"'{uploaded_file.name}' 파일은 100MB 제한을 초과했습니다.")
                else:
                    file_content = uploaded_file.read()
                    file_name = uploaded_file.name

                    # 엑셀 파일 업로드 및 시트 정보 확인
                    excel_data = pd.ExcelFile(BytesIO(file_content))
                    sheet_count = len(excel_data.sheet_names)

                    sheet_selection = handle_sheet_selection(file_content, sheet_count, 0)
                    
                    if sheet_selection:
                        selected_sheets = parse_sheet_selection(sheet_selection, sheet_count)
                        if selected_sheets:
                            html_output = convert_excel_to_html_with_styles(file_content, selected_sheets)
                            st.session_state['결과 보고서 보기'] = html_output

# 요청사항 리스트 처리 및 보고서 생성
st.subheader("3. 작성 보고서 요청사항 및 실행 버튼")

if 'rows' not in st.session_state:
    st.session_state['rows'] = [{"제목": "", "요청": "", "파일": "", "데이터": "", "checked": False}]

rows = st.session_state['rows']
checked_rows = []

for idx, row in enumerate(rows):
    with st.container():
        col1, col2 = st.columns([0.05, 0.95])
        with col1:
            row_checked = st.checkbox("", key=f"row_checked_{idx}", value=row.get("checked", False))
        with col2:
            st.markdown(f"#### 요청사항 {idx+1}")

        row['제목'] = st.text_input(f"제목 (요청사항 {idx+1})", row['제목'], key=f"title_{idx}", placeholder="여기에 제목 입력")
        row['요청'] = st.text_area(f"요청 (요청사항 {idx+1})", row['요청'], key=f"request_{idx}")

        file_list = ['파일을 선택하세요.']
        # GitHub 파일 목록 불러오기 전에 GitHub 정보가 설정되었는지 확인
        if st.session_state.get('github_token') and st.session_state.get('github_repo') and st.session_state.get('github_branch'):
            file_list += get_github_files(st.session_state['github_repo'], st.session_state['github_branch'], st.session_state['github_token'])

        selected_file = st.selectbox(f"파일 선택 (요청사항 {idx+1})", options=file_list, key=f"file_select_{idx}")

        if selected_file != '파일을 선택하세요.':
            file_path = selected_file
            file_content = get_file_from_github(st.session_state["github_repo"], st.session_state["github_branch"], file_path, st.session_state["github_token"])
            
            if file_content:
                file_type = file_path.split('.')[-1].lower()

                if file_type not in supported_file_types:
                    st.error(f"지원하지 않는 파일입니다: {file_path}")
                    row['데이터'] = ""
                else:
                    row['데이터'] = convert_excel_to_html_with_styles(file_content)
                    st.session_state['결과 보고서 보기'] = row['데이터']

            else:
                st.error(f"{selected_file} 파일을 GitHub에서 불러오지 못했습니다.")
            
        st.text_input(f"파일 경로 (요청사항 {idx+1})", row['파일'], disabled=True, key=f"file_{idx}")

    if row_checked:
        checked_rows.append(idx)

# 행 추가, 삭제, 새로고침 버튼 가로로 배치
col1, col2, col3 = st.columns([0.3, 0.3, 0.3])

with col1:
    if st.button("행 추가"):
        new_row = {"제목": "", "요청": "", "파일": "", "데이터": "", "checked": False}
        st.session_state['rows'].append(new_row)

with col2:
    if st.button("행 삭제"):
        if checked_rows:
            st.session_state['rows'] = [row for idx, row in enumerate(rows) if idx not in checked_rows]
            st.success(f"체크된 {len(checked_rows)}개의 요청사항이 삭제되었습니다.")
        else:
            st.warning("삭제할 요청사항을 선택해주세요.")

with col3:
    if st.button("새로고침"):
        st.success("새로고침 하였습니다.")

# 보고서 작성 버튼
if st.button("보고서 작성"):
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

# [양식 저장], [양식 불러오기] 버튼 가로로 배치
col1, col2 = st.columns([0.5, 0.5])

with col1:
    if st.button("양식 저장"):
        st.success("양식이 저장되었습니다.")

with col2:
    if st.button("양식 불러오기"):
        st.success("양식이 불러와졌습니다.")

# 4 프레임: 결과 보고서
st.subheader("4. 결과 보고서")
if '결과 보고서 보기' in st.session_state:
    st.components.v1.html(st.session_state['결과 보고서 보기'], height=1024, scrolling=True)

#frontend 기능 구현 끝

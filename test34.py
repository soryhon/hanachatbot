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
import openpyxl

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

# 엑셀 파일에서 시트 가져오기 및 데이터 추출
def extract_sheets_from_excel(file_content, selected_sheets):
    try:
        excel_data = pd.ExcelFile(file_content)
        all_sheets = excel_data.sheet_names
        
        if selected_sheets == 'all':
            selected_sheets = all_sheets
        else:
            selected_sheets = [all_sheets[int(i)-1] for i in selected_sheets if int(i) <= len(all_sheets)]
        
        data = pd.DataFrame()
        for sheet in selected_sheets:
            data = pd.concat([data, pd.read_excel(file_content, sheet_name=sheet)], ignore_index=True)
        
        return data
    except Exception as e:
        st.error(f"엑셀 파일의 시트 데이터를 추출하는 중에 오류가 발생했습니다: {str(e)}")
        return None

# 셀 스타일 정보를 CSS로 변환하는 함수
def get_cell_style(cell):
    styles = []

    if cell.font:
        if cell.font.bold:
            styles.append("font-weight: bold;")
        if cell.font.italic:
            styles.append("font-style: italic;")
        if cell.font.size:
            styles.append(f"font-size: {cell.font.size}pt;")
        if cell.font.color and cell.font.color.rgb:
            styles.append(f"color: #{cell.font.color.rgb[2:]};")

    if cell.fill and cell.fill.fgColor and cell.fill.fgColor.rgb:
        styles.append(f"background-color: #{cell.fill.fgColor.rgb[2:]};")

    if cell.alignment:
        if cell.alignment.horizontal:
            styles.append(f"text-align: {cell.alignment.horizontal};")
        if cell.alignment.vertical:
            styles.append(f"vertical-align: {cell.alignment.vertical};")

    if cell.border:
        for side in ['left', 'right', 'top', 'bottom']:
            border_side = getattr(cell.border, side)
            if border_side and border_side.style:
                styles.append(f"border-{side}: 1px solid black;")

    return " ".join(styles)

# 엑셀 시트 데이터를 HTML로 변환
def convert_data_to_html(file_data, file_path, idx):
    workbook = openpyxl.load_workbook(file_path, data_only=True)
    sheet = workbook.active

    html_content = f"<h3>{idx + 1}. 보고서</h3>"
    html_content += "<table style='border-collapse: collapse;'>"

    for i, row in enumerate(file_data.itertuples(index=False), 1):
        html_content += "<tr>"
        for j, value in enumerate(row, 1):
            cell = sheet.cell(row=i, column=j)
            style = get_cell_style(cell)
            html_content += f"<td style='{style}'>{value}</td>"
        html_content += "</tr>"

    html_content += "</table>"
    return html_content

# HTML 데이터로 여러 요청사항 리스트 병합
def generate_html_report(rows):
    html_report = ""
    for idx, row in enumerate(rows):
        if row["데이터"] is not None and isinstance(row["데이터"], pd.DataFrame):
            html_report += convert_data_to_html(row["데이터"], row["파일"], idx)
    return html_report

# LLM을 통해 프롬프트와 파일을 전달하고 응답을 받는 함수
def run_llm_with_file_and_prompt(api_key, titles, requests, file_data_list):
    global global_generated_prompt
    openai.api_key = api_key

    responses = []
    global_generated_prompt = [] 

    try:
        for i, (title, request, file_data) in enumerate(zip(titles, requests, file_data_list)):
            if isinstance(file_data, pd.DataFrame):
                file_data_str = file_data.to_string()
            elif isinstance(file_data, dict):
                file_data_str = "\n".join([f"시트 이름: {sheet_name}\n{data.to_string()}" for sheet_name, data in file_data.items()])
            else:
                file_data_str = str(file_data)

            generated_prompt = f"""
            보고서 제목은 '{title}'로 하고, 아래의 파일 데이터를 분석하여 '{request}'를 요구 사항을 만족할 수 있도록 최적화된 보고서를 완성해.
            표로 표현 할 때는 table 태그 형식으로 구현해야 한다. th과 td 태그는 border는 사이즈 1이고 색상은 검정색으로 구성한다.
            파일 데이터: {file_data_str}
            """

            global_generated_prompt.append(generated_prompt)

            prompt_template = PromptTemplate(template=generated_prompt, input_variables=[])
            llm = ChatOpenAI(model_name="gpt-4")
            chain = LLMChain(llm=llm, prompt=prompt_template)

            success = False
            retry_count = 0
            max_retries = 5

            while not success and retry_count < max_retries:
                try:
                    response = chain.run({})
                    responses.append(response)
                    success = True
                except RateLimitError:
                    retry_count += 1
                    st.warning(f"API 요청 한도를 초과했습니다. 10초 후 다시 시도합니다. 재시도 횟수: {retry_count}/{max_retries}")
                    time.sleep(10)

                time.sleep(10)
    except Exception as e:
        st.error(f"LLM 실행 중 오류가 발생했습니다: {str(e)}")
    return responses

# 엑셀 파일 선택 로직
def handle_file_selection(file_name, file_content, file_type, idx):
    if file_type == 'xlsx':
        try:
            excel_data = pd.ExcelFile(file_content)
            sheet_count = len(excel_data.sheet_names)

            file_data = extract_sheets_from_excel(file_content, ['all'])
            if file_data is not None and not file_data.empty:
                return file_data
            else:
                st.error("선택한 시트에 데이터가 없습니다.")
                return None
        except Exception as e:
            st.error(f"엑셀 파일 처리 중 오류가 발생했습니다: {str(e)}")
            return None
    else:
        st.error("지원하지 않는 파일 형식입니다.")
        return None

# GitHub 파일 목록에서 엑셀 파일을 선택할 때 handle_file_selection을 호출하는 부분
if 'rows' in st.session_state:
    rows = st.session_state['rows']
    for idx, row in enumerate(rows):
        file_list = ['파일을 선택하세요.']  # 기본 파일 리스트 초기화
        if st.session_state.get('github_token') and st.session_state.get('github_repo'):
            file_list += get_github_files(st.session_state['github_repo'], st.session_state['github_branch'], st.session_state['github_token'])
        
        # 고유한 key 값을 설정하기 위해 idx와 row에 포함된 고유 정보(제목)를 추가하여 중복 방지
        unique_key = f"file_select_{idx}_{row['제목']}_{idx}"
        
        selected_file = st.selectbox(f"파일 선택 (요청사항 {idx+1})", options=file_list, key=unique_key)
        
        if selected_file and selected_file != '파일을 선택하세요.':
            file_path = selected_file
            file_content = get_file_from_github(st.session_state["github_repo"], st.session_state["github_branch"], file_path, st.session_state["github_token"])

            if file_content:
                file_type = file_path.split('.')[-1].lower()

                if file_type not in supported_file_types:
                    st.error(f"지원하지 않는 파일 형식입니다: {file_path}")
                    row['데이터'] = ""
                else:
                    file_data = handle_file_selection(file_path, file_content, file_type, idx)
                    
                    if file_data is not None and not file_data.empty:
                        row['파일'] = f"/{st.session_state['github_repo']}/{st.session_state['github_branch']}/{selected_file}"
                        row['데이터'] = file_data
                    else:
                        st.error(f"{selected_file} 파일의 데이터를 처리하지 못했습니다.")
            else:
                st.error(f"{selected_file} 파일을 GitHub에서 불러오지 못했습니다.")
        else:
            st.info("파일을 선택하세요.")

# GitHub 정보가 있는지 확인하고 파일 업로드 객체를 출력
github_info_loaded = load_env_info()

# 업로드 가능한 파일 크기 제한 (100MB)
MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

st.subheader("1. 파일 업로드")
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
                    st.warning(f"'{uploaded_file.name}' 파일은 {MAX_FILE_SIZE_MB}MB 제한을 초과했습니다.")
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
                        
                        if file_type == 'xlsx':
                            handle_file_selection(file_name, file_content, file_type, 0)
                        uploaded_files = None
else:
    st.warning("GitHub 정보가 저장되기 전에는 파일 업로드를 할 수 없습니다. 먼저 GitHub 정보를 입력해 주세요.")

# 3 프레임: 작성 보고서 요청사항 및 실행 버튼
st.subheader("3. 작성 보고서 요청사항 및 실행 버튼")

with st.expander("요청사항 리스트", expanded=True):
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
            if st.session_state.get('github_token') and st.session_state.get('github_repo'):
                file_list += get_github_files(st.session_state['github_repo'], st.session_state['github_branch'], st.session_state['github_token'])

            # 고유한 key 값을 설정하여 중복 방지
            unique_key = f"file_select_{idx}_{row['제목']}_{idx}"

            selected_file = st.selectbox(f"파일 선택 (요청사항 {idx+1})", options=file_list, key=unique_key)

            if selected_file != '파일을 선택하세요.':
                file_path = selected_file
                file_content = get_file_from_github(st.session_state["github_repo"], st.session_state["github_branch"], file_path, st.session_state["github_token"])
                
                if file_content:
                    file_type = file_path.split('.')[-1].lower()

                    if file_type not in supported_file_types:
                        st.error(f"지원하지 않는 파일입니다: {file_path}")
                        row['데이터'] = ""
                    else:
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

    col1, col2, col3 = st.columns([0.3, 0.3, 0.3])

    with col1:
        if st.button("행 추가", key="add_row"):
            new_row = {"제목": "", "요청": "", "파일": "", "데이터": "", "checked": False}
            st.session_state['rows'].append(new_row)

    with col2:
        if st.button("행 삭제", key="delete_row"):
            if checked_rows:
                st.session_state['rows'] = [row for idx, row in enumerate(rows) if idx not in checked_rows]
                st.success(f"체크된 {len(checked_rows)}개의 요청사항이 삭제되었습니다.")
            else:
                st.warning("삭제할 요청사항을 선택해주세요.")

    with col3:
        if st.button("새로고침", key="refresh_page"):
            st.success("새로고침 하였습니다.")

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

col1, col2 = st.columns([0.5, 0.5])

with col1:
    if st.button("양식 저장", key="save_template"):
        st.success("양식이 저장되었습니다.")

with col2:
    if st.button("양식 불러오기", key="load_template"):
        st.success("양식이 불러와졌습니다.")

# 4 프레임: 결과 보고서
st.subheader("4. 결과 보고서")

st.write("결과 보고서 보기")
html_report = generate_html_report(st.session_state['rows'])
if html_report:
    st.components.v1.html(html_report, height=1024, scrolling=True)

st.text_area("전달된 프롬프트:", value="\n\n".join(global_generated_prompt), height=150)

if "response" in st.session_state:
    for idx, response in enumerate(st.session_state["response"]):
        st.text_area(f"응답 {idx+1}:", value=response, height=300)
        
        st.components.v1.html(response, height=600, scrolling=True)

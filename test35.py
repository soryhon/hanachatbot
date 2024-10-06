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

# 엑셀 셀 스타일을 추출하여 CSS로 변환
def convert_excel_style_to_css(cell):
    css_styles = []
    
    # 폰트 스타일
    if cell.font.bold:
        css_styles.append("font-weight: bold;")
    if cell.font.italic:
        css_styles.append("font-style: italic;")
    if cell.font.underline:
        css_styles.append("text-decoration: underline;")
    
    # 폰트 색상 처리 (RGB 또는 자동 색상)
    if cell.font.color:
        if hasattr(cell.font.color, 'rgb') and cell.font.color.rgb:
            css_styles.append(f"color: #{cell.font.color.rgb[2:]};")
        elif cell.font.color.type == 'theme':
            css_styles.append("color: #000000;")  # 테마 색상일 경우 기본적으로 검은색으로 설정
    
    # 배경색 (RGB 값이 없을 경우 안전하게 처리)
    # if cell.fill and cell.fill.start_color:
    #     if hasattr(cell.fill.start_color, 'rgb') and cell.fill.start_color.rgb:
    #         css_styles.append(f"background-color: #{cell.fill.start_color.rgb[2:]};")
    #     elif cell.fill.start_color.type == 'theme':
    #         css_styles.append("background-color: #FFFFFF;")  # 테마 색상일 경우 흰색으로 설정
    
    # 정렬
    if cell.alignment.horizontal:
        css_styles.append(f"text-align: {cell.alignment.horizontal};")
    if cell.alignment.vertical:
        css_styles.append(f"vertical-align: {cell.alignment.vertical};")
    
    # 테두리
    if cell.border:
        border_style = []
        for side in ['left', 'right', 'top', 'bottom']:
            border = getattr(cell.border, side)
            if border and border.style:
                border_style.append(f"border-{side}: 1px solid black;")
        css_styles.extend(border_style)

    return " ".join(css_styles)

# 엑셀 파일에서 각 셀의 스타일을 반영하여 HTML로 변환
def convert_excel_to_html_with_styles(excel_file):
    workbook = openpyxl.load_workbook(excel_file, data_only=True)
    sheet = workbook.active  # 첫 번째 시트를 가져옴

    html_content = "<table style='border-collapse: collapse;'>"
    
    for row in sheet.iter_rows():
        html_content += "<tr>"
        for cell in row:
            style = convert_excel_style_to_css(cell)  # 각 셀의 스타일을 CSS로 변환
            cell_value = cell.value if cell.value is not None else ""
            html_content += f"<td style='{style}'>{cell_value}</td>"
        html_content += "</tr>"

    html_content += "</table>"
    return html_content

# 엑셀 파일에서 스타일을 추출하여 HTML로 변환하는 함수
def extract_sheets_with_styles_from_excel(file_content):
    try:
        html_report = convert_excel_to_html_with_styles(file_content)
        return html_report
    except Exception as e:
        st.error(f"엑셀 파일의 시트 데이터를 추출하는 중에 오류가 발생했습니다: {str(e)}")
        return None

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

# GitHub 정보와 OpenAI API 키를 자동 설정하는 함수 호출
github_info_loaded = load_env_info()

# 파일 업로드 및 엑셀 시트 처리
st.subheader("1. 파일 업로드")

uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요.", type="xlsx")
if uploaded_file:
    # 파일이 업로드되면 처리할 내용 추가
    st.success(f"'{uploaded_file.name}' 파일이 업로드되었습니다.")

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
    # 폴더가 이미 존재할 경우 메시지를 표시하지 않음

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
    create_github_folder_if_not_exists(repo, folder_name, token, branch)  # 업로드 전 폴더가 없으면 생성
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

# HTML로 변환하는 함수
def generate_html_report(rows):
    html_report = ""
    for idx, row in enumerate(rows):
        if row["데이터"] is not None and isinstance(row["데이터"], pd.DataFrame):
            html_report += convert_data_to_html(row["데이터"], row["제목"], idx)
    return html_report

# NaN 값 처리, 셀 병합 및 줄바꿈 변환을 포함한 HTML 변환
def convert_data_to_html(file_data, title, idx):
    file_data = file_data.fillna("")  # NaN 값을 빈 값으로 대체

    html_content = f"<h3>{idx + 1}. {title}</h3>"
    html_content += "<table style='border-collapse: collapse;'>"

    for i, row in file_data.iterrows():
        html_content += "<tr>"
        for j, col in enumerate(row):
            col = str(col).replace("\n", "<br>")  # 줄바꿈을 <br>로 변환
            html_content += f"<td style='border: 1px solid black;'>{col}</td>"
        html_content += "</tr>"

    html_content += "</table>"
    return html_content

# GitHub 정보가 로드되었는지 확인한 후 파일 업로드 처리
if github_info_loaded:
    # 파일 업로드 처리 및 요청사항 리스트 생성
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

                selected_file = st.selectbox(f"파일 선택 (요청사항 {idx+1})", options=file_list, key=f"file_select_{idx}")

                if selected_file != '파일을 선택하세요.':
                    file_path = selected_file
                    # 방어적 코드를 추가하여 값이 없을 경우 파일 가져오기 중단
                    if st.session_state.get("github_repo") and st.session_state.get("github_branch") and st.session_state.get("github_token"):
                        file_content = get_file_from_github(st.session_state["github_repo"], st.session_state["github_branch"], file_path, st.session_state["github_token"])
                        
                        if file_content:
                            file_type = file_path.split('.')[-1].lower()

                            if file_type not in ['xlsx', 'pptx', 'docx', 'csv', 'png', 'jpg', 'jpeg']:
                                st.error(f"지원하지 않는 파일입니다: {file_path}")
                                row['데이터'] = ""
                            else:
                                # 엑셀 파일인 경우 기본적으로 1번 시트 데이터를 가져오도록 설정
                                if file_type == 'xlsx':
                                    row['데이터'] = extract_sheets_with_styles_from_excel(file_content)
                                else:
                                    row['데이터'] = file_content
                                row['파일'] = f"/{st.session_state['github_repo']}/{st.session_state['github_branch']}/{selected_file}"

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

# 4 프레임: 결과 보고서
st.subheader("4. 결과 보고서")
if any(row['파일'] for row in rows):
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

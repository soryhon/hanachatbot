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

# 4 프레임: 결과 보고서
st.subheader("4. 결과 보고서")
if '결과 보고서 보기' in st.session_state:
    st.components.v1.html(st.session_state['결과 보고서 보기'], height=1024, scrolling=True)

#frontend 기능 구현 끝

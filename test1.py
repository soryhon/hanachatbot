

import streamlit as st
import pandas as pd
import os
import openai
from langchain.llms import OpenAI
from PIL import Image
from PyPDF2 import PdfReader
import base64
import io
import docx

# OpenAI API 설정
os.environ["OPENAI_API_KEY"] = "sk-iqikeXmsMIaJo73WNYPtQARmKCdhr-IUY4yNJjgWxJT3BlbkFJSjjKw6pNAyeNKntKTicdtpx6Sv4It1Cm_4_yZ6E2oA"
llm = OpenAI(model='gpt-4', temperature=0.7)

# 메인 레이아웃
st.title("일일 업무 및 보고서 자동화 프로그램")

# 세 개의 프레임을 나누어서 배치
col1, col2, col3 = st.columns([4, 1, 5])

# 1. 작성 보고서 요청사항 (col1에 위치)
with col1:
    st.header("1. 작성 보고서 요청사항")
    
    # pandas 데이터프레임을 사용하여 입력받을 데이터 구조 생성
    if 'df' not in st.session_state:
        st.session_state['df'] = pd.DataFrame(columns=['제목', '요청', '데이터'])

    # 파일 선택 함수
    def select_file(row_idx):
        uploaded_file = st.file_uploader(f"데이터 선택 (행 {row_idx})", type=['csv', 'txt', 'pdf', 'docx', 'pptx'], key=f'file_{row_idx}')
        if uploaded_file is not None:
            file_path = os.path.join("/mnt/data", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state['df'].at[row_idx, '데이터'] = file_path
            st.success(f"파일 저장 완료: {file_path}")

    # 데이터프레임의 각 행을 입력받는 인터페이스 생성
    for idx, row in st.session_state['df'].iterrows():
        col_title, col_request, col_data = st.columns([3, 3, 4])
        col_title.text_input("제목", key=f'title_{idx}', value=row['제목'] if pd.notna(row['제목']) else "", on_change=lambda: update_df_value(idx, '제목'))
        col_request.text_input("요청", key=f'request_{idx}', value=row['요청'] if pd.notna(row['요청']) else "", on_change=lambda: update_df_value(idx, '요청'))
        col_data.button("데이터 선택", on_click=lambda idx=idx: select_file(idx))

    # 행 추가 및 삭제 버튼
    st.button("행 추가", on_click=lambda: st.session_state['df'] = st.session_state['df'].append({'제목': '', '요청': '', '데이터': ''}, ignore_index=True))
    selected_rows = st.multiselect("삭제할 행 선택", st.session_state['df'].index)
    if st.button("행 삭제"):
        st.session_state['df'] = st.session_state['df'].drop(selected_rows).reset_index(drop=True)

# 2. 파일 업로드 (col1에 위치)
with col1:
    st.header("2. 파일 업로드")
    uploaded_files = st.file_uploader("파일 선택", accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            st.write(f"업로드된 파일명: {file.name}")
            # 파일 저장 로직 필요

# 3. 실행 (col2에 위치)
with col2:
    st.header("3. 실행")
    if st.button("실행"):
        results = []
        for idx, row in st.session_state['df'].iterrows():
            prompt = f"제목: {row['제목']}, 요청: {row['요청']}, 데이터: {row['데이터']}"
            response = llm(prompt)
            results.append(response)
        st.session_state['results'] = results
        st.success("LLM 처리 완료")

# 4. 결과 보고서 (col3에 위치)
with col3:
    st.header("4. 결과 보고서")
    if 'results' in st.session_state:
        for idx, result in enumerate(st.session_state['results']):
            st.subheader(f"제목({st.session_state['df'].at[idx, '제목']})")
            st.write(result)

    export_format = st.selectbox("저장할 형식 선택", ['pdf', 'docx', 'xlsx', 'txt'])
    if st.button("Export"):
        # 결과 보고서를 선택된 형식으로 저장하는 로직 필요

# 5. 참고 템플릿 미리보기 (col1에 위치)
with col1:
    st.header("5. 참고 템플릿 미리보기")
    template_file = st.file_uploader("템플릿 파일 선택", type=['pdf', 'png', 'jpg', 'html'])
    if template_file:
        if template_file.type == "application/pdf":
            reader = PdfReader(template_file)
            for page in reader.pages:
                st.write(page.extract_text())
        elif template_file.type.startswith("image"):
            image = Image.open(template_file)
            st.image(image)
        # HTML 파일은 별도로 처리 필요

# 6. 저장 및 7. 불러오기 (col3에 위치)
with col3:
    st.header("6. 저장")
    save_filename = st.text_input("저장할 파일명 입력")
    if st.button("저장"):
        # txt 파일로 저장하는 로직
        with open(f"/mnt/data/{save_filename}.txt", "w") as f:
            f.write(st.session_state['df'].to_string())

    st.header("7. 불러오기")
    load_file = st.file_uploader("저장된 txt 파일 선택")
    if load_file:
        # txt 파일에서 데이터 불러오기
        loaded_data = pd.read_csv(load_file, delimiter="\t")
        st.session_state['df'] = loaded_data
        st.success("불러오기 완료")

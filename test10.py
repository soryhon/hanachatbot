import streamlit as st
import pandas as pd
from io import BytesIO
import os

# 페이지 레이아웃 설정 (가로로 3개의 프레임, 전체 화면 해상도 적용)
st.set_page_config(layout="wide")

# 세 개의 프레임 설정
col1, col2, col3 = st.columns([39, 10, 49])

# 첫 번째 프레임: 작성 보고서 요청사항, 파일 업로드, 참고 템플릿 미리보기
with col1:
    st.markdown("### 1. 작성 보고서 요청사항")
    st.markdown("---")
    
    # 기본 데이터 프레임 생성
    if 'rows' not in st.session_state:
        st.session_state.rows = pd.DataFrame({
            '제목': [''],
            '요청': [''],
            '데이터': ['']
        })
    
    def add_row():
        new_row = pd.DataFrame({
            '제목': [''],
            '요청': [''],
            '데이터': ['']
        })
        st.session_state.rows = pd.concat([st.session_state.rows, new_row], ignore_index=True)
        
    def delete_row(index):
        st.session_state.rows.drop(index, inplace=True)
        st.session_state.rows.reset_index(drop=True, inplace=True)

    # 테이블 표시
    for idx, row in st.session_state.rows.iterrows():
        st.checkbox(f"행{idx+1}")
        title = st.text_input(f"제목 (행{idx+1})", row['제목'], key=f"title_{idx}")
        request = st.text_input(f"요청 (행{idx+1})", row['요청'], key=f"request_{idx}")
        file = st.file_uploader(f"데이터 (행{idx+1})", key=f"file_{idx}")
        if file:
            st.session_state.rows.at[idx, '데이터'] = file.name

    # 행 추가 및 삭제 버튼
    st.button("행추가", on_click=add_row)
    st.button("행삭제", on_click=lambda: delete_row([idx for idx, _ in enumerate(st.session_state.rows) if st.session_state[f"checkbox_{idx}"]]))

    # 파일 업로드 섹션
    st.markdown("### 2. 파일 업로드")
    upload_files = st.file_uploader("여러 파일 업로드", accept_multiple_files=True)
    
    # 참고 템플릿 미리보기 섹션
    st.markdown("### 5. 참고 템플릿 미리보기")
    template_file = st.file_uploader("파일 선택", key="template")
    if st.button("미리보기"):
        if template_file:
            st.image(template_file)
        else:
            st.write("템플릿 파일을 선택하세요.")

# 두 번째 프레임: 실행 버튼
with col2:
    st.markdown("### 3. 실행")
    if st.button("실행"):
        st.session_state['openai_key'] = st.text_input("OpenAI API 키 입력", type="password")
        st.write("LLM 요청을 처리 중입니다...")

# 세 번째 프레임: 결과 보고서, 저장, 불러오기
with col3:
    st.markdown("### 4. 결과 보고서")
    # 실행 결과 보고
    for idx, row in st.session_state.rows.iterrows():
        st.markdown(f"#### 제목: {row['제목']}")
        st.text_area(f"LLM 응답 결과 값 (행{idx+1})", value="LLM 응답 결과값 표시 영역")
    
    # 결과 보고서 Export 버튼
    st.download_button("Export", data=b"결과 데이터", file_name="report.pdf")

    # 저장 및 불러오기 버튼
    st.markdown("### 6. 저장")
    save_file = st.text_input("파일 이름 입력", key="save_file")
    if st.button("저장"):
        if save_file:
            # 작성된 내용 및 템플릿 저장
            st.write(f"{save_file}.csv 저장 중...")
        else:
            st.write("파일 이름을 입력하세요.")
    
    st.markdown("### 7. 불러오기")
    load_file = st.file_uploader("CSV 파일 불러오기")
    if st.button("불러오기"):
        if load_file:
            # 불러오기 처리
            st.write(f"{load_file.name} 불러오기 완료.")
        else:
            st.write("불러올 파일을 선택하세요.")

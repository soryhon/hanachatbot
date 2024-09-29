import streamlit as st
import pandas as pd
import requests
import urllib.parse  # URL 인코딩을 위한 라이브러리
import base64  # base64 인코딩 및 복호화를 위한 라이브러리

# 페이지 설정
st.set_page_config(layout="wide")  # 페이지 가로길이를 모니터 전체 해상도로 설정

# 스타일 적용
st.markdown("""
    <style>
    .report-table {
        border: 2px solid #2e6fa7;
        border-radius: 10px;
        background-color: #eaf2fb;
        width: 100%;
        padding: 10px;
        margin-bottom: 20px;
    }
    .table-header {
        background-color: #2e6fa7;
        color: white;
        padding: 8px;
        font-weight: bold;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
    }
    .input-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
    .input-table td {
        padding: 8px;
        border: 1px solid #cccccc;
    }
    .input-table .label {
        background-color: #f5f5f5;
        width: 15%;
        text-align: center;
    }
    .input-table .input-cell {
        width: 85%;
    }
    .input-table .checkbox-cell {
        width: 5%;
    }
    </style>
""", unsafe_allow_html=True)

# GitHub에서 파일 목록을 가져오는 함수 (간단한 예시)
def get_github_files(repo, github_token, folder_name=None, branch="main"):
    # 여기에서는 그냥 예시 파일 리스트를 사용합니다.
    return ["파일1.txt", "파일2.csv", "파일3.docx"]

# 컬럼 설정
col1, col2, col3 = st.columns([0.39, 0.10, 0.49])

# 1. 작성 보고서 요청사항
with col1:
    st.markdown('<div class="report-table">', unsafe_allow_html=True)
    st.markdown('<div class="table-header">행 1</div>', unsafe_allow_html=True)

    # 테이블 형태로 제목, 요청, 데이터 입력 필드 표시
    st.markdown('<table class="input-table">', unsafe_allow_html=True)

    # 체크박스
    st.markdown('<tr><td class="checkbox-cell"><input type="checkbox"></td>', unsafe_allow_html=True)
    
    # 제목 입력
    st.markdown('<td class="label">제목</td>', unsafe_allow_html=True)
    title_input = st.text_input("", "입력창", key="title_1", label_visibility="collapsed")
    st.markdown(f'<td class="input-cell">{title_input}</td></tr>', unsafe_allow_html=True)

    # 요청 입력
    st.markdown('<tr><td></td><td class="label">요청</td>', unsafe_allow_html=True)
    request_input = st.text_input("", "입력창", key="request_1", label_visibility="collapsed")
    st.markdown(f'<td class="input-cell">{request_input}</td></tr>', unsafe_allow_html=True)

    # 데이터 입력
    st.markdown('<tr><td></td><td class="label">데이터</td>', unsafe_allow_html=True)

    # 선택 버튼 및 파일 리스트
    st.markdown('<td class="input-cell">', unsafe_allow_html=True)
    if st.button("선택 (행1)"):
        st.write("파일 선택됨")
    selected_file = st.selectbox("", options=get_github_files("repo", "token"), label_visibility="collapsed")
    st.markdown(f'<br>파일 리스트: {selected_file}', unsafe_allow_html=True)
    
    # 데이터 입력창
    data_input = st.text_input("", "입력창", key="data_1", label_visibility="collapsed")
    st.markdown(f'{data_input}</td></tr>', unsafe_allow_html=True)

    # 테이블 종료
    st.markdown('</table>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# 2. 파일 업로드 및 GitHub 저장소 정보 입력 기능
with col1:
    st.subheader("2. 파일 업로드 및 GitHub 저장소 정보")
    uploaded_files = st.file_uploader("파일을 여러 개 드래그 앤 드롭하여 업로드하세요.", accept_multiple_files=True)

    if uploaded_files and st.button("파일 업로드"):
        for uploaded_file in uploaded_files:
            st.write(f"업로드된 파일: {uploaded_file.name}")

# 3. 실행 버튼 및 OpenAI API 키 입력
with col2:
    st.subheader("3. 실행")

    openai_api_key = st.text_input("OpenAI API 키를 입력하세요.", type="password")

    if st.button("OpenAI API 키 저장"):
        st.session_state['openai_api_key'] = openai_api_key
        st.success("OpenAI API 키가 저장되었습니다.")

    if st.button("실행"):
        if st.session_state['openai_api_key'] == "":
            st.error("OpenAI API 키를 입력해야 실행할 수 있습니다.")
        else:
            llm_results = {}
            for idx, row in enumerate(rows):
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

# 4. 결과 보고서 화면
with col3:
    st.subheader("4. 결과 보고서")

    if 'llm_results' in locals() and llm_results:
        for idx, result in llm_results.items():
            st.text(f"제목: {rows[idx]['제목']}")
            st.text(f"LLM 응답 결과:\n{result}")

    if st.button("Export"):
        file_type = st.selectbox("파일 형식 선택", options=["pdf", "docx", "xlsx", "txt"])
        st.success(f"{file_type} 형식으로 파일 다운로드 가능")

# 5. 참고 템플릿 미리보기
with col1:
    st.subheader("5. 참고 템플릿 미리보기")
    selected_template_file = st.selectbox("템플릿 파일 선택", options=["Template1", "Template2", "Template3"])
    if st.button("선택"):
        st.success(f"선택한 템플릿: {selected_template_file}")

# 6. 저장
with col3:
    st.subheader("6. 저장")
    save_path = st.text_input("저장할 파일명 입력")
    if st.button("저장") and save_path:
        df = pd.DataFrame(rows)
        df.to_csv(f"{save_path}.csv")
        st.success(f"{save_path}.csv 파일로 저장되었습니다.")

# 7. 불러오기
with col3:
    st.subheader("7. 불러오기")
    uploaded_save_file = st.file_uploader("저장된 CSV 파일 불러오기", type=["csv"])
    if uploaded_save_file is not None:
        loaded_data = pd.read_csv(uploaded_save_file)
        st.dataframe(loaded_data)
        st.success("데이터가 불러와졌습니다.")

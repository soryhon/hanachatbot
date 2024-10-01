# app.py

import streamlit as st
import pandas as pd
import backend

# 페이지 설정
st.set_page_config(layout="wide")

# 세션 상태 초기화
if 'rows' not in st.session_state:
    st.session_state['rows'] = [{"제목": "", "요청": "", "데이터": "", "checked": False}]
if 'github_repo' not in st.session_state:
    st.session_state['github_repo'] = ""
if 'github_token' not in st.session_state:
    st.session_state['github_token'] = ""
if 'github_branch' not in st.session_state:
    st.session_state['github_branch'] = "main"
if 'openai_api_key' not in st.session_state:
    st.session_state['openai_api_key'] = ""
if 'github_saved' not in st.session_state:
    st.session_state['github_saved'] = False
if 'openai_saved' not in st.session_state:
    st.session_state['openai_saved'] = False
if 'show_info' not in st.session_state:
    st.session_state['show_info'] = True

# GitHub 및 OpenAI 정보 입력
if not (st.session_state['github_saved'] and st.session_state['openai_saved']):
    st.subheader("GitHub 저장소 정보 및 OpenAI API 키 입력")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("GitHub 정보 입력")
        st.session_state['github_repo'] = st.text_input("GitHub 저장소 경로 (예: username/repo)")
        st.session_state['github_token'] = st.text_input("GitHub API 토큰 입력", type="password")
        st.session_state['github_branch'] = st.text_input("브랜치 이름 (예: main 또는 master)", value="main")

        if st.button("GitHub 정보 저장"):
            if st.session_state['github_repo'] and st.session_state['github_token'] and st.session_state['github_branch']:
                st.session_state['github_saved'] = True
                st.success(f"GitHub 정보가 저장되었습니다!\nRepo: {st.session_state['github_repo']}, Branch: {st.session_state['github_branch']}")
            else:
                st.error("모든 GitHub 정보를 입력해주세요.")

    with col_b:
        st.subheader("OpenAI API 키 입력")
        st.session_state['openai_api_key'] = st.text_input("OpenAI API 키를 입력하세요.", type="password")

        if st.button("OpenAI API 키 저장"):
            if st.session_state['openai_api_key']:
                st.session_state['openai_saved'] = True
                st.success("OpenAI API 키가 저장되었습니다.")
            else:
                st.error("OpenAI API 키를 입력해주세요.")

# 1 프레임 (작성 보고서 요청사항, 파일 업로드, 참고 탬플릿 미리보기)
col1, col2, col3 = st.columns([0.39, 0.10, 0.49])

# 1. 작성 보고서 요청사항
with col1:
    st.subheader("1. 작성 보고서 요청사항")
    with st.expander("요청사항 리스트", expanded=True):
        rows = st.session_state['rows']
        checked_rows = []

        for idx, row in enumerate(rows):
            row_checked = st.checkbox(f"요청사항 {idx+1}", value=row.get("checked", False))
            row['제목'] = st.text_input(f"제목 (요청사항 {idx+1})", row['제목'])
            row['요청'] = st.text_input(f"요청 (요청사항 {idx+1})", row['요청'])
            
            if row_checked:
                checked_rows.append(idx)
                row['checked'] = True
            else:
                row['checked'] = False

            # GitHub 토큰이 입력된 경우에만 파일 목록 가져오기
            file_list = []
            if st.session_state['github_token']:
                file_list = backend.get_github_files(st.session_state['github_repo'], st.session_state['github_token'], branch=st.session_state['github_branch'])
            selected_file = st.selectbox(f"파일 선택 (요청사항 {idx+1})", options=file_list if file_list else ["(파일 없음)"])

            if st.session_state['github_token'] and st.button(f"파일 선택 (요청사항 {idx+1})"):
                server_path = backend.get_file_server_path(st.session_state['github_repo'], st.session_state['github_branch'], selected_file)
                row['데이터'] = server_path
                st.success(f"선택한 파일: {selected_file}\n서버 경로: {server_path}")

        if st.button("행 추가"):
            rows.append({"제목": "", "요청": "", "데이터": "", "checked": False})

        if st.button("행 삭제"):
            st.session_state['rows'] = [row for idx, row in enumerate(rows) if idx not in checked_rows]

    # 2. 파일 업로드
    st.subheader("2. 파일 업로드")
    uploaded_files = st.file_uploader("파일을 여러 개 드래그 앤 드롭하여 업로드하세요.", accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_content = uploaded_file.read()
            file_name = uploaded_file.name
            folder_name = 'uploadFiles'

            if st.session_state['github_token']:
                sha = backend.get_file_sha(st.session_state['github_repo'], f"{folder_name}/{file_name}", st.session_state['github_token'], branch=st.session_state['github_branch'])
                if sha:
                    if st.checkbox(f"'{file_name}' 파일이 이미 존재합니다. 덮어쓰시겠습니까?"):
                        backend.upload_file_to_github(st.session_state['github_repo'], folder_name, file_name, file_content, st.session_state['github_token'], branch=st.session_state['github_branch'], sha=sha)
                else:
                    backend.upload_file_to_github(st.session_state['github_repo'], folder_name, file_name, file_content, st.session_state['github_token'])

    # 5. 참고 탬플릿 미리보기
    st.subheader("5. 참고 탬플릿 미리보기")
    template_files = []
    if st.session_state['github_token']:
        template_files = backend.get_github_files(st.session_state['github_repo'], st.session_state['github_token'], folder_name="templateFiles", branch=st.session_state['github_branch'])

    selected_template_file = st.selectbox("참고 탬플릿 파일 선택", template_files if template_files else ["(파일 없음)"])
    
    if st.session_state['github_token'] and st.button("참고 탬플릿 파일 선택"):
        server_template_path = backend.get_file_server_path(st.session_state['github_repo'], st.session_state['github_branch'], selected_template_file)
        st.session_state['template_file_path'] = server_template_path
        st.success(f"선택한 파일 경로: {server_template_path}")

    if st.session_state['template_file_path']:
        st.markdown(backend.preview_file(st.session_state['template_file_path']), unsafe_allow_html=True)

# 2 프레임 (3. 실행)
with col2:
    st.subheader("3. 실행")
    if st.button("실행"):
        llm_results = {}
        for idx, row in enumerate(st.session_state['rows']):
            prompt = [
                {"role": "system", "content": "다음 파일을 분석하여 보고서를 작성하세요."},
                {"role": "user", "content": f"보고서 제목 : '{row['제목']}'\n요청 문구 : '{row['요청']}'\n데이터 전달 : '{row['데이터']}'"}
            ]
            llm_response = backend.send_to_llm(prompt, st.session_state['openai_api_key'])
            if llm_response:
                llm_results[idx] = llm_response
            else:
                llm_results[idx] = "LLM 응답을 받지 못했습니다."

        st.session_state['llm_results'] = llm_results
        st.success("LLM 요청이 완료되었습니다.")

# 3 프레임 (4. 결과 보고서 및 6. 저장 및 7. 불러오기)
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
        llm_results = st.session_state.get('llm_results', {})
        if llm_results:
            for idx, result in llm_results.items():
                st.text(f"제목: {st.session_state['rows'][idx]['제목']}")
                st.text(f"LLM 응답 결과:\n{result}")
        else:
            st.text("결과가 없습니다.")

    st.subheader("6. 저장 및 7. 불러오기")
    col3_1, col3_2 = st.columns([0.5, 0.5])

    with col3_1:
        st.subheader("6. 저장")
        save_path = st.text_input("저장할 파일명 입력")
        if st.button("저장") and save_path:
            df = pd.DataFrame(st.session_state['rows'])
            df.to_csv(f"{save_path}.csv", index=False)
            st.success

import streamlit as st
import pandas as pd
import backend as bd
import datetime
import time
import openpyxl
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import altair as alt
import numpy as np

# Frontend 기능 구현 시작 ---

# GitHub 정보가 있는지 확인하고 파일 업로드 객체를 출력
github_info_loaded = bd.load_env_info()

# 업로드 가능한 파일 크기 제한 (100MB)
MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024

#Session_state 변수 초기화
folderlist_init_value = "보고서명을 선택하세요."
templatelist_init_value = "불러올 보고서 양식을 선택하세요."
# 세션 상태에 각 변수 없다면 초기화
#bd.init_session_state(False)
#bd.refresh_page()
if 'request_title_02' not in st.session_state:
    st.session_state['request_title_02'] = ""    
if 'request_text_02' not in st.session_state:
    st.session_state['request_text_02'] = ""  
if 'check_setting_02' not in st.session_state:    
    st.session_state['check_setting_02'] = True
if 'check_result_02' not in st.session_state:
    st.session_state['check_result_02']=True
if 'check_report_02' not in st.session_state:
    st.session_state['check_report_02']=True
if 'html_report_02' not in st.session_state:
    st.session_state['html_report_02'] = "" 
if 'response_02' not in st.session_state:
    st.session_state["response_02"] = [] 
if 'selected_folder_index_02' not in st.session_state:
    st.session_state['selected_folder_index_02'] = 0 
if 'selected_folder_name_02' not in st.session_state:
    st.session_state['selected_folder_name_02'] = folderlist_init_value
if 'folder_list_option_02' not in st.session_state:
    st.session_state['folder_list_option_02'] = [folderlist_init_value]
if 'selected_template_index_02' not in st.session_state:
    st.session_state['selected_template_index_02'] = 0


# 1 프레임
# 보고서 타이틀
col1, col2 = st.columns([0.55,0.45])
with col1:
    st.markdown(
        "<p style='font-size:25px; font-weight:bold; color:#000000;'>보고서 비교분석 자동 완성 📈</p>",
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        "<div style='text-align:right;width:100%;'><p style='font-size:13px; font-weight:normal; color:#aaaaaa; margin-top:10px;'>by <b style='font-size:16px;color:#0099FF'>CheockCheock</b><b style='font-size:22px;color:#009999'>1</b> <b style='font-size:14px;'>prototype v.01</b></p></div>",
        unsafe_allow_html=True
    )

# 2 프레임
# 보고서명 및 폴더 선택, 새 폴더 만들기
subfolder_list=[]
date_list=[]
if github_info_loaded:
    with st.expander("📝 보고서 선택", expanded=st.session_state['check_report_02']):
        col1, col2 = st.columns([0.25, 0.75])
        with col1:
            st.write("")
            st.markdown(
                "<p style='font-size:14px; font-weight:bold; color:#000000;text-align:center;border:1px solid #E7EAF1;margin-top:10px;border-radius:5px;'>비교분석 할<br/>보고서명 선택 </p>",
                unsafe_allow_html=True
            )
             
        with col2:
            # 폴더 존재 확인 및 생성
            
            folder_list = bd.get_report_folder_list_from_github(st.session_state['github_repo'], st.session_state['github_branch'], st.session_state['github_token'])
        
            # st.selectbox 위젯 생성 (이제 session_state['selected_folder'] 사용 가능)

            # 'selected_folder'가 folder_list에 있을 때만 index 설정
            selected_index = st.session_state['selected_folder_index_02']
            if st.session_state['selected_folder_name_02'] in folder_list:
                selected_index = folder_list.index(st.session_state['selected_folder_name_02']) + 1
            #else:
                #selected_index = 0  # 기본값으로 '주제를 선택하세요.' 선택
            st.session_state['selected_folder_index_02'] = selected_index
            st.session_state['folder_list_option_02'] = [folderlist_init_value] + folder_list
            # 폴더 선택 selectbox 생성 (새 폴더 추가 후, 선택값으로 설정)
            selected_folder = st.selectbox(
                "등록된 보고서명 리스트",
                options=st.session_state['folder_list_option_02'],  # 옵션 리스트에 새 폴더 반영
                index=st.session_state['selected_folder_index_02'],  # 새로 선택된 폴더를 기본값으로 선택
                key="selected_folder"
            )
            # 파일 업로드와 요청사항 리스트의 기본 폴더 설정
            if selected_folder != folderlist_init_value:
                #st.session_state['upload_folder_02'] = f"uploadFiles/{selected_folder}"
                st.session_state['selected_folder_name_02'] = f"{selected_folder}"                  
                st.session_state['check_report_02']=False
                st.session_state['check_setting_02']=True
                st.session_state['selected_template_index_02'] = 0
                #st.success(f"[{selected_folder}] 보고서명이이 선택되었습니다.")
                
        
                # 하위 폴더 리스트(날짜 리스트) 가져오기
                subfolder_list, date_list = bd.get_subfolder_list(st.session_state['github_repo'], st.session_state['github_branch'], st.session_state['github_token'], selected_folder)
            #else:   
                #st.warning("보고서명을 선택하세요.")

      
else:
    st.warning("GitHub 정보가 설정되지 않았습니다. 먼저 GitHub Token을 입력해 주세요.")


# 3 프레임
# 보고서 타이틀 보기
col1, col2, col3 = st.columns([0.2, 0.6, 0.2])
with col1:
    st.write("")
with col2:   
    report_title = "작성할 보고서를 선택하세요."
    title_style="font-size:15px; font-weight:normal; color:#cccccc;border: 1px solid #dddddd;letter-spacing: 1px;"
    if 'selected_folder_name_02' in st.session_state:
        if st.session_state['selected_folder_name_02'] != folderlist_init_value:
            report_title = " [" + st.session_state['selected_folder_name_02'] + "] 보고서"
            title_style="font-size:20px; font-weight:bold; color:#000000;border: 0px solid #dddddd;letter-spacing: 4px;"
    st.markdown(
        f"<div style='text-align:center;{title_style};border-radius: 10px;width:100%;padding: 10px;margin-top:10px;margin-bottom:10px;'>{report_title}</div>",
        unsafe_allow_html=True
    )
   
with col3:
    st.write("")

# 4 프레임
# 작성 보고서 요청사항 세부타이틀
st.markdown(
    "<p style='font-size:18px; font-weight:bold; color:#007BFF;'>작성 보고서 요청사항</p>",
    unsafe_allow_html=True
)

# 5 프레임
# 요청사항 갯수 및 기준일자 설정 
with st.expander("⚙️ 요청사항 및 기준일자 설정", expanded=st.session_state['check_setting_02']):
    col1, col2 = st.columns([0.7,0.3])
    with col1:
        request_title = st.text_input("제목 : '제목을 입력해주세요.", key="request_title_input_02")
        st.session_state['request_title_02'] = request_title

        request_text = st.text_area("요청 : '요청할 내용을 입력해주세요.", key="request_text_area_02")
        st.session_state['request_text_02'] = request_text
    with col2:
        st.write("")
        st.write("")
        st.image("image/cheockcheock1_21.jpg",  use_column_width=True)
    
    if date_list:
        st.markdown(
            "<hr style='border-top:1px solid #dddddd;border-bottom:0px solid #dddddd;width:100%;padding:0px;margin:0px'></hr>",
            unsafe_allow_html=True
        )    
        today = datetime.date.today()
        # 시작일자와 마지막 일자 달력 입력
        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            if 'start_date_value' not in st.session_state:
                st.session_state['start_date_value'] = date_list[0]
            
            start_date = st.date_input("📅 시작일자 선택", 
                value=st.session_state['start_date_value'],
                min_value=date_list[0],
                max_value=today,
                key="start_date"
            )
            st.session_state['start_date_value'] = start_date
        with col2:            
            if 'end_date_value' not in st.session_state:
                st.session_state['end_date_value'] = today
            
            end_date = st.date_input("📅 마지막일자 선택", 
                value=st.session_state['end_date_value'],
                min_value=date_list[0],
                max_value=today,
                key="end_date"
            )
            st.session_state['end_date_value'] = end_date
       
# 6 프레임
# 보고서 작성 실행 버튼
col1, col2, col3 = st.columns([0.2, 0.6, 0.2])
with col1:
    st.write("")
with col2:   
# 보고서 실행 버튼 클릭 시 함수 호출 수정
    if st.button("🚀 보고서 작성 실행", key="generate_report", use_container_width=True):
        st.session_state['check_result_02']=True
        st.session_state['check_report_02'] = False
        st.session_state['check_setting_02'] = False
                
        if not st.session_state.get("openai_api_key"):
            st.error("먼저 OpenAI API 키를 입력하고 저장하세요!")
        elif not st.session_state['selected_folder_name_02'] or not st.session_state['request_title_02'] or not st.session_state['request_text_02'] or not st.session_state['start_date_value'] or not st.session_state['end_date_value']:
            st.error("보고서명, 요청사항, 기준일자을 모두 입력해야 합니다!")
        else:
            with st.spinner('요청사항과 보고서 파일 데이터를 추출 중입니다...'):
                 
                # 파일 데이터 가져와서 HTML 보고서 생성
                html_request = bd.fetch_report_data_between_dates(st.session_state['github_repo'], st.session_state['github_branch'], st.session_state['github_token'], selected_folder, start_date, end_date)
                st.session_state['html_report_02'] = html_request
                
                time.sleep(1)  # 예를 들어, 5초 동안 로딩 상태 유지

            with st.spinner('결과 보고서 작성 중입니다...'):
                # LLM 함수 호출
                title = st.session_state['request_title_02']
                request = st.session_state['request_text_02']
        
                responses = bd.run_llm_with_analysisfile_and_prompt(
                    st.session_state["openai_api_key"], 
                    title, 
                    request, 
                    st.session_state['html_report_02']
                )
                st.session_state['response_02'] = responses
                st.session_state['check_result_02'] = True
                time.sleep(1)  # 예를 들어, 5초 동안 로딩 상태 유지


with col3:
    st.write("")           

# 9 프레임
# 결과 보고서 세부 타이틀
st.markdown(
    "<p style='font-size:18px; font-weight:bold; color:#007BFF;'>결과 보고서</p>",
    unsafe_allow_html=True
)

# 10 프레임
# 결과 보고서 LLM 응답 보기/ 결과 보고서 저장/ 보고서 양식 저장
html_result_value = "<div id='html_result_value'>"
with st.expander("📊 결과 보고서 보기", expanded=st.session_state['check_result_02']):
    if "response_02" in st.session_state:
        st.markdown(
            "<hr style='border-top:1px solid #dddddd;border-bottom:0px solid #dddddd;width:100%;padding:0px;margin:0px'></hr>",
            unsafe_allow_html=True
        )  
        st.session_state['check_result_02'] = True


        for idx, response in enumerate(st.session_state["response_02"]):
            #st.text_area(f"응답 {idx+1}:", value=response, height=300)
            response_text, chartcode = bd.extract_text_within_brackets(response)
            
            fm, plt = bd.download_and_apply_font_from_github(st.session_state['github_repo'], st.session_state['github_branch'], fm, plt)
            #st.code(chartcode, language='python')  # 추출한 Python 코드를 화면에 출력
            st.markdown(
                  "<p style='font-size:22px;font-weight:bold;color:#CC66FF;padding:5px;'>📈 AI 추천 차트</p>",
                  unsafe_allow_html=True
            )
            # eval()을 사용하여 Python 코드를 실행하고 차트를 출력
            try:
                exec(chartcode)  # exec()을 사용하여 추출된 Python 코드를 실행
            except Exception as e:
                st.error(f"코드를 실행하는 중 오류가 발생했습니다: {str(e)}")
            
            # 추출된 코드를 화면에 출력
            st.markdown(
                "<hr style='border-top:1px solid #dddddd;border-bottom:0px solid #dddddd;width:100%;padding:0px;margin:0px'></hr>",
                unsafe_allow_html=True
            )   
            html_response_value = f"<div style='border: 0px solid #cccccc; padding: 1px;'>{response_text}</div>"
            html_result_value += html_response_value
            st.components.v1.html(html_response_value, height=1024, scrolling=True)

    html_result_value += "</div>"
    st.markdown(
        "<hr style='border-top:1px solid #dddddd;border-bottom:0px solid #dddddd;width:100%;padding:0px;margin:0px'></hr>",
        unsafe_allow_html=True
    )
    
# 결과 저장 버튼
    col1, col2 = st.columns([0.5, 0.5])
    with col1:   
        if st.button("💾 결과 내용 저장", key="save_result", use_container_width=True):
            st.session_state['check_result_02'] = True
            st.session_state['check_report_02'] = False
            st.session_state['check_setting_02'] = False
            st.session_state['check_request_02'] = False
            if "response_02" in st.session_state:                
                
                folder_name = st.session_state['selected_folder_name_02']
                report_date_str = st.session_state.get('report_date_str_02', datetime.datetime.now().strftime('%Y%m%d'))
                
                # save_html_response 함수를 사용하여 HTML 파일 저장
                file_name, temp_file_path = bd.save_html_response(html_result_value, folder_name, report_date_str)

                # 파일 저장 경로 (analysisReportFiles/{폴더명}/{일자})
                github_folder = f"analysisReportFiles/{folder_name}/{report_date_str}"

                # 폴더 존재 확인 및 생성
                bd.check_and_create_github_folder(github_folder, st.session_state['github_repo'], st.session_state['github_branch'], st.session_state['github_token'])
                
                # GitHub에 HTML 파일 저장
                sha = bd.get_file_sha(st.session_state['github_repo'], f"{github_folder}/{file_name}", st.session_state['github_token'], branch=st.session_state['github_branch'])
                bd.upload_file_to_github(st.session_state['github_repo'], github_folder, file_name, open(temp_file_path, 'rb').read(), st.session_state['github_token'], branch=st.session_state['github_branch'], sha=sha)
                st.session_state['check_result_02'] = True
                st.success(f"{file_name} 파일이 생성되었습니다.")
                if st.download_button(
                    label="📥 다운로드",
                    use_container_width=True,
                    data=open(temp_file_path, 'r', encoding='utf-8').read(),
                    file_name=file_name,
                    mime="text/html"
                ):
                    st.session_state['check_result_02'] = True
                    st.session_state['check_report_02'] = False
                    st.session_state['check_setting_02'] = False
                    st.session_state['check_request_02'] = False

            else:
                st.warning("결과 보고서를 먼저 실행하세요.")
    with col2:
        st.write("")
        #if st.button("🗃️ 보고서 양식 저장", key="save_template", use_container_width=True):
            #st.session_state['check_result_02'] = True
            #st.session_state['check_report_02'] = False
            #st.session_state['check_upload'] = False
            #st.session_state['check_setting_02'] = False
            #st.session_state['check_request'] = False
            #bd.save_template_to_json()

    
# Frontend 기능 구현 끝 ---

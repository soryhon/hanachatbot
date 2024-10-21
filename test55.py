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
folderlist_init_value = "보고서를 선택하세요."
templatelist_init_value = "불러올 보고서 양식을 선택하세요."
# 세션 상태에 각 변수 없다면 초기화
bd.init_session_state(False)
bd.refresh_page()

if 'selected_report_folder_index' not in st.session_state:
    st.session_state['selected_report_folder_index'] = 0
if 'selected_analysis_folder_index' not in st.session_state:
    st.session_state['selected_analysis_folder_index'] = 0
if 'selected_audio_folder_index' not in st.session_state:
    st.session_state['selected_audio_folder_index'] = 0
if 'selected_keyword_folder_index' not in st.session_state:
    st.session_state['selected_keyword_folder_index'] = 0
if 'selected_report_file_name' not in st.session_state:
    st.session_state['selected_report_file_name']=""
if 'selected_report_folder_name' not in st.session_state:
    st.session_state['selected_report_folder_name']=""
    
# 1 프레임
# 보고서 타이틀
col1, col2 = st.columns([0.55,0.45])
with col1:
    st.markdown(
        "<p style='font-size:25px; font-weight:bold; color:#000000;'>결과 보고서 현황 📋</p>",
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        "<div style='text-align:right;width:100%;'><p style='font-size:13px; font-weight:normal; color:#aaaaaa; margin-top:10px;'>by <b style='font-size:16px;color:#0099FF'>CheokCeock</b><b style='font-size:22px;color:#009999'>1</b> <b style='font-size:14px;'>prototype v.01</b></p></div>",
        unsafe_allow_html=True
    )

# 2 프레임
# 보고서명 및 폴더 선택, 새 폴더 만들기

if github_info_loaded:
    with st.expander("📝 보고서 선택", expanded=st.session_state['check_report']):
        tab1, tab2, tab3, tab4 = st.tabs(["• 업무 보고서", "• 보고서 비교분석","• 음성 파일 보고서","• Quickly 키워드 보고서"])
        folder_list =["reportFiles","analysisReportFiles","audioReportFiles", "keywordReportFiles"]

        # 2차원 배열에 각 폴더별 파일 리스트 저장
        file_lists = []
        
        # 각 폴더에 대해 파일 리스트 가져오기
        for folder_name in folder_list:
            # 각 폴더에서 파일 리스트를 가져와서 2차원 배열에 저장
            file_list = bd.get_reportType_file_list_from_github(
                st.session_state['github_repo'], 
                st.session_state['github_branch'], 
                st.session_state['github_token'], 
                folder_name
            )
            
            # 결과를 2차 배열에 추가
            file_lists.append(file_list)

        # 업무 보고서 자동 완성 리스트
        with tab1:            
            col1, col2 = st.columns([0.21, 0.79])
            with col1:
                st.write("")
                st.markdown(
                    "<p style='font-size:14px; font-weight:bold; color:#000000;text-align:center;'>업무 보고서<br/>리스트 선택 </p>",
                    unsafe_allow_html=True
                )
            with col2:
                # 폴더 존재 확인 및 생성
                # 'selected_file_name'가 file_list에 있을 때만 index 설정
                #selected_index = st.session_state['selected_report_folder_index']
                report_file_list = [folderlist_init_value] + file_lists[0]
                # 폴더 선택 selectbox 생성 (새 폴더 추가 후, 선택값으로 설정)
                selected_file_name = st.selectbox(
                    "등록된 보고서명 리스트",
                    options=report_file_list,  # 옵션 리스트에 새 폴더 반영
                    index=st.session_state['selected_report_folder_index'],  # 새로 선택된 폴더를 기본값으로 선택
                    key="selected_report_folder"
                )
                # 파일 업로드와 요청사항 리스트의 기본 폴더 설정
                if selected_file_name != folderlist_init_value:
                    st.session_state['selected_report_file_name'] = f"{selected_file_name}"
                    st.session_state['selected_report_folder_name'] = f"{folder_list[0]}"
                    st.session_state['selected_report_folder_index'] = file_list.index(selected_file_name) + 1
                    st.session_state['selected_analysis_folder_index'] = 0
                    st.session_state['selected_audio_folder_index'] = 0
                    st.session_state['selected_keyword_folder_index'] = 0
                    st.session_state['check_report']=False

                    #bd.refresh_page()
                    st.success(f"[{selected_file_name}] 보고서명이 선택되었습니다.")  


        # 보고서 비교분석 완성 리스트
        with tab2:            
            col1, col2 = st.columns([0.21, 0.79])
            with col1:
                st.write("")
                st.markdown(
                    "<p style='font-size:14px; font-weight:bold; color:#000000;text-align:center;'>보고서 비교분석<br/>리스트 선택 </p>",
                    unsafe_allow_html=True
                )
            with col2:
                # 폴더 존재 확인 및 생성
                # 'selected_file_name'가 file_list에 있을 때만 index 설정
                #selected_index = st.session_state['selected_analysis_folder_index']
                report_file_list = [folderlist_init_value] + file_lists[1]
                # 폴더 선택 selectbox 생성 (새 폴더 추가 후, 선택값으로 설정)
                selected_file_name = st.selectbox(
                    "등록된 보고서명 리스트",
                    options=report_file_list,  # 옵션 리스트에 새 폴더 반영
                    index=st.session_state['selected_analysis_folder_index'],  # 새로 선택된 폴더를 기본값으로 선택
                    key="selected_analysis_folder"
                )
                # 파일 업로드와 요청사항 리스트의 기본 폴더 설정
                if selected_file_name != folderlist_init_value:
                    st.session_state['selected_report_file_name'] = f"{selected_file_name}"
                    st.session_state['selected_report_folder_name'] = f"{folder_list[1]}"
                    st.session_state['selected_analysis_folder_index'] = file_list1.index(selected_file_name) + 1
                    st.session_state['selected_report_folder_index'] = 0
                    st.session_state['selected_audio_folder_index'] = 0
                    st.session_state['selected_keyword_folder_index'] = 0
                    st.session_state['check_report']=False
                    
                    #bd.refresh_page()
                    st.success(f"[{selected_file_name}] 보고서명이 선택되었습니다.")  

        # 음성파일 보고서 완성 리스트
        with tab3:            
            col1, col2 = st.columns([0.21, 0.79])
            with col1:
                st.write("")
                st.markdown(
                    "<p style='font-size:14px; font-weight:bold; color:#000000;text-align:center;'>음성파일 보고서<br/>리스트 선택 </p>",
                    unsafe_allow_html=True
                )
            with col2:
                # 폴더 존재 확인 및 생성
                # 'selected_file_name'가 file_list에 있을 때만 index 설정
                #selected_index = st.session_state['selected_audio_folder_index']
                report_file_list = [folderlist_init_value] + file_lists[2]
                # 폴더 선택 selectbox 생성 (새 폴더 추가 후, 선택값으로 설정)
                selected_file_name = st.selectbox(
                    "등록된 보고서명 리스트",
                    options=report_file_list,  # 옵션 리스트에 새 폴더 반영
                    index=st.session_state['selected_audio_folder_index'],  # 새로 선택된 폴더를 기본값으로 선택
                    key="selected_audio_folder"
                )
                # 파일 업로드와 요청사항 리스트의 기본 폴더 설정
                if selected_file_name != folderlist_init_value:
                    st.session_state['selected_report_file_name'] = f"{selected_file_name}"
                    st.session_state['selected_report_folder_name'] = f"{folder_list[2]}"
                    st.session_state['selected_audio_folder_index'] = file_list2.index(selected_file_name) + 1
                    st.session_state['selected_analysis_folder_index'] = 0
                    st.session_state['selected_report_folder_index'] = 0
                    st.session_state['selected_keyword_folder_index'] = 0
                    st.session_state['check_report']=False
                    
                    #bd.refresh_page()
                    st.success(f"[{selected_file_name}] 보고서명이 선택되었습니다.")  


        # Quickly 키워드 보고서 리스트
        with tab4:            
            col1, col2 = st.columns([0.21, 0.79])
            with col1:
                st.write("")
                st.markdown(
                    "<p style='font-size:14px; font-weight:bold; color:#000000;text-align:center;'>키워드 보고서<br/>리스트 선택 </p>",
                    unsafe_allow_html=True
                )
            with col2:
                # 폴더 존재 확인 및 생성
                # 'selected_file_name'가 file_list에 있을 때만 index 설정
                #selected_index = st.session_state['selected_keyword_folder_index']
                report_file_list = [folderlist_init_value] + file_lists[3]
                # 폴더 선택 selectbox 생성 (새 폴더 추가 후, 선택값으로 설정)
                selected_file_name = st.selectbox(
                    "등록된 보고서명 리스트",
                    options=report_file_list,  # 옵션 리스트에 새 폴더 반영
                    index=st.session_state['selected_keyword_folder_index'],  # 새로 선택된 폴더를 기본값으로 선택
                    key="selected_keyword_folder"
                )
                # 파일 업로드와 요청사항 리스트의 기본 폴더 설정
                if selected_file_name != folderlist_init_value:
                    st.session_state['selected_report_file_name'] = f"{selected_file_name}"
                    st.session_state['selected_report_folder_name'] = f"{folder_list[3]}"
                    st.session_state['selected_keyword_folder_index'] = file_list3.index(selected_file_name) + 1
                    st.session_state['selected_report_folder_index'] = 0
                    st.session_state['selected_audio_folder_index'] = 0
                    st.session_state['selected_analysis_folder_index'] = 0
                    st.session_state['check_report']=False
                    
                    #bd.refresh_page()
                    st.success(f"[{selected_file_name}] 보고서명이 선택되었습니다.")  
      
else:
    st.warning("GitHub 정보가 설정되지 않았습니다. 먼저 GitHub Token을 입력해 주세요.")


          
# 9 프레임
# 결과 보고서 세부 타이틀
st.markdown(
    "<p style='font-size:18px; font-weight:bold; color:#007BFF;'>결과 보고서</p>",
    unsafe_allow_html=True
)

# 10 프레임
# 결과 보고서 LLM 응답 보기/ 결과 보고서 저장/ 보고서 양식 저장
html_result_value = "<div id='html_result_value'>"
with st.expander("📊 결과 보고서 보기", expanded=st.session_state['check_result']):
    if "selected_report_file_name" in st.session_state and st.session_state['selected_report_file_name']:
        st.markdown(
            "<hr style='border-top:1px solid #dddddd;border-bottom:0px solid #dddddd;width:100%;padding:0px;margin:0px'></hr>",
            unsafe_allow_html=True
        )  
        st.session_state['check_result'] = True
        result_folder = st.session_state['selected_report_folder_name']
        result_file = st.session_state['selected_report_file_name']
        result_path = f"{result_folder}/{result_file}"
        # GitHub에서 HTML 파일 데이터 가져오기
        file_content = bd.get_file_from_github(
            st.session_state['github_repo'], 
            st.session_state['github_branch'], 
            f"{result_path}",  # 폴더 경로와 파일 이름을 합침
            st.session_state['github_token']
        )
        
        if file_content:
            # HTML 파일 내용을 화면에 출력
            #st.markdown(file_content, unsafe_allow_html=True)
            st.components.v1.html(file_content, height=1024, scrolling=True)
        else:
            st.error(f"{selected_file} 파일 데이터를 가져오는 데 실패했습니다.")


            

    html_result_value += "</div>"
    st.markdown(
        "<hr style='border-top:1px solid #dddddd;border-bottom:0px solid #dddddd;width:100%;padding:0px;margin:0px'></hr>",
        unsafe_allow_html=True
    )
    
# 결과 저장 버튼
    col1, col2 = st.columns([0.5, 0.5])
    with col1:   
        if st.button("💾 결과 내용 저장", key="save_result", use_container_width=True):
            st.session_state['check_result'] = True
            st.session_state['check_report'] = False
            st.session_state['check_upload'] = False
            st.session_state['check_setting'] = False
            st.session_state['check_request'] = False
            if "response" in st.session_state:                
                
                folder_name = st.session_state['selected_folder_name']
                report_date_str = st.session_state.get('report_date_str', datetime.datetime.now().strftime('%Y%m%d'))
                
                # save_html_response 함수를 사용하여 HTML 파일 저장
                file_name, temp_file_path = bd.save_html_response(html_result_value, folder_name, report_date_str)

                # 파일 저장 경로 (analysisReportFiles/{폴더명}/{일자})
                github_folder = f"analysisReportFiles/{folder_name}/{report_date_str}"

                # 폴더 존재 확인 및 생성
                bd.check_and_create_github_folder(github_folder, st.session_state['github_repo'], st.session_state['github_branch'], st.session_state['github_token'])
                
                # GitHub에 HTML 파일 저장
                sha = bd.get_file_sha(st.session_state['github_repo'], f"{github_folder}/{file_name}", st.session_state['github_token'], branch=st.session_state['github_branch'])
                bd.upload_file_to_github(st.session_state['github_repo'], github_folder, file_name, open(temp_file_path, 'rb').read(), st.session_state['github_token'], branch=st.session_state['github_branch'], sha=sha)
                st.session_state['check_result'] = True
                st.success(f"{file_name} 파일이 생성되었습니다.")
                if st.download_button(
                    label="📥 다운로드",
                    use_container_width=True,
                    data=open(temp_file_path, 'r', encoding='utf-8').read(),
                    file_name=file_name,
                    mime="text/html"
                ):
                    st.session_state['check_result'] = True
                    st.session_state['check_report'] = False
                    st.session_state['check_upload'] = False
                    st.session_state['check_setting'] = False
                    st.session_state['check_request'] = False

            else:
                st.warning("결과 보고서를 먼저 실행하세요.")
    with col2:
        st.write("")


# 11 프레임
# 결과 보고서 HTML 보기
#if "html_report" in st.session_state:
    #st.write("파일 데이터 추출 보기")
    #html_report_value = f"<div style='border: 2px solid #cccccc; padding: 2px;'>{st.session_state['html_report']}</div>"
    #st.components.v1.html(html_report_value, height=10240, scrolling=True)

# 12 프레임
# 전달된 프롬프트
#st.text_area("전달된 프롬프트:", value="\n\n".join(global_generated_prompt), height=150)
    
# Frontend 기능 구현 끝 ---

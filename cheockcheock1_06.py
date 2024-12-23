import streamlit as st
import pandas as pd
import os
from datetime import datetime
import backend as bd

# Frontend 기능 구현 시작 ---

# GitHub 정보가 있는지 확인하고 파일 업로드 객체를 출력
github_info_loaded = bd.load_env_info()

# 1 프레임
# 보고서 타이틀
col1, col2 = st.columns([0.55,0.45])
with col1:
    st.markdown(
        "<p style='font-size:25px; font-weight:bold; color:#000000;'>사용자 만족도 평가 🏆</p>",
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        "<div style='text-align:right;width:100%;'><p style='font-size:15px; font-weight:normal; color:#aaaaaa;margin-top:10px;'>by <b style='font-size:16px;color:#0099FF'>CheockCheock</b><b style='font-size:22px;color:#009999'>1</b> <b style='font-size:14px;'>prototype v.01</b></p></div>",
        unsafe_allow_html=True
    )

if github_info_loaded:
    with st.expander("✏️ 만족도 평가하기", expanded=True):
        col1, col2 = st.columns([0.21, 0.79])
        with col1:
            st.write("")
            st.markdown(
                "<p style='font-size:14px; font-weight:bold; color:#000000;text-align:center;border:1px solid #E7EAF1;margin-top:10px;border-radius:5px;'>닉네임 또는 이름<br/>입력</p>",
                unsafe_allow_html=True
            )
        with col2:
            nickname = st.text_input("닉네임 또는 이름을 입력하세요:")
        st.markdown(
            "<hr style='border-top:1px solid #dddddd;border-bottom:0px solid #dddddd;width:100%;padding:0px;margin:0px'></hr>",
            unsafe_allow_html=True
        ) 
        col1, col2, col3 = st.columns([0.07, 0.82, 0.11])
        with col1:
            st.write("")
        with col2:
            # 별점 선택 (슬라이더 사용)
            score = st.slider("✔ 만족도 별점을 아래의 슬라이드바를 움직여서 선택해주세요. (1~5점 까지):", 1.0, 5.0, 1.0)
        with col3:
            st.write("")   
        # score에 따라 이미지 설정
        star_images = bd.get_star_images(score)
        
        # 별 이미지를 표시할 5개의 열 생성
        col1, col2, col3, col4, col5 = st.columns([0.2, 0.2, 0.2, 0.2, 0.2])
        
        # 각 열에 맞는 별 이미지 출력
        with col1:  # score 1점 별
            st.image(star_images[0], width=95)
        with col2:  # score 2점 별
            st.image(star_images[1], width=95)
        with col3:  # score 3점 별
            st.image(star_images[2], width=95)
        with col4:  # score 4점 별
            st.image(star_images[3], width=95)
        with col5:  # score 5점 별
            st.image(star_images[4], width=95)
   

    col1, col2, col3 = st.columns([0.2, 0.6, 0.2])
    with col1:
        st.write("")
    with col2:
        # 평가 버튼
        if st.button("🎯 평가하기", key="appraisal", use_container_width=True):
            if nickname and score:
                file_path = "satisfaction/appraisal.csv"
                bd.add_to_csv(nickname, score, st.session_state['github_token'], st.session_state['github_repo'], st.session_state['github_branch'], file_path)
                st.success(f"{nickname}님의 평가가 성공적으로 등록되었습니다!")
            else:
                st.error("닉네임/이름과 별 개수 선택은 필수입니다.")
    with col3:
        st.write("")
        
    col1, col2, col3 = st.columns([0.25, 0.5, 0.25]) 
    with col1:
        st.write("")
    with col2:
        st.image("image/cheockcheock1_61.jpg",  use_column_width=True)
    with col3:
        st.write("")

    # 버튼 이미지 URL (로컬 이미지 경로를 사용하려면 외부로 로드하는 방식이 필요합니다.)
    button_image_url = "https://raw.githubusercontent.com/soryhon/hanachatbot/refs/heads/main/image/cheockcheock1_6.jpg"
    
    # HTML을 사용한 버튼 생성
    button_html = f"""
    <div style="display: flex; justify-content: center;">
        <form action="" method="get">
            <button style="background-color: transparent; border: none; cursor: pointer;">
                <img src="{button_image_url}" alt="Button Image" style="width: 50px; height: 50px;">
            </button>
        </form>
    </div>
    """
    
    # HTML 버튼을 삽입
    st.markdown(button_html, unsafe_allow_html=True)
    
    # 버튼 클릭 처리
    if st.button("이미지 버튼으로 클릭"):
        st.write("버튼이 클릭되었습니다!")
else:
    st.warning("GitHub 정보가 설정되지 않았습니다. 먼저 GitHub Token을 입력해 주세요.")








    


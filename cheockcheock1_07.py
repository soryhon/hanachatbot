import streamlit as st
import pandas as pd
import datetime
import backend as bd

# appraisal.csv 파일 경로
file_path = "satisfaction/appraisal.csv"

# 데이터 로드 및 기본 정보 표시
total_count, average_score, appraisal_data = bd.get_appraisal_data(file_path)
if appraisal_data is not None:
    col1 , col2 = st.columns([0.5,0.5])
    with col1:
      st.title(f"총 평가 건수: {total_count}건")
    with col2:
      st.write(f"평균 점수: {average_score:.2f}")

    # 시작일자와 종료일자를 설정
    start_date, end_date = bd.get_date_range(appraisal_data)
    if start_date and end_date:
        st.write(f"데이터 범위: {start_date.date()} ~ {end_date.date()}")
        
        # 달력 입력창 추가
        selected_start_date = st.date_input("시작일자 선택", value=start_date)
        selected_end_date = st.date_input("종료일자 선택", value=end_date)
        
        # [추첨하기] 버튼을 클릭하면, 기간 내 랜덤으로 1건 추출
        if st.button("🎉 추첨하기"):
            random_entry = bd.get_random_appraisal_in_range(appraisal_data, selected_start_date, selected_end_date)
            if random_entry is not None:
                st.write(f"닉네임: {random_entry['Nickname']}")
                st.write(f"평가 점수: {random_entry['Score']}")
                st.write(f"날짜: {random_entry['DATE']}")
            else:
                st.write("선택한 기간 내 데이터가 없습니다.")
else:
    st.write("평가 데이터를 불러올 수 없습니다.")

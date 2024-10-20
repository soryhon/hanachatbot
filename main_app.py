import streamlit as st
import importlib
import os
import backend as bd
import time

# 세션 상태에 radio_visible 변수가 없다면 False로 초기화
def init_menu(idx):
    if not idx:
        idx = 0
    
    if 'menu01' not in st.session_state:
        st.session_state['menu01'] = True
    if 'menu02' not in st.session_state:
        st.session_state['menu02'] = False
    if 'menu03' not in st.session_state:
        st.session_state['menu03'] = False
    if 'menu05' not in st.session_state:
        st.session_state['menu04'] = False   
    if 'selected_menu01_index' not in st.session_state:
        st.session_state['selected_menu01_index'] =0
    if idx == 1:
        st.session_state['menu01'] = False
        st.session_state['menu02'] = True
        st.session_state['menu03'] = False
        st.session_state['menu04'] = False
        st.session_state['selected_menu01_index'] =0
    elif idx == 2:
        st.session_state['menu01'] = False
        st.session_state['menu02'] = False
        st.session_state['menu03'] = True
        st.session_state['menu04'] = False
        st.session_state['selected_menu01_index'] = 0
    elif idx == 3:
        st.session_state['menu01'] = False
        st.session_state['menu02'] = False
        st.session_state['menu03'] = False
        st.session_state['menu04'] = True
        st.session_state['selected_menu01_index'] = 0
    else:
        st.session_state['menu01'] = True
        st.session_state['menu02'] = False
        st.session_state['menu03'] = False
        st.session_state['menu04'] = False
    

  
        
init_menu(0)
sub_menu_list=['📚업무 보고서 자동 완성', '📈보고서 비교분석 자동 완성', '🎧음성 파일 보고서 완성', '⚡Quickly 키워드 검색 보고서','📋결과 보고서 현황', '👥프로젝트 및 팀 소개', '🏆만족도 평가']
file_list=["test50.py","test51.py","test53.py","","","team_info.py",""]
menu_list=['보고서 자동 완성', '결과 보고서 현황', '챌린지5팀 소개', '만족도 평가']

# 사이드바에 메뉴 추가
st.sidebar.markdown(
    """
    <div style='background-color:#E7EAF1;text-align:center;width:100%;padding-bottom:6px;border-radius:8px;'>
    <b style='font-size:22px;color:#0099FF;font-style:italic;'>CheokCeock</b><b style='font-size:30px;color:#009999;'>☝️</b>
    </div>
    """,
    unsafe_allow_html=True
)


selected_menu = st.sidebar.selectbox("메뉴 선택하세요.", sub_menu_list, index=st.session_state['selected_menu01_index'])
if selected_menu:
    idx  = sub_menu_list.index(selected_menu)
    st.session_state['selected_menu01_index'] = idx
    selected_file = file_list[idx]
    bd.exec_page(selected_file)
else:
    st.session_state['selected_menu01_index'] = 0
    



st.sidebar.markdown(
    """
    <div style='font-size:12px; font-weight:normal; color:#999999;text-align:center;width:90%;border-top:0px dotted #cccccc;margin-left:5%;margin-right:5%'>ⓒ LepoLab. Challenger_5 Team</div>
    """,
    unsafe_allow_html=True
)

import streamlit as st
import importlib
import os
import backend as bd

# 세션 상태에 radio_visible 변수가 없다면 False로 초기화
def selected_menu(idx):
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

    if idx == 1:
        st.session_state['menu01'] = False
        st.session_state['menu02'] = True
        st.session_state['menu03'] = False
        st.session_state['menu04'] = False
    elif idx == 2:
        st.session_state['menu01'] = False
        st.session_state['menu02'] = False
        st.session_state['menu03'] = True
        st.session_state['menu04'] = False
    elif idx == 3:
        st.session_state['menu01'] = False
        st.session_state['menu02'] = False
        st.session_state['menu03'] = False
        st.session_state['menu04'] = True
    else:
        st.session_state['menu01'] = True
        st.session_state['menu02'] = False
        st.session_state['menu03'] = False
        st.session_state['menu04'] = False

  
        
selected_menu(0)
sub_menu_list=['업무 보고서 자동 완성', '보고서 비교분석 자동 완성', '음성 파일 보고서 완성', 'Quickly 키워드 검색 보고서']
file_list=["test50.py","test51.py","test53.py",""]
menu_list=['보고서 자동 완성', '결과 보고서 현황', '챌린지5팀 소개', '만족도 평가']

# 사이드바에 메뉴 추가
st.sidebar.markdown(
    """
    <div style='text-align:center;width:100%;'><b style='font-size:22px;color:#0099FF;font-style:italic;'>📝CheokCeock</b><b style='font-size:30px;color:#009999'>1</b></div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown(
    "<p style='background-color:#E7EAF1;border-radius: 5px;font-size:15px; font-weight:bold; color:#090909;text-align:center;width:100%;padding:8px;border:0px solid #cccccc;margin-top:15px;'>보고서 유형 선택</p>",
    unsafe_allow_html=True
)

selected_menu = st.sidebar.selectbox("보고서 유형 선택하세요.", ["사용할 유형 선택하세요."]+sub_menu_list)
if selected_menu != "사용할 유형 선택하세요.":
    selected_menu(0)
    if st.session.state["menu01"] == True:
        idx  = sub_menu_list.index(selected_menu)
        selected_file = file_list[idx]
        bd.exec_page(selected_file)

st.sidebar.markdown(
    """
    <div style='font-size:12px; font-weight:bold; color:#007BFF;text-align:center;width:90%;border-top:1px dotted #cccccc;margin-left:5%;margin-right:5%'></div>
    """,
    unsafe_allow_html=True
)
if st.sidebar.button("결과 보고서 현황", key="button_menu02",use_container_width=True):
    if st.session_state['menu01'] == True:
        st.session_state['menu01']=False
    else:
        st.session_state['menu01']=True
        
if st.sidebar.button("챌린지5팀 소개", key="button_menu03",use_container_width=True):
    selected_menu(2)
    if st.session.state["menu03"] == True:
        selected_file = 'team_info.py'
        bd.exec_page(selected_file)

if st.sidebar.button("만족도 평가", key="button_menu04",use_container_width=True):
    if st.session_state['menu01'] == True:
        st.session_state['menu01']=False
    else:
        st.session_state['menu01']=True
        




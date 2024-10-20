import streamlit as st
import importlib
import os

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

def exec_page(file_name):
    if file_name:
        with open(file_name, 'r') as file:
                file_content = file.read()
            
        # 파일 내용을 화면에 출력
        #st.code(file_content, language='python')
        try:
            exec(file_content)  # exec()을 사용하여 추출된 Python 코드를 실행
        except Exception as e:
            st.error(f"코드를 실행하는 중 오류가 발생했습니다: {str(e)}")    
        
selected_menu(0)
sub_menu_list=['업무 보고서 자동 완성', '보고서 비교분석 자동 완성', '음성 파일 보고서 완성', 'Quickly 키워드 검색 보고서']
file_list=["test50.py","test51.py","test53.py",""]
menu_list=['보고서 자동 완성', '결과 보고서 현황', '챌린지5팀 소개', '만족도 평가']

# 사이드바에 메뉴 추가
st.sidebar.markdown(
    """
    <div style='text-align:right;width:100%;'><p style='font-size:18px; font-weight:normal; color:#aaaaaa; margin-top:10px;'>by <b style='font-size:16px;color:#0099FF'>CheokCeock</b><b style='font-size:24px;color:#009999'>1</b></p></div>",
    """,
    unsafe_allow_html=True
)


selected_menu = st.sidebar.selectbox("보고서 유형", sub_menu_list)
if selected_menu:
    idx  = sub_menu_list.index(selected_menu)
    selected_file = file_list[idx]
    exec_page(selected_file)

if st.sidebar.button("결과 보고서 현황", key="button_menu02",use_container_width=True):
    if st.session_state['menu01'] == True:
        st.session_state['menu01']=False
    else:
        st.session_state['menu01']=True
        
if st.sidebar.button("챌린지5팀 소개", key="button_menu03",use_container_width=True):
    if st.session_state['menu01'] == True:
        st.session_state['menu01']=False
    else:
        st.session_state['menu01']=True

if st.sidebar.button("만족도 평가", key="button_menu04",use_container_width=True):
    if st.session_state['menu01'] == True:
        st.session_state['menu01']=False
    else:
        st.session_state['menu01']=True
        
st.sidebar.markdown(
    "<p style='font-size:18px; font-weight:bold; color:#007BFF;text-align:center;width:100%;border:0px solid #000000;'>보고서 자동 완성</p>",
    unsafe_allow_html=True
)


        

selected_menu = st.radio("radio", ['보고서 자동 완성', '결과 보고서 현황', '챌린지5팀 소개', '만족도 평가'])
if st.form_submit_button("업무 보고서 자동 완성", use_container_width=True):        
    selected_menu(0)

with st.sidebar.form("보고서 자동 완성", clear_on_submit=False):

    if st.form_submit_button("업무 보고서 자동 완성", use_container_width=True):        
        selected_menu(0)
        # 선택한 Python 파일 내용 읽기
        selected_file = "test50.py"
        exec_page(selected_file)
    if st.form_submit_button("보고서 비교분석 자동 완성", use_container_width=True):        
        selected_menu(0)
        # 선택한 Python 파일 내용 읽기
        selected_file = "test51.py"
        exec_page(selected_file)
    if st.form_submit_button("음성 파일 보고서 완성", use_container_width=True):        
        selected_menu(0)
        # 선택한 Python 파일 내용 읽기
        selected_file = "test53.py"
        exec_page(selected_file)
    if st.form_submit_button("'Quickly 키워드 검색 보고서", use_container_width=True):        
        selected_menu(0)
        st.write("Quickly 키워드 검색 보고서")
        # 선택한 Python 파일 내용 읽기
        #selected_file = "test50.py"
        #exec_page(selected_file)



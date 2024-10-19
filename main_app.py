import streamlit as st
import importlib
import os

# 세션 상태에 radio_visible 변수가 없다면 False로 초기화
if 'menu01' not in st.session_state:
    st.session_state['menu01'] = True
if 'menu02' not in st.session_state:
    st.session_state['menu02'] = False
if 'menu03' not in st.session_state:
    st.session_state['menu03'] = False
if 'menu05' not in st.session_state:
    st.session_state['menu04'] = False   

# 버튼 클릭 시 radio_visible 값 변경
if st.sidebar.button("보고서 자동 완성", use_container_width=True):
    st.session_state['menu01'] = True
    st.session_state['menu02'] = False
    st.session_state['menu03'] = False
    st.session_state['menu04'] = False

if st.session_state['menu01']:
    selected_menu01_option = st.sidebar.radio("", ['업무 보고서 자동 완성', '보고서 비교분석 자동 완성', '음성 파일 보고서 완성'])

if st.sidebar.button("결과 보고서 확인", use_container_width=True):
    st.session_state['menu01'] = False
    st.session_state['menu02'] = True
    st.session_state['menu03'] = False
    st.session_state['menu04'] = False

if st.session_state['menu02']:
    selected_menu02_button = st.sidebar.button("결과 보고서 현황")

if st.sidebar.button("챌린지5팀 소개", use_container_width=True):
    st.session_state['menu01'] = False
    st.session_state['menu02'] = False
    st.session_state['menu03'] = True
    st.session_state['menu04'] = False

if st.session_state['menu03']:
    st.sidebar.write("챌린지5팀 소개")

if st.sidebar.button("만족도 평가", use_container_width=True):
    st.session_state['menu01'] = False
    st.session_state['menu02'] = False
    st.session_state['menu03'] = False
    st.session_state['menu04'] = True







if st.session_state['menu04']:
    st.write("만족도 평가")
    
# 사이드바에 메뉴 추가
page = st.sidebar.radio('Choose a page', ['Home', '업무 보고서 자동 완성', '보고서 비교분석 자동 완성', '음성 파일 보고서 완성'])

# 홈 페이지 설정
if page == 'Home':
    st.title("Welcome to the Home Page")
    st.write("This is the main page of the application.")

# Page 1 선택 시 'cheokcheok1_01.py' 실행
elif page == '업무 보고서 자동 완성':
    # 선택한 Python 파일 내용 읽기
    selected_file = "test50.py"
    with open(selected_file, 'r') as file:
        file_content = file.read()
    
    # 파일 내용을 화면에 출력
    #st.code(file_content, language='python')
    try:
        exec(file_content)  # exec()을 사용하여 추출된 Python 코드를 실행
    except Exception as e:
        st.error(f"코드를 실행하는 중 오류가 발생했습니다: {str(e)}")

# Page 2 선택 시 'cheokcheok1_02.py' 실행
elif page == '보고서 비교분석 자동 완성':
    # 선택한 Python 파일 내용 읽기
    selected_file = "test51.py"
    with open(selected_file, 'r') as file:
        file_content = file.read()
    
    # 파일 내용을 화면에 출력
    #st.code(file_content, language='python')
    try:
        exec(file_content)  # exec()을 사용하여 추출된 Python 코드를 실행
    except Exception as e:
        st.error(f"코드를 실행하는 중 오류가 발생했습니다: {str(e)}")
elif page == '음성 파일 보고서 완성':
    # 선택한 Python 파일 내용 읽기
    selected_file = "test53.py"
    with open(selected_file, 'r') as file:
        file_content = file.read()
    
    # 파일 내용을 화면에 출력
    #st.code(file_content, language='python')
    try:
        exec(file_content)  # exec()을 사용하여 추출된 Python 코드를 실행
    except Exception as e:
        st.error(f"코드를 실행하는 중 오류가 발생했습니다: {str(e)}")

# 세션 상태에 radio_visible 변수가 없다면 False로 초기화
if 'radio_visible' not in st.session_state:
    st.session_state['radio_visible'] = False

# 버튼 클릭 시 radio_visible 값 변경
if st.sidebar.button("옵션 선택하기"):
    st.session_state['radio_visible'] = True

# 버튼이 클릭되었을 때만 radio 버튼 표시
if st.session_state['radio_visible']:
    selected_option = st.sidebar.radio("옵션을 선택하세요", ["옵션 1", "옵션 2", "옵션 3"])
    
    # 선택한 옵션을 화면에 표시
    st.write(f"선택한 옵션: {selected_option}")

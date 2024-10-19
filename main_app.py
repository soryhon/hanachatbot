import streamlit as st
import importlib
import os

# 사이드바에 메뉴 추가
page = st.sidebar.selectbox('Choose a page', ['Home', '업무 보고서 자동 완성', 'Page 2'])

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
elif page == 'Page 2':
    st.title("Page 2")
    cheokcheok1_02 = importlib.import_module('test51')
    #cheokcheok1_02.show()

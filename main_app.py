import streamlit as st
import importlib

# 사이드바에 메뉴 추가
page = st.sidebar.selectbox('Choose a page', ['Home', 'Page 1', 'Page 2'])

# 홈 페이지 설정
if page == 'Home':
    st.title("Welcome to the Home Page")
    st.write("This is the main page of the application.")

# Page 1 선택 시 'cheokcheok1_01.py' 실행
elif page == 'Page 1':
    st.title("Page 1")
    cheokcheok1_01 = importlib.import_module('test50')
    cheokcheok1_01.show()

# Page 2 선택 시 'cheokcheok1_02.py' 실행
elif page == 'Page 2':
    st.title("Page 2")
    cheokcheok1_02 = importlib.import_module('test51')
    cheokcheok1_02.show()

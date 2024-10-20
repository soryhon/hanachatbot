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
    <div style='text-align:center;width:100%;'><b style='font-size:22px;color:#0099FF;font-style:italic;'>📝CheokCeock</b><b style='font-size:30px;color:#009999'>1</b></div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown(
    "<p style='background-color:#E7EAF1;border-radius: 5px;font-size:15px; font-weight:bold; color:#090909;text-align:center;width:100%;padding:8px;border:0px solid #cccccc;margin-top:15px;'>보고서 유형 선택</p>",
    unsafe_allow_html=True
)

selected_menu = st.sidebar.selectbox("보고서 유형 선택하세요.", sub_menu_list)
if selected_menu:
    idx  = sub_menu_list.index(selected_menu)
    selected_file = file_list[idx]
    exec_page(selected_file)

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
    # 1 프레임
    # 보고서 타이틀
    col1, col2 = st.columns([0.55, 0.45])
    with col1:
        st.markdown(
            "<p style='font-size:25px; font-weight:bold; color:#000000;'>✨ 프로젝트 및 팀원소개 ✨</p>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            "<div style='text-align:right;width:100%;'><p style='font-size:13px; font-weight:normal; color:#aaaaaa; margin-top:10px;'>by <b style='font-size:16px;color:#0099FF'>CheokCeock</b><b style='font-size:22px;color:#009999'>1</b> <b style='font-size:14px;'>prototype v.01</b></p></div>",
            unsafe_allow_html=True
        )

    st.markdown("<hr style='border-top:1px solid #dddddd;'>", unsafe_allow_html=True)
    st.markdown("## 프로젝트 소개")    
    with st.container():
        st.image("checkcheck.jpg", width=150)
        st.markdown("### CheokCeock1")
        st.markdown("""
            **추진 배경**  
            **매일 반복적이고 고정된 형식의 업무 처리 및 보고서 작성 수행을 보다 효율적으로 자동화하여 시간 절약 및 정확도를 개선 하기 위함.**  
        """)
    

    # 팀원 소개 섹션
    st.markdown("<hr style='border-top:1px solid #dddddd;'>", unsafe_allow_html=True)
    st.markdown("## 팀원 소개")

    # 팀원 1 소개
    with st.container():
#        st.image("team_member1.jpg", width=150)  # 팀원 1의 이미지 경로
        st.markdown("### 고종현 과장(인프라보안팀)")
        st.markdown("""
            **역할**: 팀 리더👑  
            **소개**: 고종현 팀장은 풍부한 경험과 탁월한 리더십으로 팀을 이끌었고, 그의 전략적 사고와 문제 해결 능력은 프로젝트의 성공적으로 이끌었습니다.  
        """)
#        st.markdown("<hr style='border-top:1px solid #dddddd;'>", unsafe_allow_html=True)  # 구분선

    # 팀원 2 소개
    with st.container():
#        st.image("team_member2.jpg", width=150)
        st.markdown("### 정도용 차장(내부통제지원팀)")
        st.markdown("""
            **역할**: 데이터 분석가👨‍💻  
            **소개**: 정도용 팀원의 심도 있는 데이터 분석 능력은 프로젝트의 핵심 인사이트를 도출하는 데 큰 도움이 되었습니다.  
        """)
#        st.markdown("<hr style='border-top:1px solid #dddddd;'>", unsafe_allow_html=True)  # 구분선    
        
    # 팀원 3 소개
    with st.container():
#        st.image("team_member3.jpg", width=150)  # 팀원 3의 이미지 경로
        st.markdown("### 김상영 대리(외환팀)")
        st.markdown("""
            **역할**: 프론트엔드 개발자👨‍💻  
            **소개**: 김상영 팀원의 혁신적인 아이디어와 효율적인 개발 능력은 프로젝트의 성공적인 개발에 기여했습니다.  
        """)
#        st.markdown("<hr style='border-top:1px solid #dddddd;'>", unsafe_allow_html=True)  # 구분선

    # 팀원 4 소개
    with st.container():
#        st.image("team_member4.jpg", width=150)  # 팀원 4의 이미지 경로
        st.markdown("### 배근일 대리(인프라팀)")
        st.markdown("""
            **역할**: 백엔드 개발자👨‍💻  
            **소개**: 배근일 팀원의 서버 및 데이터베이스 관리 능력은 프로젝트의 백엔드 구성에 큰 도움이 되었습니다.        
        """)
        st.markdown("<hr style='border-top:1px solid #dddddd;'>", unsafe_allow_html=True)  # 구분선

if st.sidebar.button("만족도 평가", key="button_menu04",use_container_width=True):
    if st.session_state['menu01'] == True:
        st.session_state['menu01']=False
    else:
        st.session_state['menu01']=True
        




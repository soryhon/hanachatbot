import streamlit as st
import pandas as pd
import os
import csv
from datetime import datetime
import socket
import backend as bd

# 사용자 IP 주소 및 컴퓨터명 가져오기
def get_user_ip_and_hostname():
    hostname = socket.gethostname()  # 컴퓨터명 추출
    ip_address = socket.gethostbyname(hostname)  # IP 주소 추출
    return ip_address, hostname

# CSV 파일이 있는지 확인하고 없으면 생성
def check_or_create_csv():
    try:
        file_contents = repo.get_contents(FILE_PATH, ref=BRANCH)
    except:
        # 파일이 없을 경우 헤더를 추가해 생성
        header = ['ID', 'Score', 'IP', 'Hostname', 'DATE']  # Hostname 추가
        with open(FILE_PATH, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(header)
        repo.create_file(FILE_PATH, "Create appraisal.csv", ",".join(header), branch=BRANCH)

# 평가 결과를 CSV에 추가
def add_to_csv(nickname, score):
    try:
        file_contents = repo.get_contents(FILE_PATH, ref=BRANCH)
        csv_data = file_contents.decoded_content.decode('utf-8').splitlines()
        df = pd.read_csv(pd.compat.StringIO("\n".join(csv_data)))
    except:
        df = pd.DataFrame(columns=['ID', 'Score', 'IP', 'Hostname', 'DATE'])

    ip_address, hostname = get_user_ip_and_hostname()  # IP와 컴퓨터명 가져오기

    new_data = {
        'ID': nickname,
        'Score': score,
        'IP': ip_address,
        'Hostname': hostname,  # 컴퓨터명 저장
        'DATE': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    df = df.append(new_data, ignore_index=True)
    
    # CSV로 저장
    csv_data = df.to_csv(index=False)
    repo.update_file(FILE_PATH, "Update appraisal.csv", csv_data, file_contents.sha, branch=BRANCH)


# Frontend 기능 구현 시작 ---

# GitHub 정보가 있는지 확인하고 파일 업로드 객체를 출력
github_info_loaded = bd.load_env_info()



# Streamlit UI
st.title("사용자 만족도 평가")


# 닉네임/이름 입력
nickname = st.text_input("닉네임/이름을 입력하세요:")



col1,col2,col3,col4,col5 = st.columns([0.2,0.2,0.2,0.2,0.2])
with col1:
    st.image("image/star01.png", width=100)
with col2:
    st.image("image/star01.png", width=100)
with col3:
    st.image("image/star01.png", width=100)
with col4:
    st.image("image/star01.png", width=100)
with col5:
    st.image("image/star01.png", width=100)
# 별점 선택 (슬라이더 사용)
score = st.slider("별점 선택 (1~5, 0.5 단위):", 1.0, 5.0, 0.5)

# 평가 버튼
if st.button("평가"):
    if nickname and score:
        check_or_create_csv()
        add_to_csv(nickname, score)
        st.success(f"{nickname}님의 평가가 성공적으로 등록되었습니다!")
    else:
        st.error("닉네임/이름과 별 개수 선택은 필수입니다.")

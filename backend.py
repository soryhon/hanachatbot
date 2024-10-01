import requests
import base64
import streamlit as st
import os  # 서버 경로 생성에 필요
import urllib.parse  # URL 인코딩을 위한 라이브러리
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.agents import create_pandas_dataframe_agent
import pandas as pd
from pptx import Presentation
import docx2txt
from PyPDF2 import PdfReader
from io import BytesIO
from PIL import Image

# GitHub에서 파일 목록을 가져오는 함수
def get_github_files(repo, github_token, folder_name=None, branch="main"):
    """
    GitHub 저장소에서 파일 목록을 가져오는 함수.

    Parameters:
        repo (str): GitHub 저장소 경로 (username/repo 형식).
        github_token (str): GitHub API 토큰.
        folder_name (str, optional): 특정 폴더 이름 (없을 경우 저장소 전체에서 검색).
        branch (str, optional): 브랜치 이름 (기본값은 'main').

    Returns:
        list: 파일 경로 목록.
    """
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    headers = {
        "Authorization": f"token {github_token}"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        tree = response.json().get("tree", [])
        if folder_name:
            file_list = [item["path"] for item in tree if folder_name in item["path"] and item["type"] == "blob"]
        else:
            file_list = [item["path"] for item in tree if item["type"] == "blob"]
        return file_list
    else:
        st.error(f"GitHub 파일 목록을 가져오지 못했습니다: {response.status_code}")
        return []

# GitHub에서 파일의 SHA 값을 가져오는 함수
def get_file_sha(repo, file_path, github_token, branch="main"):
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}?ref={branch}"
    headers = {
        "Authorization": f"token {github_token}"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("sha")
    else:
        return None

# GitHub에 파일을 업로드하거나 덮어쓰는 함수
def upload_file_to_github(repo, folder_name, file_name, content, github_token, branch="main", sha=None):
    url = f"https://api.github.com/repos/{repo}/contents/{folder_name}/{file_name}"
    headers = {
        "Authorization": f"token {github_token}",
        "Content-Type": "application/json"
    }
    content_base64 = base64.b64encode(content).decode("utf-8")
    data = {
        "message": f"Upload {file_name}",
        "content": content_base64,
        "branch": branch
    }

    # sha 값이 있으면 덮어쓰기
    if sha:
        data["sha"] = sha

    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code == 201:
        st.success(f"파일이 GitHub 저장소에 성공적으로 업로드되었습니다: {file_name}")
    elif response.status_code == 200:  # 덮어쓰기 성공
        st.success(f"파일이 GitHub 저장소에 성공적으로 덮어쓰기되었습니다: {file_name}")
    else:
        st.error(f"GitHub 업로드 실패: {response.status_code} - {response.text}")

# Langchain을 사용한 LLM 요청 함수
def send_to_llm(prompt, file_path, openai_api_key):
    try:
        # 파일이 CSV 또는 Excel인 경우 Pandas로 읽고, Langchain Agent로 처리
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
            st.write("읽은 CSV 파일 데이터 미리보기:", df.head())

        elif file_path.endswith(".xlsx"):
            df = pd.read_excel(file_path)
            st.write("읽은 Excel 파일 데이터 미리보기:", df.head())

        elif file_path.endswith(".pptx"):
            ppt = Presentation(file_path)
            text = ""
            for slide in ppt.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
            st.write("PowerPoint 파일 텍스트 미리보기:", text)
            return text

        elif file_path.endswith(".docx"):
            text = docx2txt.process(file_path)
            st.write("Word 파일 텍스트 미리보기:", text)
            return text

        elif file_path.endswith(".pdf"):
            pdf_reader = PdfReader(file_path)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            st.write("PDF 파일 텍스트 미리보기:", text)
            return text

        elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            image = Image.open(file_path)
            st.image(image, caption="이미지 미리보기", use_column_width=True)
            return "이미지 파일이 로드되었습니다."

        else:
            st.error("지원되지 않는 파일 형식입니다.")
            return None

        # OpenAI API 설정
        llm = OpenAI(openai_api_key=openai_api_key)

        # Langchain Pandas Dataframe Agent 생성
        agent = create_pandas_dataframe_agent(llm, df, verbose=True)

        # 프롬프트를 Agent에게 전달하여 처리
        result = agent.run(prompt)

        return result

    except Exception as e:
        st.error(f"파일 내용을 추출하는 중 오류가 발생했습니다: {e}")
        return None

# 서버에서 GitHub 파일 경로를 생성하는 함수
def get_file_server_path(repo, branch, file_path):
    """
    GitHub 저장소의 파일 경로를 서버 경로로 변환하는 함수.

    Parameters:
        repo (str): GitHub 저장소 경로.
        branch (str): GitHub 브랜치.
        file_path (str): GitHub 파일 경로.

    Returns:
        str: 서버에서 사용할 파일 경로.
    """
    base_server_path = "/mnt/data/github_files"
    full_path = os.path.join(base_server_path, repo, branch, file_path)
    return full_path

# 파일 미리보기 함수 (이미지 파일에 대한 추가 처리)
def preview_file(file_path):
    """
    주어진 파일 경로에 따라 미리보기를 생성하는 함수.

    Parameters:
        file_path (str): 미리보기할 파일의 경로.

    Returns:
        str: HTML 콘텐츠로 미리보기를 표시.
    """
    try:
        file_extension = file_path.split('.')[-1].lower()
        encoded_file_path = urllib.parse.quote(file_path)

        if file_extension in ['png', 'jpg', 'jpeg', 'gif']:
            return f'<img src="{encoded_file_path}" alt="이미지 미리보기" style="max-width: 100%;">'
        elif file_extension == 'pdf':
            return f'<iframe src="{encoded_file_path}" width="100%" height="600px"></iframe>'
        elif file_extension == 'html':
            return f'<a href="{encoded_file_path}" target="_blank">HTML 파일 열기</a>'
        else:
            return '<p>미리보기가 지원되지 않는 파일 형식입니다.</p>'
    except Exception as e:
        st.error(f"파일 미리보기 오류: {e}")
        return '<p>미리보기 중 오류가 발생했습니다.</p>'

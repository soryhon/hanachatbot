import requests
import base64
import streamlit as st
import os  # 서버 경로 생성에 필요
import urllib.parse  # URL 인코딩을 위한 라이브러리
from langchain.llms import OpenAI
import pandas as pd
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation
from PIL import Image

# GitHub에서 파일 목록을 가져오는 함수
def get_github_files(repo, github_token, folder_name=None, branch="main"):
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
    url = f"https://api.github.com/repos/{repo}/contents/{urllib.parse.quote(file_path)}?ref={branch}"
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
    url = f"https://api.github.com/repos/{repo}/contents/{urllib.parse.quote(folder_name)}/{urllib.parse.quote(file_name)}"
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

    if sha:
        data["sha"] = sha

    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code == 201:
        st.success(f"파일이 GitHub 저장소에 성공적으로 업로드되었습니다: {file_name}")
    elif response.status_code == 200:
        st.success(f"파일이 GitHub 저장소에 성공적으로 덮어쓰기되었습니다: {file_name}")
    else:
        st.error(f"GitHub 업로드 실패: {response.status_code} - {response.text}")

# 다양한 파일 형식을 처리하는 함수
def extract_file_content(file_path):
    """
    주어진 파일 경로에서 파일 내용을 추출합니다. 다양한 형식 (CSV, Excel, PDF, 이미지, Word, PPT) 지원.
    """
    try:
        # URL 인코딩된 파일 경로 처리
        file_path = urllib.parse.unquote(file_path)
        file_extension = file_path.split('.')[-1].lower()

        # CSV 파일 처리
        if file_extension == "csv":
            df = pd.read_csv(file_path)
            return df.to_string()

        # Excel 파일 처리
        elif file_extension in ["xls", "xlsx"]:
            df = pd.read_excel(file_path)
            return df.to_string()

        # Word 파일 처리
        elif file_extension == "docx":
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])

        # PowerPoint 파일 처리
        elif file_extension == "pptx":
            prs = Presentation(file_path)
            return "\n".join([slide.shapes.title.text for slide in prs.slides if slide.shapes.title])

        # PDF 파일 처리
        elif file_extension == "pdf":
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text

        # 이미지 파일 처리
        elif file_extension in ["png", "jpg", "jpeg", "gif"]:
            img = Image.open(file_path)
            return f"이미지 파일 처리됨 (크기: {img.width}x{img.height})"

        else:
            raise ValueError("지원되지 않는 파일 형식입니다.")

    except Exception as e:
        st.error(f"파일 내용을 추출하는 중 오류가 발생했습니다: {e}")
        return None

# Langchain을 사용한 LLM 요청 함수
def send_to_llm(prompt, file_path, openai_api_key):
    try:
        # 파일 내용을 추출
        file_content = extract_file_content(file_path)
        
        if file_content is None:
            st.error("파일 내용을 추출하지 못했습니다.")
            return None

        # OpenAI API 설정
        llm = OpenAI(openai_api_key=openai_api_key)

        # 프롬프트에 파일 내용을 추가하여 LLM에 전달
        full_prompt = prompt + "\n파일 내용:\n" + file_content

        # Langchain을 사용하여 처리
        result = llm.run(full_prompt)
        
        return result

    except Exception as e:
        st.error(f"LLM 요청 중 오류가 발생했습니다: {e}")
        return None

# 서버에서 GitHub 파일 경로를 생성하는 함수
def get_file_server_path(repo, branch, file_path):
    base_server_path = "/mnt/data/github_files"
    encoded_file_path = urllib.parse.quote(file_path)
    full_path = os.path.join(base_server_path, repo, branch, encoded_file_path)
    return full_path

# 파일 미리보기 함수 (이미지 파일에 대한 추가 처리)
def preview_file(file_path):
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

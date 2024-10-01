import os  # 서버 경로 생성에 필요
import requests
import base64
import streamlit as st
from urllib.parse import quote  # URL 인코딩을 위해 사용
import pandas as pd
from pptx import Presentation
import docx2txt
from PyPDF2 import PdfReader
from io import BytesIO
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

    if sha:
        data["sha"] = sha

    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code == 201:
        st.success(f"파일이 GitHub 저장소에 성공적으로 업로드되었습니다: {file_name}")
    elif response.status_code == 200:
        st.success(f"파일이 GitHub 저장소에 성공적으로 덮어쓰기되었습니다: {file_name}")
    else:
        st.error(f"GitHub 업로드 실패: {response.status_code} - {response.text}")

# 파일 경로를 서버에서 사용하는 경로로 변환하는 함수
def get_file_server_path(repo, branch, file_path):
    base_server_path = "/mnt/data/github_files"
    full_path = os.path.join(base_server_path, repo, branch, file_path)
    
    # 공백과 한글이 포함된 경로에 대해서는 처리하지 않음 (인코딩 하지 않음)
    return full_path

# 파일 내용을 추출하는 함수
def extract_file_content(file_path):
    try:
        # 파일 확장자를 확인하여 파일 내용 추출
        file_extension = file_path.split('.')[-1].lower()

        # 확장자에 따른 파일 읽기 로직
        if file_extension in ['csv']:
            return pd.read_csv(file_path).to_string()
        elif file_extension in ['xlsx', 'xls']:
            return pd.read_excel(file_path).to_string()
        elif file_extension in ['pptx']:
            prs = Presentation(file_path)
            text = ''
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
            return text
        elif file_extension in ['docx']:
            return docx2txt.process(file_path)
        elif file_extension in ['pdf']:
            reader = PdfReader(file_path)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            return text
        elif file_extension in ['png', 'jpg', 'jpeg']:
            image = Image.open(file_path)
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            return buffered.getvalue()
        else:
            return None

    except Exception as e:
        st.error(f"파일 내용을 추출하는 중 오류가 발생했습니다: {e}")
        return None

# 파일 미리보기 함수 (이미지 파일에 대한 추가 처리)
def preview_file(file_path):
    """
    주어진 파일 경로에 따라 미리보기를 생성합니다.
    
    Parameters:
        file_path (str): 미리보기할 파일의 경로
        
    Returns:
        str: HTML 콘텐츠로 미리보기를 표시
    """
    try:
        file_extension = file_path.split('.')[-1].lower()
        encoded_file_path = quote(file_path, safe="/:")

        if file_extension in ['png', 'jpg', 'jpeg', 'gif']:
            # 이미지 미리보기
            return f'<img src="{encoded_file_path}" alt="이미지 미리보기" style="max-width: 100%;">'
        elif file_extension == 'pdf':
            # PDF 미리보기
            return f'<iframe src="{encoded_file_path}" width="100%" height="600px"></iframe>'
        elif file_extension == 'html':
            # HTML 파일 미리보기 링크
            return f'<a href="{encoded_file_path}" target="_blank">HTML 파일 열기</a>'
        else:
            # 미리보기가 지원되지 않는 파일 형식
            return '<p>미리보기가 지원되지 않는 파일 형식입니다.</p>'
    except Exception as e:
        st.error(f"파일 미리보기 오류: {e}")
        return '<p>미리보기 중 오류가 발생했습니다.</p>'

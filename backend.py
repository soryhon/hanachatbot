import requests
import base64
import streamlit as st
import os
import urllib.parse
import pandas as pd
from io import BytesIO
from langchain.llms import OpenAI
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation
from PIL import Image

# GitHub에서 파일 목록을 가져오는 함수
def get_github_files(repo, github_token, folder_name=None, branch="main"):
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    headers = {"Authorization": f"token {github_token}"}
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
    headers = {"Authorization": f"token {github_token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("sha")
    else:
        return None

# GitHub에 파일을 업로드하거나 덮어쓰는 함수
def upload_file_to_github(repo, folder_name, file_name, content, github_token, branch="main", sha=None):
    url = f"https://api.github.com/repos/{repo}/contents/{folder_name}/{file_name}"
    headers = {"Authorization": f"token {github_token}", "Content-Type": "application/json"}
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

# 파일 형식에 맞는 내용을 추출하는 함수
def extract_file_content(file_path):
    try:
        file_extension = file_path.split('.')[-1].lower()

        # CSV 파일 처리
        if file_extension == "csv":
            df = pd.read_csv(file_path)
            return df.to_string()

        # Excel 파일 처리
        elif file_extension in ["xls", "xlsx"]:
            df = pd.read_excel(file_path)
            return df.to_string()

        # PDF 파일 처리
        elif file_extension == "pdf":
            with open(file_path, "rb") as file:
                reader = PdfReader(file)
                text = ''
                for page in reader.pages:
                    text += page.extract_text()
            return text

        # Word 파일 처리
        elif file_extension == "docx":
            doc = Document(file_path)
            text = '\n'.join([para.text for para in doc.paragraphs])
            return text

        # PPT 파일 처리
        elif file_extension == "pptx":
            prs = Presentation(file_path)
            text = ''
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
            return text

        # 이미지 파일 처리
        elif file_extension in ["png", "jpg", "jpeg", "gif"]:
            img = Image.open(file_path)
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            return "[이미지 파일]"

        else:
            return None

    except Exception as e:
        st.error(f"파일 내용을 추출하는 중 오류가 발생했습니다: {e}")
        return None

# OpenAI API를 사용하여 LLM 요청 함수
def send_to_llm(prompt, file_path, openai_api_key):
    try:
        # 파일 내용 추출
        file_content = extract_file_content(file_path)

        if file_content is None:
            st.error("지원되지 않는 파일 형식입니다.")
            return None

        # OpenAI API 설정
        llm = OpenAI(openai_api_key=openai_api_key)

        # 프롬프트를 OpenAI LLM에게 전달하여 처리
        messages = [
            {"role": "system", "content": "파일을 분석하고 보고서를 생성하세요."},
            {"role": "user", "content": f"프롬프트: {prompt}, 파일 내용: {file_content}"}
        ]

        result = llm.generate(messages)
        return result['choices'][0]['message']['content']

    except Exception as e:
        st.error(f"LLM 요청 중 오류가 발생했습니다: {e}")
        return None

# 서버에서 GitHub 파일 경로를 생성하는 함수
def get_file_server_path(repo, branch, file_path):
    base_server_path = "/mnt/data/github_files"
    full_path = os.path.join(base_server_path, repo, branch, file_path)
    return full_path

# 파일 미리보기 함수
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

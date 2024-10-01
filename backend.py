import requests
import base64
import streamlit as st
import urllib.parse  # URL 인코딩을 위한 라이브러리
from langchain.llms import OpenAI
import pandas as pd
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation
from PIL import Image
import os  # 파일 경로 처리를 위한 라이브러리

# GitHub에서 파일을 가져오는 함수 (API를 통해 직접 다운로드)
def download_github_file(repo, file_path, github_token, branch="main"):
    """
    GitHub API를 사용하여 주어진 파일 경로에서 파일을 다운로드하고 내용을 반환합니다.
    
    Parameters:
        repo (str): GitHub 저장소 이름 (예: 'username/repo')
        file_path (str): 저장소 내 파일 경로
        github_token (str): GitHub API 토큰
        branch (str): 브랜치 이름 (기본값: 'main')
    
    Returns:
        파일 내용 (bytes) 또는 None
    """
    try:
        # GitHub API 경로
        url = f"https://api.github.com/repos/{repo}/contents/{urllib.parse.quote(file_path)}?ref={branch}"
        headers = {"Authorization": f"token {github_token}"}
        
        # 요청 보내기
        response = requests.get(url, headers=headers)
        
        # 요청 성공 시 파일 데이터 디코딩
        if response.status_code == 200:
            file_data = response.json()
            file_content = base64.b64decode(file_data['content'])  # Base64 디코딩
            return file_content
        else:
            st.error(f"GitHub 파일을 다운로드하는 중 오류가 발생했습니다: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"파일 다운로드 중 오류가 발생했습니다: {e}")
        return None

# 다양한 파일 형식을 처리하는 함수
def extract_file_content(file_path, file_content):
    """
    주어진 파일 내용에서 데이터를 추출합니다. 다양한 형식 (CSV, Excel, PDF, 이미지, Word, PPT) 지원.
    
    Parameters:
        file_path (str): 파일 경로 (확장자 추출에 사용)
        file_content (bytes): 파일 내용
    
    Returns:
        str: 파일의 텍스트 또는 이미지 처리 결과
    """
    try:
        file_extension = file_path.split('.')[-1].lower()

        # CSV 파일 처리
        if file_extension == "csv":
            df = pd.read_csv(BytesIO(file_content))
            return df.to_string()

        # Excel 파일 처리
        elif file_extension in ["xls", "xlsx"]:
            df = pd.read_excel(BytesIO(file_content))
            return df.to_string()

        # Word 파일 처리
        elif file_extension == "docx":
            doc = Document(BytesIO(file_content))
            return "\n".join([para.text for para in doc.paragraphs])

        # PowerPoint 파일 처리
        elif file_extension == "pptx":
            prs = Presentation(BytesIO(file_content))
            return "\n".join([slide.shapes.title.text for slide in prs.slides if slide.shapes.title])

        # PDF 파일 처리
        elif file_extension == "pdf":
            reader = PdfReader(BytesIO(file_content))
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text

        # 이미지 파일 처리
        elif file_extension in ["png", "jpg", "jpeg", "gif"]:
            img = Image.open(BytesIO(file_content))
            return f"이미지 파일 처리됨 (크기: {img.width}x{img.height})"

        else:
            raise ValueError("지원되지 않는 파일 형식입니다.")

    except Exception as e:
        st.error(f"파일 내용을 추출하는 중 오류가 발생했습니다: {e}")
        return None


# Langchain을 사용한 LLM 요청 함수
def send_to_llm(prompt, file_path, github_token, openai_api_key, repo, branch="main"):
    try:
        # GitHub에서 파일 다운로드
        file_content = download_github_file(repo, file_path, github_token, branch)
        
        if file_content is None:
            st.error("파일 내용을 다운로드하지 못했습니다.")
            return None

        # 파일 내용을 추출
        extracted_content = extract_file_content(file_path, file_content)

        if extracted_content is None:
            st.error("파일 내용을 추출하지 못했습니다.")
            return None

        # OpenAI API 설정
        llm = OpenAI(openai_api_key=openai_api_key)

        # 프롬프트에 파일 내용을 추가하여 LLM에 전달
        full_prompt = prompt + "\n파일 내용:\n" + extracted_content

        # Langchain을 사용하여 처리
        result = llm.run(full_prompt)
        
        return result

    except Exception as e:
        st.error(f"LLM 요청 중 오류가 발생했습니다: {e}")
        return None


# 서버에서 GitHub 파일 경로를 생성하는 함수
def get_file_server_path(repo, branch, file_path):
    """
    주어진 GitHub 저장소 경로와 브랜치, 파일 경로를 사용하여 서버의 파일 경로를 반환합니다.
    
    Parameters:
        repo (str): GitHub 저장소 경로 (username/repo 형식)
        branch (str): GitHub 브랜치 이름
        file_path (str): 저장소 내의 파일 경로
    
    Returns:
        str: 서버에서 파일이 저장될 경로
    """
    base_server_path = "/mnt/data/github_files"
    
    # 파일 경로 인코딩하여 안전한 파일 경로 생성
    encoded_file_path = urllib.parse.quote(file_path)
    
    # 서버에서 파일 경로를 생성
    full_path = os.path.join(base_server_path, repo, branch, encoded_file_path)
    
    return full_path


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
        # 파일 확장자를 확인하여 미리보기 처리
        file_extension = file_path.split('.')[-1].lower()

        # URL 인코딩 적용 (한글 파일 경로 문제 해결)
        encoded_file_path = urllib.parse.quote(file_path)

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

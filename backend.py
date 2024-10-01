import requests
import base64
import streamlit as st
import os  # 서버 경로 생성에 필요
import urllib.parse  # URL 인코딩을 위한 라이브러리
from PIL import Image
from io import BytesIO

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

# OpenAI API를 사용하여 LLM에 요청을 보내는 함수
def send_to_llm(prompt, openai_api_key):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4",
        "messages": prompt
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        st.error(f"OpenAI API 요청 실패: {response.status_code} - {response.text}")
        return None

# 서버에서 GitHub 파일 경로를 생성하는 함수 (새로 추가된 부분)
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
    # 기본적으로 서버에서 파일을 저장하는 경로를 설정 (예시로 /mnt/data 경로 사용)
    base_server_path = "/mnt/data/github_files"
    
    # 서버에서 파일 경로를 생성
    full_path = os.path.join(base_server_path, repo, branch, file_path)
    
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

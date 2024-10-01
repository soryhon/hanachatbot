import os
import pandas as pd
import requests
import base64
import streamlit as st
import urllib.parse
from io import BytesIO
from docx import Document
from pptx import Presentation
from PyPDF2 import PdfReader
from PIL import Image
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain

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

# 파일 경로를 인코딩하는 함수 (한글과 공백 처리)
def encode_file_path(file_path):
    return urllib.parse.quote(file_path)

# Langchain을 사용한 LLM 요청 함수
def send_to_llm(prompt, file_path, openai_api_key):
    try:
        llm = OpenAI(api_key=openai_api_key)
        file_extension = file_path.split('.')[-1].lower()

        # 엑셀 파일 처리
        if file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(file_path)
            st.write("읽은 엑셀 데이터 미리보기:", df.head())

            template = PromptTemplate(
                input_variables=["data", "user_prompt"],
                template="다음 데이터를 기반으로 보고서를 작성하세요: {data}. 요청사항: {user_prompt}"
            )
            chain = LLMChain(llm=llm, prompt=template)
            result = chain.run(data=df.to_string(), user_prompt=prompt[1]['content'])
            return result

        # CSV 파일 처리
        elif file_extension == 'csv':
            df = pd.read_csv(file_path)
            st.write("읽은 CSV 데이터 미리보기:", df.head())

            template = PromptTemplate(
                input_variables=["data", "user_prompt"],
                template="다음 데이터를 기반으로 보고서를 작성하세요: {data}. 요청사항: {user_prompt}"
            )
            chain = LLMChain(llm=llm, prompt=template)
            result = chain.run(data=df.to_string(), user_prompt=prompt[1]['content'])
            return result

        # Word 파일 처리
        elif file_extension == 'docx':
            doc = Document(file_path)
            doc_text = '\n'.join([para.text for para in doc.paragraphs])
            st.write("읽은 Word 문서 데이터 미리보기:", doc_text[:500])

            template = PromptTemplate(
                input_variables=["data", "user_prompt"],
                template="다음 문서를 기반으로 보고서를 작성하세요: {data}. 요청사항: {user_prompt}"
            )
            chain = LLMChain(llm=llm, prompt=template)
            result = chain.run(data=doc_text, user_prompt=prompt[1]['content'])
            return result

        # PPT 파일 처리
        elif file_extension == 'pptx':
            ppt = Presentation(file_path)
            ppt_text = ''
            for slide in ppt.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        ppt_text += shape.text + "\n"
            st.write("읽은 PPT 데이터 미리보기:", ppt_text[:500])

            template = PromptTemplate(
                input_variables=["data", "user_prompt"],
                template="다음 프레젠테이션을 기반으로 보고서를 작성하세요: {data}. 요청사항: {user_prompt}"
            )
            chain = LLMChain(llm=llm, prompt=template)
            result = chain.run(data=ppt_text, user_prompt=prompt[1]['content'])
            return result

        # PDF 파일 처리
        elif file_extension == 'pdf':
            pdf_text = ""
            with open(file_path, "rb") as f:
                pdf = PdfReader(f)
                for page in pdf.pages:
                    pdf_text += page.extract_text()
            st.write("읽은 PDF 데이터 미리보기:", pdf_text[:500])

            template = PromptTemplate(
                input_variables=["data", "user_prompt"],
                template="다음 PDF 문서를 기반으로 보고서를 작성하세요: {data}. 요청사항: {user_prompt}"
            )
            chain = LLMChain(llm=llm, prompt=template)
            result = chain.run(data=pdf_text, user_prompt=prompt[1]['content'])
            return result

        # 이미지 파일 처리
        elif file_extension in ['png', 'jpg', 'jpeg', 'gif']:
            image = Image.open(file_path)
            st.image(image, caption="이미지 미리보기", use_column_width=True)
            return "이미지 파일은 텍스트 분석이 지원되지 않습니다."

        else:
            st.error("지원되지 않는 파일 형식입니다.")
            return None

    except Exception as e:
        st.error(f"파일 내용을 추출하는 중 오류가 발생했습니다: {e}")
        return None

# 서버에서 GitHub 파일 경로를 생성하는 함수
def get_file_server_path(repo, branch, file_path):
    base_server_path = "/mnt/data/github_files"
    full_path = os.path.join(base_server_path, repo, branch, file_path)
    return full_path

# 파일 미리보기 함수 (URL 기반으로 변경)
def preview_file(file_url):
    try:
        file_extension = file_url.split('.')[-1].lower()

        if file_extension in ['png', 'jpg', 'jpeg', 'gif']:
            return f'<img src="{file_url}" alt="이미지 미리보기" style="max-width: 100%;">'
        elif file_extension == 'pdf':
            return f'<iframe src="{file_url}" width="100%" height="600px"></iframe>'
        elif file_extension == 'html':
            return f'<a href="{file_url}" target="_blank">HTML 파일 열기</a>'
        else:
            return '<p>미리보기가 지원되지 않는 파일 형식입니다.</p>'
    except Exception as e:
        st.error(f"파일 미리보기 오류: {e}")
        return '<p>미리보기 중 오류가 발생했습니다.</p>'

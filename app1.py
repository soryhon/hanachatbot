import streamlit as st
import pandas as pd
import backend

# 페이지 설정
st.set_page_config(layout="wide")

# HTML + CSS + JavaScript를 활용하여 화면을 구성하는 코드
html_code = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
        }
        .container {
            width: 80%;
            margin: auto;
        }
        .section {
            margin-bottom: 20px;
        }
        h2 {
            color: #333;
        }
        .button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }
        .button:hover {
            background-color: #45a049;
        }
        input[type=text], input[type=password] {
            width: 100%;
            padding: 12px 20px;
            margin: 8px 0;
            display: inline-block;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-sizing: border-box;
        }
        .file-input {
            margin: 20px 0;
        }
        .result {
            border: 1px solid #ccc;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            background-color: #f9f9f9;
        }
        .file-list {
            margin: 20px 0;
            padding: 10px;
            border: 1px solid #ddd;
            background-color: #f4f4f4;
            border-radius: 5px;
        }
    </style>
    <script>
        function showAlert() {
            alert("버튼이 클릭되었습니다!");
        }

        function toggleVisibility(id) {
            var elem = document.getElementById(id);
            if (elem.style.display === "none") {
                elem.style.display = "block";
            } else {
                elem.style.display = "none";
            }
        }
    </script>
</head>
<body>

<div class="container">

    <!-- GitHub 및 OpenAI 정보 입력 -->
    <div class="section">
        <h2>GitHub 저장소 정보 및 OpenAI API 키 입력</h2>
        <label for="github_repo">GitHub 저장소 경로 (예: username/repo):</label>
        <input type="text" id="github_repo" placeholder="GitHub 저장소 경로 입력">
        
        <label for="github_token">GitHub API 토큰 입력:</label>
        <input type="password" id="github_token" placeholder="GitHub API 토큰 입력">
        
        <label for="openai_api_key">OpenAI API 키 입력:</label>
        <input type="password" id="openai_api_key" placeholder="OpenAI API 키 입력">
        
        <button class="button" onclick="showAlert()">저장</button>
    </div>

    <!-- 작성 보고서 요청사항 -->
    <div class="section">
        <h2>1. 작성 보고서 요청사항</h2>
        <div class="file-list" id="fileList">
            <p>요청사항 파일 목록을 여기에 표시합니다.</p>
            <!-- JavaScript로 동적 파일 목록 처리 가능 -->
        </div>
        <button class="button" onclick="showAlert()">파일 선택</button>
    </div>

    <!-- 파일 업로드 -->
    <div class="section">
        <h2>2. 파일 업로드</h2>
        <input type="file" id="fileInput" class="file-input">
        <button class="button" onclick="showAlert()">파일 업로드</button>
    </div>

    <!-- 참고 탬플릿 미리보기 -->
    <div class="section">
        <h2>3. 참고 탬플릿 미리보기</h2>
        <div class="file-list" id="templateFileList">
            <p>탬플릿 파일 목록을 여기에 표시합니다.</p>
            <!-- JavaScript로 동적 템플릿 파일 목록 처리 가능 -->
        </div>
        <button class="button" onclick="toggleVisibility('templatePreview')">파일 선택</button>
        <div id="templatePreview" class="result" style="display:none;">
            <p>선택한 파일의 미리보기 내용입니다.</p>
        </div>
    </div>

    <!-- 실행 -->
    <div class="section">
        <h2>4. 실행</h2>
        <button class="button" onclick="showAlert()">실행</button>
    </div>

    <!-- 결과 보고서 -->
    <div class="section">
        <h2>5. 결과 보고서</h2>
        <div id="result" class="result">
            <p>결과 보고서 내용이 여기에 표시됩니다.</p>
        </div>
    </div>

    <!-- 저장 및 불러오기 -->
    <div class="section">
        <h2>6. 저장 및 불러오기</h2>
        <label for="savePath">저장할 파일명 입력:</label>
        <input type="text" id="savePath" placeholder="저장할 파일명 입력">
        <button class="button" onclick="showAlert()">저장</button>

        <label for="loadFile">저장된 파일 불러오기:</label>
        <input type="file" id="loadFile" class="file-input">
        <button class="button" onclick="showAlert()">불러오기</button>
    </div>

</div>

</body>
</html>
'''

# Streamlit에서 HTML 화면 구성 표시
st.components.v1.html(html_code, height=800)

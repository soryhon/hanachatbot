import streamlit as st
import backend  # backend.py 파일의 함수를 가져옴

# 페이지 설정
st.set_page_config(layout="wide")

# HTML과 JavaScript를 이용한 화면 구성
html_code = """
<div style="width:100%; text-align:center;">
    <h2>Streamlit 기반 GitHub 및 OpenAI 인터페이스</h2>
    
    <div style="margin-bottom: 20px;">
        <h3>GitHub 정보 입력</h3>
        <input type="text" id="github_repo" placeholder="GitHub 저장소 경로 (예: username/repo)" style="width: 80%; padding: 10px; margin-bottom: 10px;"><br>
        <input type="password" id="github_token" placeholder="GitHub API 토큰 입력" style="width: 80%; padding: 10px; margin-bottom: 10px;"><br>
        <input type="text" id="github_branch" placeholder="브랜치 이름 (예: main)" value="main" style="width: 80%; padding: 10px; margin-bottom: 20px;"><br>
        <button onclick="getGithubFiles()" style="padding: 10px 20px;">GitHub 파일 목록 가져오기</button>
    </div>
    
    <div id="fileList"></div>

    <div style="margin-top: 30px;">
        <h3>OpenAI API 키 입력 및 요청</h3>
        <input type="password" id="openai_api_key" placeholder="OpenAI API 키 입력" style="width: 80%; padding: 10px; margin-bottom: 10px;"><br>
        <textarea id="openai_prompt" placeholder="OpenAI에 보낼 메시지를 입력하세요." style="width: 80%; height: 100px; padding: 10px;"></textarea><br>
        <button onclick="sendToOpenAI()" style="padding: 10px 20px;">OpenAI로 전송</button>
    </div>

    <div id="openaiResponse"></div>
</div>

<script>
    // GitHub 파일 목록 가져오기
    function getGithubFiles() {
        const githubRepo = document.getElementById("github_repo").value;
        const githubToken = document.getElementById("github_token").value;
        const githubBranch = document.getElementById("github_branch").value;

        if (!githubRepo || !githubToken || !githubBranch) {
            alert("모든 GitHub 정보를 입력해주세요.");
            return;
        }

        // Python 함수를 호출하여 GitHub 파일 목록 가져오기
        streamlitAPI("get_github_files", githubRepo, githubToken, githubBranch).then((fileList) => {
            if (fileList.length > 0) {
                let fileListHTML = "<h4>GitHub 파일 목록</h4><ul>";
                fileList.forEach(file => {
                    fileListHTML += `<li>${file}</li>`;
                });
                fileListHTML += "</ul>";
                document.getElementById("fileList").innerHTML = fileListHTML;
            } else {
                document.getElementById("fileList").innerHTML = "<p>파일 목록을 가져오지 못했습니다.</p>";
            }
        });
    }

    // OpenAI API 요청
    function sendToOpenAI() {
        const apiKey = document.getElementById("openai_api_key").value;
        const prompt = document.getElementById("openai_prompt").value;

        if (!apiKey || !prompt) {
            alert("OpenAI API 키와 메시지를 모두 입력해주세요.");
            return;
        }

        // Python 함수를 호출하여 OpenAI 요청 보내기
        streamlitAPI("send_to_openai", apiKey, prompt).then((response) => {
            document.getElementById("openaiResponse").innerHTML = `<h4>OpenAI 응답</h4><p>${response}</p>`;
        });
    }

    // Python 함수를 호출하는 Streamlit API 호출 함수
    async function streamlitAPI(functionName, ...args) {
        const result = await fetch(`/streamlit/${functionName}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ args })
        });

        const data = await result.json();
        return data.result;
    }
</script>
"""

# HTML 코드 삽입
st.components.v1.html(html_code, height=600)

# GitHub 파일 목록 가져오기 (백엔드 함수 호출)
def get_github_files():
    github_repo = st.session_state['github_repo']
    github_token = st.session_state['github_token']
    github_branch = st.session_state['github_branch']

    if github_repo and github_token and github_branch:
        return backend.get_github_files(github_repo, github_token, branch=github_branch)
    else:
        return []

# OpenAI API 요청 보내기 (백엔드 함수 호출)
def send_to_openai():
    openai_api_key = st.session_state['openai_api_key']
    prompt_text = st.session_state['openai_prompt']

    if openai_api_key and prompt_text:
        prompt = [
            {"role": "system", "content": "You are an AI that helps users based on the prompt."},
            {"role": "user", "content": prompt_text}
        ]
        return backend.send_to_llm(prompt, openai_api_key)
    else:
        return "OpenAI API 키와 메시지를 모두 입력해야 합니다."

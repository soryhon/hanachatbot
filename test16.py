import streamlit as st

# 페이지 구성 설정: 전체 화면 사용
st.set_page_config(layout="wide")

# 버튼 HTML 및 JavaScript 코드
html_code = """
<div style="width:100%; text-align:center;">
    <button onclick="showViewer()">저장 정보 보기</button>
    <button onclick="hideViewer()">저장 정보 숨기기</button>
</div>

<!-- viewer 객체 -->
<div id="viewer" style="display:none; width:80%; height:30%; margin:auto; border:1px solid black; text-align:center;">
    <h3>저장된 정보</h3>
    <p>여기에 저장된 정보가 표시됩니다.</p>
</div>

<script>
    function showViewer() {
        document.getElementById('viewer').style.display = 'block';
    }

    function hideViewer() {
        document.getElementById('viewer').style.display = 'none';
    }
</script>
"""

# HTML 코드 삽입
st.components.v1.html(html_code, height=400)

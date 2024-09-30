import streamlit as st

# 페이지 구성 설정: 전체 화면 사용
st.set_page_config(layout="wide")

# HTML 및 JavaScript 코드
html_code = """
<div style="width:100%; text-align:center;">
    <button onclick="showViewer()">저장 정보 보기</button>
    <button onclick="hideViewer()">저장 정보 숨기기</button>
</div>

<!-- viewer 객체 -->
<div id="viewer" style="display:none; width:80%; height:30%; margin:auto; border:1px solid black; text-align:center;">
    <h3>저장된 정보 테이블</h3>

    <!-- 테이블 구성 -->
    <table style="width:80%; margin:auto; text-align:center;">
        <tr>
            <th>항목</th>
            <th>정보</th>
        </tr>
        <tr>
            <td>이름</td>
            <td><input type="text" id="name_input" placeholder="이름 입력"></td>
        </tr>
        <tr>
            <td>나이</td>
            <td><input type="text" id="age_input" placeholder="나이 입력"></td>
        </tr>
    </table>

    <!-- 선택 버튼 -->
    <button style="margin-top:20px;" onclick="showPopup()">선택</button>
</div>

<!-- 팝업창 -->
<div id="popup" style="display:none; width:300px; height:150px; position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); background-color:white; border:2px solid black; text-align:center; padding:20px;">
    <h4>입력한 정보</h4>
    <p id="name_output"></p>
    <p id="age_output"></p>
    <button onclick="closePopup()">닫기</button>
</div>

<script>
    function showViewer() {
        document.getElementById('viewer').style.display = 'block';
    }

    function hideViewer() {
        document.getElementById('viewer').style.display = 'none';
    }

    function showPopup() {
        // 입력된 값을 가져와서 팝업창에 보여주기
        var name = document.getElementById('name_input').value;
        var age = document.getElementById('age_input').value;

        document.getElementById('name_output').innerText = "이름: " + name;
        document.getElementById('age_output').innerText = "나이: " + age;

        // 팝업창 표시
        document.getElementById('popup').style.display = 'block';
    }

    function closePopup() {
        // 팝업창 닫기
        document.getElementById('popup').style.display = 'none';
    }
</script>
"""

# HTML 코드 삽입
st.components.v1.html(html_code, height=600)

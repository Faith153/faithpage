# pages/6_🎮_Pinball_Game.py
import streamlit as st
import os

st.set_page_config(
    page_title="Pinball Game",
    page_icon="🎮",
    layout="wide"
)

st.title("🎮 Retro Pinball Game")

# HTML 파일 읽기
html_file_path = "pates/6_pinball_game.html"
if os.path.exists(html_file_path):
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # HTML 컴포넌트로 게임 표시
    st.components.v1.html(html_content, height=700, scrolling=False)
else:
    st.error("게임 파일을 찾을 수 없습니다.")

st.markdown("""
### 🎯 게임 조작법
- **스페이스바** 또는 **런처 클릭**: 공 발사
- **A키**: 왼쪽 플리퍼
- **D키**: 오른쪽 플리퍼
- **마우스**: 버튼 클릭으로도 조작 가능

### 🏆 점수 시스템
- 범퍼 충돌: 100점
- 장애물 충돌: 50점
- 높은 점수를 목표로 도전해보세요!
""")

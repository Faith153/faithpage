'''
your_app/
│
├── streamlit_app.py      ← 메인 페이지 스크립트
│
└── pages/                ← 추가 페이지들은 이 폴더에 넣기
    ├── 1_imagen.py        ← 페이지 파일명 앞에 숫자 붙이면 순서 지정 가능
    ├── 2_BibleReading.py
    └── 3_FaithGPT.py
'''

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd


st.title("믿음님의 코딩 연습장")
st.write("1-이미지생성기 : Imagen")
st.write("2-성경읽기표 : Bible Reading Checker 그룹생성, 관리자, 개인로그인 기능")
st.write("  ㄴ예정 : 카카오톡봇을 통한 채팅방에서 명령어로 웹 현황판에 자동 기록?")
st.write("3-FaithGPT-4.1 : 우리아이들 맞춤형 ChatGPT")
st.write("4-DD 워크매니저(결제툴)")
st.write("5-오목 prototype")
st.write("6-핀볼 prototype_html")

# 메인페이지 이미지 첨부(외부링크)
img_url = "https://images.unsplash.com/photo-1615454782617-e69bbd4f2969?q=80&w=1656&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
html_code = f"""
    <div style="display: flex; justify-content: center;">
        <img src="{img_url}" style="width:100%; max-width:1000px; border-radius:18px; box-shadow:2px 2px 16px #bbb;">
    </div>
"""
components.html(html_code, height=700)

#===============================================

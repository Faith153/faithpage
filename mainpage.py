'''
your_app/
│
├── streamlit_app.py      ← 메인 페이지 스크립트
│
└── pages/                ← 추가 페이지들은 이 폴더에 넣기
    ├── 1_imagen.py        ← 페이지 파일명 앞에 숫자 붙이면 순서 지정 가능
    ├── 2_BibleReading.py
    └── 3_Help.py
'''

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd


st.title("Faith의 코딩 연습장")
st.write("1-이미지생성기")
st.write("2-성경읽기표 : 그룹생성, 관리자, 개인별로그인 기능")
st.write("3-예정 : 우리아이들 맞춤형 ChatGPT")

# 메인페이지 이미지 첨부(외부링크)
img_url = "https://images.unsplash.com/photo-1615454782617-e69bbd4f2969?q=80&w=1656&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
html_code = f"""
    <div style="display: flex; justify-content: center;">
        <img src="{img_url}" style="width:100%; max-width:1000px; border-radius:18px; box-shadow:2px 2px 16px #bbb;">
    </div>
"""
components.html(html_code, height=700)

#===============================================

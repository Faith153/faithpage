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


st.title("Main Page")
st.write("Faith의 코딩 연습장")

# 메인페이지 이미지 첨부(외부링크)
img_url = "https://images.unsplash.com/photo-1506744038136-46273834b3fb"
html_code = f"""
    <div style="display: flex; justify-content: center;">
        <img src="{img_url}" style="width:100%; max-width:1000px; border-radius:18px; box-shadow:2px 2px 16px #bbb;">
    </div>
"""
components.html(html_code, height=500)

#===============================================

# 캐시 활용시 불러오는 시간이 반복되지 않음
@st.cache_data
def load_data(url):
    df = pd.read_csv(url, nrows=10000)
    st.write( df.shape )
    st.write( df.columns) 
    return df

df = load_data("https://github.com/plotly/datasets/raw/master/uber-rides-data1.csv")
st.dataframe(df)

st.button("새로고침")  # 버튼 클릭 시 페이지 새로고침

#=================================================

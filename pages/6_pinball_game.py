import streamlit as st

with open("6_pinball_game.html", "r", encoding="utf-8") as f:
    html_code = f.read()

st.components.v1.html(html_code, height=720, width=440, scrolling=False)

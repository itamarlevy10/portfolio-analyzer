import streamlit as st
from PIL import Image

_icon = Image.open("logo.png")
st.set_page_config(page_title="Portfolio Analyzer", page_icon=_icon, layout="wide")

pg = st.navigation([
    st.Page("pages/analyze.py", title="Analyze My Portfolio", icon="📊"),
    st.Page("pages/1_Build_My_Portfolio.py", title="Build My Portfolio", icon="🏗️"),
])
pg.run()

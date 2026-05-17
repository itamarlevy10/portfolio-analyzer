import streamlit as st
from PIL import Image, ImageDraw

def _make_icon():
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=14, fill=(37, 99, 235, 255))
    pts = [(10, 46), (22, 34), (35, 42), (48, 18), (57, 28)]
    d.line(pts, fill="white", width=5)
    for x, y in pts:
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill="white")
    return img

st.set_page_config(page_title="Portfolio Analyzer", page_icon=_make_icon(), layout="wide")

pg = st.navigation([
    st.Page("pages/analyze.py", title="Analyze My Portfolio", icon="📊"),
    st.Page("pages/1_Build_My_Portfolio.py", title="Build My Portfolio", icon="🏗️"),
])
pg.run()

import streamlit as st
import streamlit.components.v1 as components
import base64

st.set_page_config(
    page_title="AI Project",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS from static file
with open("static/style.css", "r") as f:
    css = f"<style>{f.read()}</style>"
    components.html(css, height=0)

# Load JavaScript from static file
with open("static/script.js", "r") as f:
    js_code = f.read()
    components.html(f"<script>{js_code}</script>", height=0)

st.markdown("<h1 class='main-header'>AI Project</h1>")

st.markdown("<h3>التحديثات تتم تلقائيًا...</h3>")

st.markdown(
    """
    <div class="buttons">
        <button onclick="createWebsite()">إنشاء موقع إلكتروني</button>
        <button onclick="smartUpdates()">تحديثات ذكية</button>
        <button onclick="manageAgents()">إدارة الوكلاء</button>
    </div>
    """
)

uploaded_file = st.file_uploader("اختر صورة لتحليلها", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Encode the file to base64
    encoded_string = base64.b64encode(uploaded_file.getvalue()).decode()
    st.markdown(
        f"""
        <img src="data:image/png;base64,{encoded_string}" width="200">
        """
    )
    st.markdown(
        """
        <button onclick="analyzeImage(document.querySelector('input[type=file]'))">تحليل الصورة</button>
        """
    )
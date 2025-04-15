import streamlit as st

st.set_page_config(
    page_title="AI Project",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-header {
        color: #4CAF50;
        text-align: center;
    }
    </style>
import streamlit as st
import base64

st.set_page_config(
    page_title="AI Project",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .main-header {
        color: #4CAF50;
        text-align: center;
    }
    .buttons {
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }
    .buttons button {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 5px;
    }
    @media (max-width: 600px) {
        .buttons button {
            width: 100%;
            margin-bottom: 15px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<h1 class='main-header'>AI Project</h1>", unsafe_allow_html=True)

st.markdown("<h3>التحديثات تتم تلقائيًا...</h3>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="buttons">
        <button onclick="createWebsite()">إنشاء موقع إلكتروني</button>
        <button onclick="smartUpdates()">تحديثات ذكية</button>
        <button onclick="manageAgents()">إدارة الوكلاء</button>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader("اختر صورة لتحليلها", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Encode the file to base64
    encoded_string = base64.b64encode(uploaded_file.getvalue()).decode()
    st.markdown(
        f"""
        <img src="data:image/png;base64,{encoded_string}" width="200">
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <button onclick="analyzeImage(document.querySelector('input[type=file]'))">تحليل الصورة</button>
        """,
        unsafe_allow_html=True
    )

st.markdown(
    """
    <script src="static/script.js"></script>
    """,
    unsafe_allow_html=True
)
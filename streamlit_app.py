import streamlit as st
import requests
import base64
import time

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="InsightDoc AI | Elite",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

#  SESSION STATE INIT 
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_response" not in st.session_state:
    st.session_state.last_response = None


#  CUSTOM CSS 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@300;400;600&display=swap');

.stApp {
    background-color: #0F172A;
    color: #F8FAFC;
    font-family: 'Inter', sans-serif;
}

header, [data-testid="stToolbar"], [data-testid="stStatusWidget"], .stDeployButton {
    display: none !important;
}

[data-testid="stSidebar"] {
    background-color: #1E293B;
    border-right: 1px solid #334155;
}

.title-text {
    font-family: 'Playfair Display', serif;
    font-size: 3.5rem;
    background: linear-gradient(135deg, #E2E8F0, #94A3B8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    color: #64748B;
    margin-bottom: 2rem;
}

.stTabs [aria-selected="true"] {
    color: #F8FAFC;
    border-bottom: 2px solid #D97706;
}
</style>
""", unsafe_allow_html=True)

#  SIDEBAR 
with st.sidebar:
    st.markdown("### 📂 Knowledge Vault")

    uploaded_files = st.file_uploader(
        "Secure Upload",
        type=["pdf", "docx", "txt", "csv", "db", "png", "jpg"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if st.button("📥 Secure Ingest", use_container_width=True):
        if uploaded_files:
            bar = st.progress(0.0)
            for i, file in enumerate(uploaded_files):
                try:
                    files = {"file": (file.name, file, file.type)}
                    r = requests.post(f"{API_URL}/upload", files=files, timeout=60)
                    if r.status_code == 200:
                        st.toast(f"Ingested: {file.name}", icon="✅")
                except:
                    st.toast(f"Failed: {file.name}", icon="❌")
                bar.progress((i + 1) / len(uploaded_files))
            time.sleep(0.3)
            bar.empty()

    st.markdown("---")

    if st.button("🗑️ Delete History", use_container_width=True):
        st.session_state.messages.clear()
        st.session_state.last_response = None
        st.rerun()

#  HEADER 
st.markdown('<div class="title-text">InsightDoc AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Document & Visual Intelligence Suite</div>', unsafe_allow_html=True)

#  CHAT HISTORY 
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.write(msg["content"])
            if msg.get("image_url"):
                st.image(msg["image_url"], width=400)
        else:
            tab1, tab2, tab3 = st.tabs(["Analysis", "Context", "Audit Trail"])

            with tab1:
                st.markdown(msg.get("content", ""))

            with tab2:
                for src in msg.get("sources", []):
                    with st.expander(f"📄 {src.get('filename', 'Document')}"):
                        st.code(src.get("page_content", ""), language="text")

            with tab3:
                for src in msg.get("sources", []):
                    st.caption(f"📁 {src.get('filename', '')}")

#  CHAT INPUT 
prompt = st.chat_input("Enter executive query...")

if prompt:
    # Save user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                res = requests.post(
                    f"{API_URL}/query",
                    json={"question": prompt},
                    timeout=120
                )

                if res.status_code == 200:
                    data = res.json()

                    # SAFELY STORE RESPONSE
                    st.session_state.last_response = {
                        "role": "assistant",
                        "content": data.get("answer", "No answer generated."),
                        "sources": data.get("sources", [])
                    }

                    st.session_state.messages.append(st.session_state.last_response)
                    st.rerun()

                else:
                    st.error(res.text)

            except Exception as e:
                st.error(f"Connection error: {e}")

#  VISUAL INTELLIGENCE
with st.sidebar:
    st.markdown("### 👁️ Visual Intelligence")

    image_file = st.file_uploader("Upload Image", type=["png", "jpg"], key="vision")

    if image_file and st.button("Analyze Visual"):
        b64 = base64.b64encode(image_file.getvalue()).decode()

        st.session_state.messages.append({
            "role": "user",
            "content": "Analyze this visual asset",
            "image_url": image_file
        })

        with st.spinner("Analyzing..."):
            try:
                res = requests.post(
                    f"{API_URL}/query",
                    json={
                        "question": "Provide a detailed executive summary of this image.",
                        "image_base64": b64
                    },
                    timeout=120
                )

                if res.status_code == 200:
                    data = res.json()
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": data.get("answer", ""),
                        "sources": data.get("sources", [])
                    })
                    st.rerun()
            except Exception as e:
                st.error(e)

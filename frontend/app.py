import streamlit as st
import requests
import json
from streamlit_ace import st_ace

st.set_page_config(page_title="VIntervu 2.0", layout="wide")

API_URL = "http://localhost:8000"

# Custom CSS for chat interface
st.markdown("""
<style>
    .chat-message {
        padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex
    }
    .chat-message.user {
        background-color: #2b313e
    }
    .chat-message.bot {
        background-color: #475063
    }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = [] # List of dicts: {"role": "user", "content": "..."}

if "candidate_profile" not in st.session_state:
    st.session_state.candidate_profile = None

if "agent_thoughts" not in st.session_state:
    st.session_state.agent_thoughts = []

if "interview_active" not in st.session_state:
    st.session_state.interview_active = False

if "session_id" not in st.session_state:
    st.session_state.session_id = "session_1"

def send_message(message):
    st.session_state.messages.append({"role": "user", "content": message})
    
    payload = {
        "message": message,
        "session_id": st.session_state.session_id,
        "candidate_profile": st.session_state.candidate_profile,
        "history": st.session_state.messages[:-1] # Send history excluding current new message (backend adds it)
    }
    
    try:
        response = requests.post(f"{API_URL}/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        
        bot_response = data["response"]
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        
        if data.get("candidate_profile"):
            st.session_state.candidate_profile = data["candidate_profile"]
            
        if data.get("code_output"):
            st.session_state.agent_thoughts.append(f"Evaluated code. Output: {data['code_output'][:50]}...")
            
    except Exception as e:
        st.error(f"Error communicating with backend: {e}")

# Sidebar
with st.sidebar:
    st.title("VIntervu 2.0")
    st.caption("Decoupled Architecture")
    st.subheader("Agent Thoughts")
    for thought in st.session_state.agent_thoughts:
        st.info(thought)
        
    st.divider()
    st.subheader("Resume Upload")
    uploaded_file = st.file_uploader("Upload Resume (TXT/PDF)", type=["txt", "pdf"])
    
    if uploaded_file and not st.session_state.candidate_profile:
        if st.button("Analyze Resume"):
            try:
                resume_text = ""
                if uploaded_file.type == "application/pdf":
                    import pypdf
                    pdf_reader = pypdf.PdfReader(uploaded_file)
                    for page in pdf_reader.pages:
                        resume_text += page.extract_text()
                else:
                    resume_text = uploaded_file.read().decode("utf-8")
                
                if not resume_text.strip():
                    st.error("Could not extract text from the file.")
                else:
                    # Call API
                    try:
                        response = requests.post(f"{API_URL}/analyze-resume", json={"resume_text": resume_text})
                        response.raise_for_status()
                        data = response.json()
                        
                        st.session_state.candidate_profile = data["candidate_profile"]
                        st.session_state.messages.append({"role": "assistant", "content": data["response"]})
                        st.session_state.interview_active = True
                        st.session_state.agent_thoughts.append(f"Analyzed resume for {data['candidate_profile'].get('name')}")
                        st.rerun()
                    except Exception as e:
                        error_detail = ""
                        if hasattr(e, 'response') and e.response is not None:
                            error_detail = f": {e.response.text}"
                        st.error(f"API Error{error_detail}")
            except Exception as e:
                st.error(f"Error processing file: {e}")

# Main Chat Area
st.header("Interview Session")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Input area
if st.session_state.interview_active:
    user_input = st.chat_input("Type your answer...")
    
    # Code Editor Toggle
    show_editor = st.checkbox("Open Code Editor")
    code_input = ""
    
    if show_editor:
        try:
            code_input = st_ace(language='python', theme='monokai', height=200)
        except Exception:
             code_input = st.text_area("Write Python Code")

    if user_input:
        full_input = user_input
        if code_input:
            full_input += f"\n\n```python\n{code_input}\n```"
        
        send_message(full_input)
        st.rerun()
else:
    st.info("Please upload a resume to start the interview.")

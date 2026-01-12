import streamlit as st
from groq import Groq
from supabase import create_client, Client
import os
 
# Page config
st.set_page_config(page_title="AI Chatbot", page_icon="⚡", layout="wide")
st.markdown("<style>.stApp{max-width:1100px;margin:0 auto;}</style>", unsafe_allow_html=True)
 
# Supabase setup
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found. Add it to .streamlit/secrets.toml (local) or Streamlit Cloud secrets.")
    st.stop()

 
# Get Groq API key
def get_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.getenv("GROQ_API_KEY")
 
GROQ_API_KEY = get_key()
if not GROQ_API_KEY:
    st.error("Groq API key not found.")
    st.stop()
 
try:
    groq_client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error(f"Failed to initialize Groq: {e}")
    st.stop()
 
# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
 
# Sidebar
with st.sidebar:
    st.title("⚡ AI Chatbot")
    user_name = st.text_input("Your Name", value="Anonymous")
    model = st.selectbox("Model", ["llama-3.1-8b-instant"])
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    max_tokens = st.slider("Max tokens", 100, 2000, 512, 50)
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()
 
st.title("💬 Chat with Groq")
 
# Display messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
 
# Chat input
if prompt := st.chat_input("Type your message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Build message history
                api_messages = [{"role": "system", "content": "You are a helpful assistant."}]
                for m in st.session_state.messages[-10:]:
                    api_messages.append({"role": m["role"], "content": m["content"]})
                
                # Get response from Groq
                resp = groq_client.chat.completions.create(
                    messages=api_messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=1,
                    stream=False
                )
                assistant_response = resp.choices[0].message.content
                
                # Display response
                st.write(assistant_response)
                
                # Add to messages
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                
                # Save to Supabase
                try:
                    data = {
                        "user_name": user_name,
                        "message": prompt,
                        "response": assistant_response
                    }
                    result = supabase.table("chat_history").insert(data).execute()
                    st.success("✅ Saved to database", icon="✅")
                except Exception as e:
                    st.error(f"Failed to save: {e}")
                
            except Exception as e:
                st.error(f"Groq request failed: {e}")
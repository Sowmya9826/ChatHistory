import streamlit as st
from groq import Groq
from supabase import create_client, Client
import os
 
# Page config
st.set_page_config(page_title="AI Chatbot", page_icon="⚡", layout="wide")
st.markdown("<style>.stApp{max-width:1100px;margin:0 auto;}</style>", unsafe_allow_html=True)
 
# ===== CONFIG (SAFE FOR RENDER) =====
def get_config(name):
    try:
        return st.secrets.get(name)   # works locally if secrets.toml exists
    except Exception:
        return os.getenv(name)        # works on Render

GROQ_API_KEY = get_config("GROQ_API_KEY")
SUPABASE_URL = get_config("SUPABASE_URL")
SUPABASE_KEY = get_config("SUPABASE_KEY")

missing = []
if not GROQ_API_KEY:
    missing.append("GROQ_API_KEY")
if not SUPABASE_URL:
    missing.append("SUPABASE_URL")
if not SUPABASE_KEY:
    missing.append("SUPABASE_KEY")

if missing:
    st.error(
        "Missing config: " + ", ".join(missing) +
        ". Add them in Render → Environment Variables."
    )
    st.stop()

# Create clients (ONLY after validation)
groq_client = Groq(api_key=GROQ_API_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
# Importing necessary libraries for Streamlit UI
import streamlit as st
import requests
import google.generativeai as genai

st.set_page_config(page_title="AI Mental Health Companion") # UI Page configuartion

# Backend url
API_URL = "http://localhost:5000"

# Setup Gemini API key
genai.configure(api_key="Gemini API Key")
model = genai.GenerativeModel("gemini-2.0-flash")

# Session State Init
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "new_chat" not in st.session_state:
    st.session_state.new_chat = False

# User Registration through user's details
def register():
    st.subheader("Register")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        payload = {"username": username, "email": email, "password": password}
        try:
            res = requests.post(f"{API_URL}/register", json=payload)
            st.success(res.json().get("message", "Registration successful!"))
        except Exception as e:
            st.error(f"Registration failed: {e}")

# Users Login through credentials
def login():
    st.subheader("Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login"):
        payload = {"username": username, "password": password}
        try:
            res = requests.post(f"{API_URL}/login", json=payload)
            data = res.json()
            if res.status_code == 200:
                st.session_state.user_id = data["user_id"]
                st.success("Login successful!")
            else:
                st.error(data.get("error", "Login failed"))
        except Exception as e:
            st.error(f"Login failed: {e}")

# Chatbot UI for interacting with chatbot
def chat():
    st.title("AI-Powered Mental Health Companion")

    if st.button("Start New Chat"):
        st.session_state.chat_history = []
        st.rerun()

    for chat in st.session_state.chat_history:
        with st.chat_message("user"):
            st.markdown(chat["user"])
        with st.chat_message("ai"):
            st.markdown(chat["bot"])

    prompt = st.chat_input("Hi, How are you feeling today?")
    if prompt:
        if prompt.lower() in ["bye", "exit", "quit"]:
            st.success("Thank you for using me. Take care! You've exited the chat.")
            st.stop()

        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            response = model.generate_content(prompt)
            bot_reply = response.text.strip()
        except Exception as e:
            bot_reply = "Sorry, something went wrong."

        with st.chat_message("ai"):
            st.markdown(bot_reply)

        st.session_state.chat_history.append({"user": prompt, "bot": bot_reply})

        try:
            requests.post(f"{API_URL}/save_chat", json={
                "user_id": st.session_state.user_id,
                "message": prompt,
                "response": bot_reply
            })
        except Exception as e:
            st.error(f"Could not save chat: {e}")

# Main UI Routing
st.sidebar.title("MENU")
page = st.sidebar.radio("Go to", ["User Register", "User Login", "Chat"])

if page == "User Register":
    register()
elif page == "User Login":
    login()
elif page == "Chat":
    if st.session_state.user_id:
        chat()
    else:
        st.warning("Please login first to chat with me...")
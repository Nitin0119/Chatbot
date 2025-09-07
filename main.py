import streamlit as st
import re
import time
from openai import OpenAI  # Or any other LLM provider

# --- CONFIGURATION ---
st.set_page_config(page_title="Hiring Assistant Chatbot", page_icon="🤖")

# --- API KEY SETUP ---
# It's recommended to use st.secrets for deployment
# For local development, you can use a sidebar input
OPENAI_API_KEY = "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"
if "OPENAI_API_KEY" in st.secrets:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
else:
    st.warning("API key not found. Please add it to your Streamlit secrets.", icon="⚠️")

# --- PROMPT TEMPLATES ---
# This is a basic system prompt. You can enhance it with more instructions.
SYSTEM_PROMPT = """
You are a friendly and professional AI Hiring Assistant. Your purpose is to collect basic information from a job candidate and then ask them a few technical questions based on their stated tech stack. Be conversational and clear. Do not deviate from the hiring process.
"""

# Prompt to generate technical questions
QUESTION_GENERATION_PROMPT = """
Based on the following tech stack, generate exactly {num_questions} technical interview questions. The questions should be relevant to a candidate with the specified years of experience. The questions should cover different aspects of the technologies listed.

- Years of Experience: {experience}
- Tech Stack: {tech_stack}

Generate the questions in a numbered list format. For example:
1. First question?
2. Second question?
"""


# --- HELPER FUNCTIONS ---

def is_valid_email(email):
    """Simple regex for email validation."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


def is_valid_phone(phone):
    """Simple regex for phone number validation (10 digits)."""
    return re.match(r"^\d{10}$", phone)


def call_llm(messages):
    """Function to call the LLM API."""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Or "gpt-4", "gemini-pro", etc.
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred with the AI model: {e}")
        return "Sorry, I'm having trouble connecting to my brain right now. Please try again later."


# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "step" not in st.session_state:
    st.session_state.step = "greeting"
if "candidate_info" not in st.session_state:
    st.session_state.candidate_info = {}

# --- CHATBOT UI & LOGIC ---

st.title("🤖 AI Hiring Assistant")
st.write("Welcome! This chatbot will ask you a few questions to get started with your application.")
st.markdown("---")

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Main conversation logic
def handle_conversation():
    # GREETING
    if st.session_state.step == "greeting":
        with st.chat_message("assistant"):
            greeting_message = "Hello! I'm an AI Hiring Assistant. I'll ask you a few questions to get started. First, what is your full name?"
            st.markdown(greeting_message)
        st.session_state.messages.append({"role": "assistant", "content": greeting_message})
        st.session_state.step = "get_name"
        return

    # Check for user input
    if prompt := st.chat_input("Your response..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Check for conversation end
        if prompt.lower() in ["exit", "quit", "bye"]:
            with st.chat_message("assistant"):
                end_message = "Thank you for your time. Goodbye!"
                st.markdown(end_message)
            st.session_state.messages.append({"role": "assistant", "content": end_message})
            st.session_state.step = "done"
            time.sleep(2)
            st.rerun()
            return

        # State machine for conversation flow
        step = st.session_state.step
        response = ""

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # 1. GET NAME
                if step == "get_name":
                    st.session_state.candidate_info["full_name"] = prompt
                    response = "Great to meet you! What is your email address?"
                    st.session_state.step = "get_email"

                # 2. GET EMAIL
                elif step == "get_email":
                    if is_valid_email(prompt):
                        st.session_state.candidate_info["email"] = prompt
                        response = "Thanks. What is your 10-digit phone number?"
                        st.session_state.step = "get_phone"
                    else:
                        response = "That doesn't look like a valid email. Could you please enter a valid email address?"

                # 3. GET PHONE
                elif step == "get_phone":
                    if is_valid_phone(prompt):
                        st.session_state.candidate_info["phone"] = prompt
                        response = "Perfect. How many years of professional experience do you have?"
                        st.session_state.step = "get_experience"
                    else:
                        response = "Please enter a valid 10-digit phone number."

                # 4. GET EXPERIENCE
                elif step == "get_experience":
                    st.session_state.candidate_info["experience"] = prompt
                    response = "Got it. What is your current location?"
                    st.session_state.step = "get_location"

                # 5. GET LOCATION
                elif step == "get_location":
                    st.session_state.candidate_info["location"] = prompt
                    response = "And what position(s) are you interested in?"
                    st.session_state.step = "get_position"

                # 6. GET POSITION
                elif step == "get_position":
                    st.session_state.candidate_info["positions"] = prompt
                    response = "Excellent. Now, please list your primary tech stack (e.g., Python, Django, React, PostgreSQL)."
                    st.session_state.step = "get_tech_stack"

                # 7. GET TECH STACK & GENERATE QUESTIONS
                elif step == "get_tech_stack":
                    st.session_state.candidate_info["tech_stack"] = prompt
                    response = "Thank you for providing your details. Based on your tech stack, here are a few technical questions for you. Please answer them one by one."
                    st.markdown(response)  # Initial response
                    st.session_state.messages.append({"role": "assistant", "content": response})

                    # Generate questions using LLM
                    q_prompt = QUESTION_GENERATION_PROMPT.format(
                        num_questions=3,
                        experience=st.session_state.candidate_info['experience'],
                        tech_stack=st.session_state.candidate_info['tech_stack']
                    )

                    llm_messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": q_prompt}
                    ]

                    tech_questions = call_llm(llm_messages)
                    st.markdown(tech_questions)
                    response = tech_questions  # Save questions as the response
                    st.session_state.step = "tech_questions_answered"

                # 8. CONCLUDE
                elif step == "tech_questions_answered":
                    st.session_state.candidate_info["tech_answers"] = prompt
                    response = "Thank you for your answers! That's all the information I need for now. Our hiring team will review your details and get in touch if there's a good fit. Have a great day!"
                    st.session_state.step = "done"

                # FALLBACK
                else:
                    response = "I'm sorry, I'm not sure how to handle that. Could we continue with the application process?"

            # Display final assistant response for the turn
            if st.session_state.step != "tech_questions_answered":  # Avoid duplicating the question list
                st.markdown(response)

            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()


# --- Start the conversation if API key is present ---
if 'client' in locals() or 'client' in globals():
    handle_conversation()
else:
    st.info("Please add your API key in the sidebar to start the chat.")

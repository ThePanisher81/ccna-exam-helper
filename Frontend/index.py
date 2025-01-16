import streamlit as st
import requests
from dotenv import load_dotenv
import os
import random

# Load environment variables from the .env file
load_dotenv()

# Retrieve the backend endpoints from environment variables, or use defaults if not found
BACKEND_URL_SEARCH = os.getenv("BACKEND_URL_SEARCH", "http://127.0.0.1:5000/search")
BACKEND_URL_VALIDATE = os.getenv("BACKEND_URL_VALIDATE", "http://127.0.0.1:5000/validate")

# Configure the basic layout and appearance of the Streamlit app
st.set_page_config(
    page_title="CCNA Exam Helper",
    page_icon="📘",
    layout="centered",
)

# Display the main title and description of the application
st.title("CCNA Exam Helper 📘")
st.markdown("""
**Prepare for your Cisco CCNA certification with ease!**
- Search for questions by entering a topic.
- Answer the questions provided.
- Get detailed feedback and guidance powered by AI.
---
""")

# Prompt the user to enter a CCNA-related topic
topic = st.text_input("Enter a CCNA topic (e.g., Routing, OSPF, Switching, etc.):", "")

# Trigger the question-fetching process when the button is clicked
if st.button("Fetch Questions"):
    # Check if the user has entered a valid topic (non-empty string)
    if not topic.strip():
        st.warning("Please enter a topic to fetch questions.")
    else:
        with st.spinner("Fetching questions..."):
            try:
                # Send the topic to the backend to retrieve relevant questions
                response = requests.post(BACKEND_URL_SEARCH, json={"query": topic})

                # Check response status and handle accordingly
                if response.status_code == 400:
                    # The request was invalid; display the error message from the backend
                    error_msg = response.json().get("error", "Invalid request.")
                    st.error(error_msg)
                elif response.status_code == 200:
                    # The request was successful; parse the JSON response
                    data = response.json()
                    results = data.get("results", [])
                    
                    # If no questions were found for the entered topic
                    if not results:
                        st.error("No questions found for the provided topic. Try another topic.")
                    else:
                        # Store the retrieved questions in session state
                        st.session_state["questions"] = results
                        # Reset user answers and correct answers for new search
                        st.session_state["answers"] = []
                        st.session_state["correct_answers"] = []
                        st.success("Questions fetched successfully! Scroll down to answer them.")
                else:
                    # Any other unexpected status code is handled here
                    st.error(f"Unexpected error: {response.status_code}")
                    st.error(response.text)

            # Catch connection or request errors
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching questions: {e}")

# If there are questions in session state, display them for user interaction
if "questions" in st.session_state and st.session_state["questions"]:
    st.markdown("### Answer the Questions Below:")
    question_texts = []
    correct_answers = []
    user_answers = []

    # Loop through each question from the backend results
    for question_data in st.session_state["questions"]:
        question_id = question_data["id"]
        question_text = question_data["question"]
        correct_answer = question_data["correct_answer"]
        incorrect_answers = question_data["incorrect_answers"]

        # Prepare question options (correct + incorrect answers) if not already done
        if f"q{question_id}_options" not in st.session_state:
            options = [correct_answer] + incorrect_answers
            random.shuffle(options)  # Randomize option order
            st.session_state[f"q{question_id}_options"] = options
        else:
            # Reuse previously stored options if they've already been shuffled
            options = st.session_state[f"q{question_id}_options"]

        # Display the question number and text
        st.markdown(f"**{question_id}. {question_text}**")

        # Provide a radio button for the user to select their answer
        user_answer = st.radio(
            label="",  # Label is omitted for a cleaner look
            options=options,
            key=f"q{question_id}"
        )

        # Collect data for later validation
        question_texts.append(question_text)
        correct_answers.append(correct_answer)
        user_answers.append(user_answer)

    # When the user is ready, submit the answers for validation
    if st.button("Submit Answers"):
        with st.spinner("Submitting answers..."):
            try:
                # Send the user's answers to the backend for validation
                response = requests.post(
                    BACKEND_URL_VALIDATE,
                    json={
                        "query": topic,
                        "questions": question_texts,
                        "correct_answers": correct_answers,
                        "user_answers": user_answers
                    }
                )
                # Raise an exception if the backend response is not successful (4xx/5xx)
                response.raise_for_status()

                # Extract the feedback from the response and display it
                feedback = response.json().get("feedback", {})
                st.markdown("### Feedback:")
                st.markdown(feedback.get("feedback", ""))

            except requests.exceptions.RequestException as e:
                st.error(f"Error submitting answers: {e}")

# Display a small footer at the bottom of the app
st.markdown("""
---
**Developed with ❤️ for aspiring CCNA professionals.**
""")

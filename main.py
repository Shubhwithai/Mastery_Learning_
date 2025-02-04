
import streamlit as st
import matplotlib.pyplot as plt
from openai import OpenAI
import json
import time

# Page config
st.set_page_config(page_title="AI Learning System", layout="wide")

# Initialize session states
if "level" not in st.session_state:
    st.session_state.level = 1
if "score" not in st.session_state:
    st.session_state.score = 0
if "questions" not in st.session_state:
    st.session_state.questions = None
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "topic" not in st.session_state:
    st.session_state.topic = None
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "answer_submitted" not in st.session_state:
    st.session_state.answer_submitted = False

def generate_quiz(topic, level, api_key):
    """Generate quiz questions using OpenAI API"""
    question_types = {
        1: "MCQ (Single Correct), True/False",
        2: "MCQ (Single/Multiple Correct), Matching",
        3: "Passage-Based, Multiple Response, Matching (Complex), Sequence Ordering"
    }
    
    prompt = f"""
        Generate {level}-level quiz questions for {topic}.
        Question types should be: {question_types[level]}.
        Ensure at least 8 questions for Level 1 & 2, and 6 for Level 3.
        Format output as JSON:
        [
          {{"question": "What is 2+2?", "options": ["2", "3", "4", "5"], "answer": "4", "type": "MCQ (Single Correct)"}},
          {{"question": "...", "options": ["..."], "answer": "...", "type": "..."}}
        ]
    """
    
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error generating quiz: {e}")
        return []

def show_dashboard():
    st.title("📊 Student Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Current Level", st.session_state.level)
        st.metric("Total Score", st.session_state.score)
    
    with col2:
        st.subheader("Progress by Skill Area")
        fig, ax = plt.subplots()
        categories = ["Knowledge", "Application", "Analysis"]
        scores = [min(st.session_state.level * 20, 100) for _ in categories]
        ax.bar(categories, scores, color=['blue', 'green', 'red'])
        ax.set_ylabel("Proficiency (%)")
        st.pyplot(fig)

def reset_quiz_state():
    st.session_state.questions = None
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.quiz_started = False
    st.session_state.answer_submitted = False

def handle_answer_submission(answer, correct_answer):
    if answer == correct_answer:
        st.session_state.score += 1
        st.success("Correct! ✅")
    else:
        st.error("Incorrect ❌")
    
    st.session_state.current_index += 1
    st.session_state.answer_submitted = True

def display_quiz():
    st.title(f"Quiz: {st.session_state.topic}")
    
    if not st.session_state.questions:
        with st.spinner("Generating quiz questions..."):
            questions = generate_quiz(
                st.session_state.topic,
                st.session_state.level,
                st.session_state.api_key
            )
            if questions:  # Only update if questions were generated successfully
                st.session_state.questions = questions
            else:
                st.error("Failed to generate questions. Please try again.")
                reset_quiz_state()
                return
    
    if st.session_state.current_index < len(st.session_state.questions):
        question = st.session_state.questions[st.session_state.current_index]
        
        st.subheader(f"Question {st.session_state.current_index + 1}")
        st.write(question["question"])
        
        # Use a unique key for each question
        answer = st.radio(
            "Select your answer:",
            question["options"],
            key=f"q_{st.session_state.current_index}_{st.session_state.level}"
        )
        
        if st.button("Submit Answer", key=f"submit_{st.session_state.current_index}"):
            handle_answer_submission(answer, question["answer"])
    else:
        show_quiz_results()

def show_quiz_results():
    st.subheader("Quiz Complete! 🎉")
    
    total_questions = len(st.session_state.questions)
    score_percentage = (st.session_state.score / total_questions) * 100
    st.write(f"Your Score: {st.session_state.score}/{total_questions} ({score_percentage:.1f}%)")
    
    if score_percentage >= 80 and st.session_state.level < 3:
        st.success(f"Congratulations! You've advanced to Level {st.session_state.level + 1}!")
        if st.button("Start Next Level"):
            st.session_state.level += 1
            reset_quiz_state()
    else:
        if st.button("Try Again"):
            reset_quiz_state()

def main():
    # Sidebar navigation
    menu = st.sidebar.radio("Navigation", ["Home", "Take Quiz", "Dashboard"])
    
    if menu == "Home":
        st.title("AI-Powered Adaptive Learning System")
        st.write("Welcome to the AI-Powered Learning System!")
        st.write("This platform uses GPT-4 to generate personalized quizzes and adapt to your learning level.")
        
        api_key = st.text_input("Enter your OpenAI API Key:", type="password")
        if api_key:
            st.session_state.api_key = api_key
            st.success("API Key saved! You can now take quizzes.")
        else:
            st.warning("Please provide an OpenAI API key to continue.")
            
    elif menu == "Take Quiz":
        if not hasattr(st.session_state, 'api_key') or not st.session_state.api_key:
            st.error("Please enter your OpenAI API key in the Home page first.")
            return
            
        if not st.session_state.quiz_started:
            st.header("Start a New Quiz")
            selected_topic = st.text_input("Enter a topic:", "")
            
            if st.button("Generate Quiz") and selected_topic.strip():
                st.session_state.topic = selected_topic
                st.session_state.quiz_started = True
        else:
            display_quiz()
            
    elif menu == "Dashboard":
        show_dashboard()

if __name__ == "__main__":
    main()

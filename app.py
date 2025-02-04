import streamlit as st
import matplotlib.pyplot as plt
import json
import time
from openai import OpenAI
from streamlit.components.v1 import html

# Page config
st.set_page_config(page_title="Mastery Learning Demo", layout="wide", page_icon="🎓")

# Initialize session states
def init_session():
    session_defaults = {
        "level": 1,
        "score": 0,
        "questions": None,
        "current_index": 0,
        "topic": None,
        "quiz_started": False,
        "api_key": None,
        "history": []
    }
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# Custom CSS
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    .metric-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 10px 0;
    }
    .question-card {
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def generate_quiz(topic, level, api_key):
    """Generate quiz questions using OpenAI API with enhanced formatting"""
    question_types = {
        1: "MCQ (Single Correct), True/False",
        2: "MCQ (Single/Multiple Correct), Matching",
        3: "Passage-Based, Multiple Response, Matching (Complex), Sequence Ordering"
    }
    
    example_questions = {
        1: [{"question": "What is 2+2?", "options": ["3", "4", "5"], "answer": "4", "type": "MCQ"}],
        2: [{"question": "Select prime numbers", "options": ["2", "4", "5", "9"], "answer": ["2", "5"], "type": "Multiple Correct"}],
        3: [{"question": "Arrange planets by size", "options": ["Mars", "Earth", "Jupiter"], "answer": ["Jupiter", "Earth", "Mars"], "type": "Sequence"}]
    }
    
    prompt = f"""
    Generate {level}-level quiz questions about {topic}. Follow these rules:
    1. Question types: {question_types[level]}
    2. {['8 questions', '8 questions', '6 questions'][level-1]}
    3. Format as VALID JSON array
    4. For multiple correct answers, use array in 'answer'
    5. For sequences, use ordered array in 'answer'
    6. Example format: {json.dumps(example_questions[level])}
    
    Output ONLY the JSON array, no extra text.
    """
    
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        questions = json.loads(response.choices[0].message.content)
        return validate_questions(questions)
    except Exception as e:
        st.error(f"Quiz generation failed: {str(e)}")
        return []

def validate_questions(questions):
    """Ensure questions have valid structure"""
    valid_questions = []
    for q in questions:
        if all(key in q for key in ['question', 'options', 'answer', 'type']):
            if isinstance(q['answer'], (str, list)) and len(q['options']) >= 2:
                valid_questions.append(q)
    return valid_questions

def show_dashboard():
    st.title("📈 Learning Analytics Dashboard")
    
    with st.expander("Progress Overview", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Level", f"Level {st.session_state.level}")
        with col2:
            st.metric("Total Correct", f"{st.session_state.score} Answers")
        with col3:
            attempts = len(st.session_state.history)
            st.metric("Total Attempts", attempts)
    
    with st.expander("Progress History"):
        if st.session_state.history:
            fig, ax = plt.subplots()
            dates = [h['date'] for h in st.session_state.history]
            # Calculate cumulative correct answers instead of using 'score'
            scores = []
            correct_count = 0
            for h in st.session_state.history:
                if h['correct']:
                    correct_count += 1
                scores.append(correct_count)
            
            ax.plot(dates, scores, marker='o')
            ax.set_title("Score Progression")
            ax.set_ylabel("Correct Answers")
            st.pyplot(fig)

def question_card(question, index):
    """Styled question container with dynamic input types"""
    with st.container():
        st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
        
        st.subheader(f"Question {index+1} ({question['type']})")
        st.markdown(f"**{question['question']}**")
        
        # Progress bar
        progress = index/len(st.session_state.questions)
        st.progress(progress)
        
        # Dynamic input types
        if "Multiple" in question['type']:
            answers = st.multiselect("Select all correct answers:", 
                                   question['options'],
                                   key=f"q_{index}")
        elif "Sequence" in question['type']:
            answers = st.multiselect("Arrange in correct order:", 
                                   question['options'],
                                   default=question['options'],
                                   key=f"q_{index}")
        else:
            answers = st.radio("Select answer:", 
                             question['options'],
                             key=f"q_{index}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        return answers

def show_congratulations():
    """Animated celebration component"""
    html(f"""
    <div style="text-align:center">
        <h3 style="color:#4CAF50">🎉 Level Complete! 🎉</h3>
        <lottie-player src="https://assets10.lottiefiles.com/packages/lf20_6wutsrox.json"  
            background="transparent" speed="1" style="width: 200px; height: 200px; margin: auto" loop autoplay>
        </lottie-player>
    </div>
    <script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>
    """, height=250)

def main():
    # Sidebar with quick actions
    with st.sidebar:
        st.header("Quick Actions")
        if st.button("🔄 Reset Session"):
            init_session()
            st.rerun()
        
        st.divider()
        st.write("**Current Status**")
        st.write(f"Level: {st.session_state.level}")
        st.write(f"Score: {st.session_state.score}")
    
    # Main content
    page = st.sidebar.radio("Navigation", ["🏠 Home", "📝 Take Quiz", "📊 Dashboard"])
    
    if page == "🏠 Home":
        st.title("AI-Powered Mastery Learning Demo")
        st.image("https://images.unsplash.com/photo-1589254065878-42c9da997008?ixlib=rb-1.2.1&auto=format&fit=crop&w=1920&q=80", 
                use_column_width=True)
        
        st.write("""
        ## Experience Adaptive Learning
        **Key Features:**
        - 🎯 Level-based progression system
        - 📈 Real-time learning analytics
        - 🤖 AI-generated assessments
        - 🔄 Mastery-based advancement
        """)
        
        with st.expander("🚀 Get Started"):
            api_key = st.text_input("Enter OpenAI API Key:", type="password")
            if api_key:
                st.session_state.api_key = api_key
                st.success("Key verified!")
                
            st.write("1. Enter your API key\n2. Choose a topic\n3. Start learning!")

    elif page == "📝 Take Quiz":
        if not st.session_state.api_key:
            st.warning("🔑 Please enter your API key on the Home page")
            return
        
        if not st.session_state.quiz_started:
            st.header("Start New Learning Session")
            topic = st.selectbox("Choose a topic:", 
                               ["Mathematics", "Science", "History", "Custom Topic..."])
            if "Custom" in topic:
                topic = st.text_input("Enter custom topic:")
            
            if st.button("Start Learning Session"):
                if topic.strip():
                    st.session_state.topic = topic
                    st.session_state.quiz_started = True
                    st.rerun()
                else:
                    st.error("Please enter a valid topic")
        else:
            if not st.session_state.questions:
                with st.spinner("🧠 Generating personalized questions..."):
                    st.session_state.questions = generate_quiz(
                        st.session_state.topic,
                        st.session_state.level,
                        st.session_state.api_key
                    )
                if not st.session_state.questions:
                    st.session_state.quiz_started = False
                    return
            
            if st.session_state.current_index < len(st.session_state.questions):
                question = st.session_state.questions[st.session_state.current_index]
                user_answer = question_card(question, st.session_state.current_index)
                
                if st.button("✅ Submit Answer"):
                    correct_answer = question['answer']
                    if isinstance(correct_answer, list):
                        correct = set(user_answer) == set(correct_answer)
                    else:
                        correct = user_answer == correct_answer
                    
                    if correct:
                        st.session_state.score += 1
                        st.success("Correct! Well done!")
                    else:
                        st.error(f"Improve this: Correct answer is {correct_answer}")
                    
                    st.session_state.history.append({
                        "date": time.strftime("%Y-%m-%d %H:%M"),
                        "question": question['question'],
                        "correct": correct
                    })
                    
                    st.session_state.current_index += 1
                    time.sleep(1)
                    st.rerun()
            else:
                show_congratulations()
                score_percent = (st.session_state.score/len(st.session_state.questions))*100
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Session Results")
                    st.write(f"**Accuracy:** {score_percent:.1f}%")
                    st.write(f"**Questions Attempted:** {len(st.session_state.questions)}")
                
                with col2:
                    if score_percent >= 80 and st.session_state.level < 3:
                        st.success("🎓 Mastery Achieved! Unlocking next level...")
                        time.sleep(1)
                        st.session_state.level += 1
                        st.session_state.questions = None
                        st.session_state.current_index = 0
                        st.session_state.score = 0
                        st.rerun()
                    else:
                        st.warning("Keep practicing to unlock the next level")
                        if st.button("Retry Level"):
                            st.session_state.questions = None
                            st.session_state.current_index = 0
                            st.session_state.score = 0
                            st.rerun()

    elif page == "📊 Dashboard":
        show_dashboard()

if __name__ == "__main__":
    main()

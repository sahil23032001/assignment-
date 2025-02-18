import streamlit as st
import requests
import json
import matplotlib.pyplot as plt

# Together AI configuration
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"  # Example endpoint
TOGETHER_API_KEY = "f5bf26528f0577e0a6c2513e858404d48eaa1f64e07e88b8a33b2610fc66529e"  # Replace with your actual API key

def generate_question(difficulty_level):
    prompt = f"""
    Generate a GMAT-style quantitative question with {difficulty_level} difficulty.
    Include 5 answer choices and indicate the correct answer index (0-4).
    Format the response as JSON with: question, choices, correct_answer, difficulty.
    Example:
    {{
        "question": "If x + y = 7 and 3x - y = 5, what is the value of x?",
        "choices": ["2", "3", "4", "5", "6"],
        "correct_answer": 1,
        "difficulty": "{difficulty_level}"
    }}
    """

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo-128K",  # Updated Together AI model
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.7
    }

    response = requests.post(TOGETHER_API_URL, headers=headers, json=payload)

    try:
        response_data = response.json()
        if "choices" in response_data and len(response_data["choices"]) > 0:
            return json.loads(response_data["choices"][0]["message"]["content"])
        else:
            raise ValueError("No valid choices in API response")
    except Exception as e:
        st.error(f"Error generating question: {e}")
        return None

def calculate_score(difficulty):
    return {'easy': 1, 'medium': 2, 'hard': 3}[difficulty.lower()]

def initialize_session():
    st.session_state.update({
        'current_question': 0,
        'questions': [],
        'user_answers': [],
        'score': 0,
        'current_difficulty': 'medium',
        'test_started': True
    })

# Streamlit UI Setup
st.title("AI-Powered Adaptive GMAT Test")

if not st.session_state.get('test_started'):
    if st.button("Start Test"):
        initialize_session()

if st.session_state.get('test_started'):
    if st.session_state.current_question < 10:
        if len(st.session_state.questions) <= st.session_state.current_question:
            with st.spinner("Generating question... Please wait."):
                question = generate_question(st.session_state.current_difficulty)
                if question:
                    st.session_state.questions.append(question)
                else:
                    if st.button("Retry Question Generation"):
                        st.rerun()

        if len(st.session_state.questions) > st.session_state.current_question:
            current_q = st.session_state.questions[st.session_state.current_question]

            st.subheader(f"Question {st.session_state.current_question + 1}")
            st.markdown(f"**Question:** {current_q['question']}")

            user_answer = st.radio("Select your answer:", 
                                    [f"{chr(65+i)}) {choice}" for i, choice in enumerate(current_q['choices'])])

            if st.button("Submit Answer"):
                selected_index = ord(user_answer[0].upper()) - 65
                is_correct = selected_index == current_q['correct_answer']

                if is_correct:
                    st.session_state.score += calculate_score(current_q['difficulty'])
                    difficulties = ['easy', 'medium', 'hard']
                    new_index = min(difficulties.index(current_q['difficulty'].lower()) + 1, 2)
                    st.session_state.current_difficulty = difficulties[new_index]
                else:
                    difficulties = ['easy', 'medium', 'hard']
                    new_index = max(difficulties.index(current_q['difficulty'].lower()) - 1, 0)
                    st.session_state.current_difficulty = difficulties[new_index]

                st.session_state.user_answers.append(is_correct)
                st.session_state.current_question += 1
                st.rerun()
    else:
        st.subheader("Test Results")

        result_data = []
        for i, q in enumerate(st.session_state.questions):
            result_data.append({
                "Question": i + 1,
                "Correct": "Yes" if st.session_state.user_answers[i] else "No",
                "Points": calculate_score(q['difficulty']) if st.session_state.user_answers[i] else 0
            })

        st.dataframe(result_data)

        min_score = 0
        max_score = 30
        avg_score = 15  # Average possible score

        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#0E1117')  # Match Streamlit's theme
        ax.set_facecolor('#0E1117')

        # Create gradient background
        ax.imshow([[0,1]], cmap='Blues', extent=[0, max_score, -2, 2], 
                aspect='auto', alpha=0.1)

        # Plot reference lines
        ax.axvline(x=avg_score, color='yellow', linestyle='--', alpha=0.5, label='Average Score')
        ax.axvline(x=st.session_state.score, color='#4CAF50', linewidth=3, label='Your Score')

        # Create score range visualization
        ax.barh(0, max_score, height=1, color='#1a1a1a', alpha=0.3)
        ax.barh(0, st.session_state.score, height=1, color='#4CAF50', alpha=0.7)

        # Add annotations
        ax.text(st.session_state.score + 0.5, 0, 
                f'{st.session_state.score}/30\n({st.session_state.score/max_score:.0%})',
                color='white', va='center', fontsize=12, fontweight='bold')
        
        ax.text(0.5, 1.2, 'Score Breakdown', 
                color='white', fontsize=14, transform=ax.transAxes,
                ha='center', fontweight='bold')

        # Style adjustments
        ax.set_xlim(0, max_score)
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('white')
        
        ax.tick_params(axis='x', colors='white')
        ax.xaxis.label.set_color('white')
        
        # Add legend
        ax.legend(facecolor='#0E1117', edgecolor='none', 
                labelcolor='white', loc='upper right')

        # Add metric boxes
        box_style = dict(boxstyle='round', facecolor='#262730', edgecolor='none', pad=0.3)
        ax.text(0.01, 0.95, 
                f"▫ Correct Answers: {sum(st.session_state.user_answers)}/10\n"
                f"▫ Hard Questions: {len([q for q in st.session_state.questions if q['difficulty'] == 'hard'])}\n"
                f"▫ Accuracy: {sum(st.session_state.user_answers)/10:.0%}",
                transform=ax.transAxes, color='white', 
                fontsize=10, bbox=box_style, verticalalignment='top')

        st.pyplot(fig)

        if st.button("Retake Test"):
            initialize_session()
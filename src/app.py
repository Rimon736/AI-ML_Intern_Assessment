import streamlit as st
import httpx
import uuid

API_URL = "http://localhost:8000" # Maps to FastAPI

st.set_page_config(page_title="Adaptive Prep System", layout="wide")
st.title("Adaptive Document Prep System")

# 1. Initialize session states
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
# Unique ID to prevent old answers from "sticking" across new generations
if "quiz_id" not in st.session_state:
    st.session_state.quiz_id = str(uuid.uuid4())
# Track if the user has finalized and saved their score
if "session_saved" not in st.session_state:
    st.session_state.session_saved = False

st.sidebar.header("Configuration")
selected_sections = st.sidebar.multiselect(
    "Select Sections to Study:", 
    options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    default=[5, 8]
)

if st.sidebar.button("Generate Quiz Session"):
    with st.spinner("Generating adaptive questions (checking history)..."):
        try:
            response = httpx.post(
                f"{API_URL}/api/generate", 
                json={"section_ids": selected_sections},
                timeout=60.0
            )
            
            if response.status_code == 200:
                st.session_state.quiz_data = response.json().get("data", {})
                # Reset states for the fresh quiz
                st.session_state.quiz_id = str(uuid.uuid4())
                st.session_state.session_saved = False
                st.sidebar.success("Quiz Generated Successfully!")
            else:
                st.sidebar.error(f"API Error: {response.text}")
        except Exception as e:
            st.sidebar.error(f"Failed to connect to backend: {e}")

# 2. Render the quiz
if st.session_state.quiz_data:
    total_questions = 0
    answered_questions = 0
    correct_answers = 0
    
    # Store answers to send to the database later
    qa_results = []
    
    for sec_id, questions in st.session_state.quiz_data.items():
        st.subheader(f"Section {sec_id}")
        
        for i, q in enumerate(questions):
            total_questions += 1
            # Unique key fixes the "pre-selected wrong answer" bug
            unique_q_key = f"{st.session_state.quiz_id}_{sec_id}_{i}"
            
            with st.expander(f"Q{i+1}: {q['question']}", expanded=True):
                user_ans = st.radio(
                    "Options:", 
                    q['options'], 
                    key=unique_q_key, 
                    index=None,
                    disabled=st.session_state.session_saved # Lock radio buttons after saving
                )
                
                if user_ans:
                    answered_questions += 1
                    is_correct = (user_ans == q['answer'])
                    
                    if is_correct:
                        correct_answers += 1
                        st.success("Correct!")
                    else:
                        st.error("Incorrect")
                        
                    st.info(f"**Correct Answer:** {q['answer']}\n\n**Explanation:** {q['explanation']}")
                    
                    # Package the result for the database
                    qa_results.append({
                        "section_id": int(sec_id),
                        "question": q,
                        "user_answer": user_ans,
                        "is_correct": is_correct
                    })

    # 3. SCORING AND CALL-TO-ACTION SECTION
    st.markdown("---")
    st.subheader("Session Summary")
    
    # Live Progress Bar
    progress = answered_questions / total_questions if total_questions > 0 else 0
    st.progress(progress, text=f"Questions Answered: {answered_questions} / {total_questions}")
    
    # When all questions are answered, reveal the final score and Next Steps
    if answered_questions == total_questions and total_questions > 0:
        score_percentage = (correct_answers / total_questions) * 100
        delta_color = "normal" if score_percentage >= 60 else "inverse"
        
        st.metric(
            label="Final Score", 
            value=f"{score_percentage:.0f}%", 
            delta=f"{correct_answers} / {total_questions} Correct",
            delta_color=delta_color
        )
        
        # Save to Database Flow
        if not st.session_state.session_saved:
            st.info("💡 **Next Step:** Save this session to record your weak areas. The system will use this history to generate adaptive questions next time!")
            
            if st.button("💾 Save Session to Database", type="primary"):
                try:
                    payload = {
                        "scenario_name": "Interactive_UI",
                        "section_ids": [int(k) for k in st.session_state.quiz_data.keys()],
                        "qa_results": qa_results
                    }
                    resp = httpx.post(f"{API_URL}/api/save", json=payload, timeout=10.0)
                    
                    if resp.status_code == 200:
                        st.session_state.session_saved = True
                        st.balloons()
                        st.rerun() # Refresh UI to lock in the saved state
                    else:
                        st.error(f"Failed to save: {resp.text}")
                except Exception as e:
                    st.error(f"Backend Connection Error: {e}")
        else:
            # Clear instructions after saving
            st.success("**Session Complete and Saved to Knowledge Base!**")
            st.markdown("### What should I do next?")
            st.markdown("1. Scroll to the sidebar and click **'Generate Quiz Session'** again for the *same* sections. You will see the **Adaptive RAG Intelligence** actively target the questions you just got wrong!")
            st.markdown("2. Or, select entirely new sections to test new material.")
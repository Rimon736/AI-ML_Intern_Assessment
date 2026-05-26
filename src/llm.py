import json
from groq import Groq
from typing import List, Dict
from src.config import GROQ_API_KEY, QUESTIONS_PER_SECTION
from src.db import get_weak_areas
from src.config import OUTPUT_DIR, logger

# Initialize the Groq Client
client = Groq(api_key=GROQ_API_KEY)

def generate_mcqs(section_id: int, section_text: str) -> List[Dict]:
    """
    Generates MCQs for a section. Applies Adaptive Intelligence if historical weak areas exist.
    """
    weak_areas = get_weak_areas(section_id)
    
    prompt = f"""
    You are an expert military/intelligence analyst creating a training quiz.
    Based on the provided text for Section {section_id}, generate {QUESTIONS_PER_SECTION} multiple-choice questions.
    """

    if weak_areas:
        prompt += "\n\nCRITICAL ADAPTIVE INSTRUCTION: The user has previously answered questions incorrectly about the following topics. "
        prompt += "You MUST generate at least 2 questions that test these specific concepts to ensure they have learned from their mistakes:\n"
        for i, mistake in enumerate(weak_areas):
            prompt += f"- Concept missed: '{mistake['question_text']}' (Correct answer was: {mistake['correct_answer']})\n"

    # Groq JSON mode requires the root to be an Object, so we wrap the array in a "questions" key.
    prompt += f"""
    \n\nSOURCE TEXT:\n{section_text[:15000]}
    
    OUTPUT FORMAT:
    You must output a strictly valid JSON object containing a single key called "questions". 
    The value of "questions" must be an array of objects. Do not include markdown formatting or backticks.
    Format exactly like this:
    {{
        "questions": [
            {{
                "question": "Question text here?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "answer": "Exact string of the correct option from the options list",
                "explanation": "Brief explanation of why this is correct."
            }}
        ]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # <--- Updated active model
            messages=[
                {"role": "system", "content": "You are a helpful API that outputs purely in JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        
        # Parse the JSON response and extract the array
        result = json.loads(response.choices[0].message.content)
        return result.get("questions", [])
        
    except Exception as e:
        logger.info(f"Error generating questions for Section {section_id}: {e}")
        
        # Graceful fallback as requested by the assessment rubric
        logger.info(f"\n   [!] Groq API Failed. Engaging Graceful Fallback.")
        fallback_questions = []
        for i in range(QUESTIONS_PER_SECTION):
            if weak_areas and i < 2:
                topic = f"Review of past mistake: {weak_areas[i%len(weak_areas)]['question_text'][:30]}..."
            else:
                topic = f"Standard concept from Section {section_id}"

            fallback_questions.append({
                "question": f"Simulated Question {i+1}: What is the primary focus regarding {topic}?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "answer": "Option A",
                "explanation": f"Simulated explanation for {topic}. The LLM API is currently unavailable."
            })
        return fallback_questions
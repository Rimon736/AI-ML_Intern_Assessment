import os
import json
import random
import argparse
import time    
from typing import List
from src.db import init_db, save_session, export_kb_snapshot
from src.parser import extract_sections_from_pdf
from src.llm import generate_mcqs
from src.config import OUTPUT_DIR, logger

def simulate_user_answer(question: dict) -> str:
    """
    Simulates a user answering a question. 
    Weighted to be correct 60% of the time to generate realistic 'weak area' history.
    """
    options = question['options']
    correct_answer = question['answer']
    
    # 60% chance to get it right, 40% chance to pick a random wrong answer
    if random.random() < 0.6:
        return correct_answer
    else:
        wrong_options = [opt for opt in options if opt != correct_answer]
        # Fallback if no wrong options (malformed question)
        return random.choice(wrong_options) if wrong_options else options[0]

def run_prep_session(scenario_name: str, section_ids: List[int], all_sections: dict, iteration: int = None):
    """Executes the core prep flow for given sections."""
    logger.info(f"\n{'='*50}\nStarting Session: {scenario_name} over Sections: {section_ids}\n{'='*50}")
    
    session_results = []
    generated_questions = []

    for sec_id in section_ids:
        if sec_id not in all_sections:
            logger.info(f"Warning: Section {sec_id} not found in PDF. Skipping.")
            continue
        
        logger.info(f"-> Generating adaptive questions for Section {sec_id}...")
        text_chunk = all_sections[sec_id]
        
        # LLM Generates Questions (Adaptive logic handled inside this function)
        questions = generate_mcqs(sec_id, text_chunk)
        generated_questions.extend(questions)

        # Simulate user taking the quiz
        logger.info(f"-> Simulating user answers for Section {sec_id}...")
        for q in questions:
            user_ans = simulate_user_answer(q)
            is_correct = (user_ans == q['answer'])
            
            session_results.append({
                "section_id": sec_id,
                "question": q,
                "user_answer": user_ans,
                "is_correct": is_correct
            })
            
            status = "✅" if is_correct else "❌"
            logger.info(f"   {status} Q: {q['question'][:60]}... | User: {user_ans[:30]}...")
        
        # Respect API limits by pausing between sections
        logger.info("-> Pausing for 30 seconds to respect API free-tier limits...")
        time.sleep(30)
    # Save to Knowledge Base
    save_session(scenario_name, section_ids, session_results)
    logger.info("\n-> Session saved to Knowledge Base.")

    # File Export Logic (For Assessment Submission)
    if iteration is not None:
        iter_dir = os.path.join(OUTPUT_DIR, f"scenario_b_iter{iteration}")
        os.makedirs(iter_dir, exist_ok=True)
        
        # Save generated questions
        q_file = os.path.join(iter_dir, f"questions_iter{iteration}.json")
        with open(q_file, 'w', encoding='utf-8') as f:
            json.dump(generated_questions, f, indent=4)
            
        # Export KB Snapshot
        kb_file = os.path.join(iter_dir, f"kb_snapshot_iter{iteration}.json")
        export_kb_snapshot(kb_file)
        
        logger.info(f"-> Evaluation outputs saved to {iter_dir}/")

def main():
    parser = argparse.ArgumentParser(description="Adaptive Document Prep System")
    parser.add_argument('command', choices=['scenario-a', 'scenario-b'], help='Scenario to execute')
    args = parser.parse_args()

    # Initialize DB and ensure output dir exists
    init_db()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logger.info("Parsing PDF corpus (SLATEFALL_DOSSIER)...")
    all_sections = extract_sections_from_pdf()
    
    if not all_sections:
        logger.info("Failed to extract sections. Ensure the PDF is in the root directory.")
        return

    if args.command == 'scenario-a':
        run_prep_session("Scenario A (Cold Start)", [1, 2], all_sections)
        
    elif args.command == 'scenario-b':
        # Scenario B: 3 Iterations demonstrating Adaptive Intelligence
        run_prep_session("Scenario B - Iteration 1", [5, 8], all_sections, iteration=1)
        run_prep_session("Scenario B - Iteration 2", [6, 8, 9], all_sections, iteration=2)
        run_prep_session("Scenario B - Iteration 3", [8], all_sections, iteration=3)

if __name__ == "__main__":
    main()
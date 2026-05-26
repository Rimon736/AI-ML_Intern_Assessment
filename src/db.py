import sqlite3
import json
import os
from typing import List, Dict
from src.config import DB_PATH

def init_db():
    """Initializes the SQLite Knowledge Base schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create Sessions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            sections TEXT,
            scenario_name TEXT
        )
    ''')

    # Create Questions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            section_id INTEGER,
            question_text TEXT,
            options TEXT, 
            correct_answer TEXT,
            explanation TEXT,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    ''')

    # Create User Responses Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            user_answer TEXT,
            is_correct BOOLEAN,
            FOREIGN KEY(question_id) REFERENCES questions(id)
        )
    ''')

    conn.commit()
    conn.close()

def save_session(scenario_name: str, section_ids: List[int], qa_results: List[Dict]) -> int:
    """Saves a complete session to the KB."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Save Session
    cursor.execute(
        "INSERT INTO sessions (sections, scenario_name) VALUES (?, ?)", 
        (json.dumps(section_ids), scenario_name)
    )
    session_id = cursor.lastrowid

    # Save Questions and Responses
    for item in qa_results:
        # Save Question
        cursor.execute('''
            INSERT INTO questions (session_id, section_id, question_text, options, correct_answer, explanation)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session_id, 
            item['section_id'], 
            item['question']['question'], 
            json.dumps(item['question']['options']),
            item['question']['answer'],
            item['question']['explanation']
        ))
        question_id = cursor.lastrowid

        # Save Response
        cursor.execute('''
            INSERT INTO user_responses (question_id, user_answer, is_correct)
            VALUES (?, ?, ?)
        ''', (
            question_id, 
            item['user_answer'], 
            item['is_correct']
        ))

    conn.commit()
    conn.close()
    return session_id

def get_weak_areas(section_id: int) -> List[Dict]:
    """Retrieves questions the user previously got wrong for a specific section."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT q.question_text, q.correct_answer, q.explanation
        FROM user_responses ur
        JOIN questions q ON ur.question_id = q.id
        WHERE ur.is_correct = 0 AND q.section_id = ?
    ''', (section_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def export_kb_snapshot(output_path: str):
    """Exports a snapshot of the last 5 sessions to a JSON file."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get last 5 sessions
    cursor.execute("SELECT * FROM sessions ORDER BY timestamp DESC LIMIT 5")
    sessions = [dict(s) for s in cursor.fetchall()]

    for session in sessions:
        cursor.execute('''
            SELECT q.section_id, q.question_text, ur.user_answer, ur.is_correct 
            FROM questions q
            JOIN user_responses ur ON q.id = ur.question_id
            WHERE q.session_id = ?
        ''', (session['id'],))
        session['history'] = [dict(r) for r in cursor.fetchall()]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, indent=4)
        
    conn.close()
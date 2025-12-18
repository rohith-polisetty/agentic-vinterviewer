import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "vintervu.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Candidates table
    c.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            resume_text TEXT,
            profile_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Sessions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            candidate_id INTEGER,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            FOREIGN KEY (candidate_id) REFERENCES candidates (id)
        )
    ''')
    
    # Interview Logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS interview_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            question TEXT,
            answer TEXT,
            evaluation TEXT,
            score INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def save_candidate(name, resume_text, profile_data):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO candidates (name, resume_text, profile_json) VALUES (?, ?, ?)",
        (name, resume_text, json.dumps(profile_data))
    )
    candidate_id = c.lastrowid
    conn.commit()
    conn.close()
    return candidate_id

def create_session(session_id, candidate_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO sessions (id, candidate_id, status) VALUES (?, ?, ?)",
        (session_id, candidate_id, "ACTIVE")
    )
    conn.commit()
    conn.close()

def log_interaction(session_id, question, answer, evaluation, score):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO interview_logs (session_id, question, answer, evaluation, score) VALUES (?, ?, ?, ?, ?)",
        (session_id, question, answer, evaluation, score)
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")

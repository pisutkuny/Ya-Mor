import sqlite3
import datetime
import pandas as pd
import streamlit as st

DB_FILE = 'appointments.db' # Keeping the same DB file for simplicity, but we will add new tables

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Users (Caregivers/Patient Pair)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            role TEXT, -- 'patient' or 'caregiver'
            line_token TEXT, -- For Line Notify
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Medications (The 'Stock' and 'Schedule')
    # frequency: JSON string e.g., '["morning", "evening"]'
    c.execute('''
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            image_path TEXT,
            dosage TEXT, -- e.g. "1 Tablet"
            frequency TEXT, 
            stock INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Activity Logs (History for Doctor)
    c.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            med_id INTEGER,
            action TEXT, -- 'taken', 'skipped', 'missed'
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            note TEXT,
            FOREIGN KEY(med_id) REFERENCES medications(id)
        )
    ''')
    
    # Ensure old table exists so we don't break V1 if they toggle back (Optional/Legacy)
    c.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital TEXT,
            doctor TEXT,
            date TEXT,
            time TEXT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

# --- Medication Functions ---
def add_medication(name, image_path, dosage, frequency, stock):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO medications (name, image_path, dosage, frequency, stock)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, image_path, dosage, str(frequency), stock))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error adding medication: {e}")
        return False

def get_medications():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM medications", conn)
    conn.close()
    return df

# --- Activity Log Functions ---
def log_activity(med_id, action, note=""):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO activity_logs (med_id, action, note)
            VALUES (?, ?, ?)
        ''', (med_id, action, note))
        
        # Deduct stock if taken
        if action == 'taken':
            c.execute('UPDATE medications SET stock = stock - 1 WHERE id = ?', (med_id,))
            
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error logging activity: {e}")
        return False

def get_activity_logs():
    conn = sqlite3.connect(DB_FILE)
    query = """
        SELECT l.id, m.name as med_name, l.action, l.timestamp, l.note 
        FROM activity_logs l
        JOIN medications m ON l.med_id = m.id
        ORDER BY l.timestamp DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# --- User/Settings Functions ---
def save_user_settings(name, line_token):
    # For simplicity, we assume single user pair mostly, so we update or insert ID 1
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Check if exists
    c.execute("SELECT count(*) FROM users WHERE id = 1")
    exists = c.fetchone()[0]
    if exists:
        c.execute("UPDATE users SET name=?, line_token=? WHERE id=1", (name, line_token))
    else:
        c.execute("INSERT INTO users (id, name, line_token) VALUES (1, ?, ?)", (name, line_token))
    conn.commit()
    conn.close()

def get_user_settings():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, line_token FROM users WHERE id = 1")
    row = c.fetchone()
    conn.close()
    if row:
        return {"name": row[0], "line_token": row[1]}
    return None

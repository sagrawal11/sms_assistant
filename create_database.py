#!/usr/bin/env python3
"""
Database initialization script for Alfred the Butler
Creates all required tables if they don't exist
"""

import sqlite3
import os

def init_database():
    """Initialize the database with all required tables"""
    
    # Database path
    db_path = os.path.join('databases', 'personal_assistant.db')
    
    print(f"🔧 Initializing database at: {db_path}")
    
    # Ensure databases directory exists
    os.makedirs('databases', exist_ok=True)
    
    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("✅ Connected to database")
    
    # Create food logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            food_name TEXT NOT NULL,
            calories INTEGER NOT NULL,
            protein REAL NOT NULL,
            carbs REAL NOT NULL,
            fat REAL NOT NULL,
            restaurant TEXT,
            portion_multiplier REAL DEFAULT 1.0
        )
    ''')
    print("✅ food_logs table created")
    
    # Create water logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS water_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            amount_ml REAL NOT NULL,
            amount_oz REAL NOT NULL
        )
    ''')
    print("✅ water_logs table created")
    
    # Create gym logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gym_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            exercise TEXT NOT NULL,
            sets INTEGER,
            reps INTEGER,
            weight REAL,
            notes TEXT
        )
    ''')
    print("✅ gym_logs table created")
    
    # Create reminders and todos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders_todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            due_date DATETIME,
            completed BOOLEAN DEFAULT FALSE,
            completed_at DATETIME
        )
    ''')
    print("✅ reminders_todos table created")
    
    # Create calendar events cache table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_event_id TEXT UNIQUE NOT NULL,
            summary TEXT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            location TEXT,
            description TEXT,
            cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✅ calendar_events table created")
    
    # Commit changes and close
    conn.commit()
    conn.close()
    
    print("🎉 Database initialization complete!")
    print(f"📁 Database file: {db_path}")
    
    # Show table info
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("\n📊 Available tables:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"   • {table[0]}: {count} records")
    
    conn.close()

if __name__ == "__main__":
    init_database()

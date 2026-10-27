"""
database.py
-----------
Handles everything related to the SQLite database.
Only this class talks to SQL, so the rest of the project stays clean.
"""

import os
import sqlite3

# The database file is created next to this file, so the project
# works no matter which folder you run it from in VS Code.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "hostel.db")


class Database:
    def __init__(self, db_name=DEFAULT_DB_PATH):
        self.db_name = db_name
        self.create_tables()
        self.create_default_admin()

    # ---------- connection ----------
    def connect(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # lets us use row["column_name"]
        return conn

    # ---------- table creation ----------
    def create_tables(self):
        conn = self.connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                username      TEXT NOT NULL UNIQUE,
                password      TEXT NOT NULL,
                role          TEXT NOT NULL,
                reg_no        TEXT,
                hostel_block  TEXT,
                room_no       TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS complaints (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id    INTEGER NOT NULL,
                student_name  TEXT NOT NULL,
                room_no       TEXT NOT NULL,
                category      TEXT NOT NULL,
                description   TEXT NOT NULL,
                status        TEXT NOT NULL DEFAULT 'Pending',
                remark        TEXT DEFAULT '',
                date_filed    TEXT NOT NULL,
                is_private    INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        # Migration for old database files created before the personal-issue feature
        cols = [r[1] for r in conn.execute("PRAGMA table_info(complaints)").fetchall()]
        if "is_private" not in cols:
            conn.execute("ALTER TABLE complaints ADD COLUMN is_private INTEGER NOT NULL DEFAULT 0")
        conn.commit()
        conn.close()

    def create_default_admin(self):
        """Creates one admin account the first time the project runs."""
        if self.fetch_one("SELECT id FROM users WHERE role = 'admin'") is None:
            self.execute(
                "INSERT INTO users (name, username, password, role) VALUES (?, ?, ?, ?)",
                ("Hostel Warden", "admin", "admin123", "admin"),
            )

    # ---------- helper methods ----------
    def execute(self, query, params=()):
        """Runs INSERT / UPDATE / DELETE. Returns the id of the inserted row."""
        conn = self.connect()
        cursor = conn.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def fetch_one(self, query, params=()):
        conn = self.connect()
        row = conn.execute(query, params).fetchone()
        conn.close()
        return row

    def fetch_all(self, query, params=()):
        conn = self.connect()
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return rows

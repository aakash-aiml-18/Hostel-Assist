"""Export hostel.db tables to CSV files (open directly in Excel).

Used two ways:
  - manually:  python export_to_excel.py
  - automatic: import export_to_excel; export_to_excel.export_all()
    (called by services.py after every DB change, so the CSVs are
    always up to date with whatever you do on the website)
"""
import csv
import sqlite3
import os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hostel.db")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

TABLES = {
    "users": ["id", "name", "username", "password", "role", "reg_no", "hostel_block", "room_no"],
    "complaints": ["id", "student_id", "student_name", "room_no", "category",
                   "description", "status", "remark", "date_filed", "is_private"],
}


def export_all():
    try:
        conn = sqlite3.connect(DB)
        for table, cols in TABLES.items():
            rows = conn.execute(f"SELECT {', '.join(cols)} FROM {table}").fetchall()
            out = os.path.join(OUT_DIR, f"{table}.csv")
            with open(out, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(cols)
                w.writerows(rows)
        conn.close()
    except Exception:
        pass  # never break the website because of an export issue


if __name__ == "__main__":
    export_all()
    print("Done. users.csv and complaints.csv updated.")

"""
services.py
-----------
Business logic of the project. Two classes:

  * AuthService       -> register and login
  * ComplaintManager  -> connects the LINKED LIST with the DATABASE

How the linked list and the database work together:
  1. When the app starts, every complaint is read from SQLite and added
     to the linked list (load_from_database).
  2. When something changes (new complaint, new status, delete), the
     linked list is updated AND the change is saved to SQLite,
     so nothing is lost when the server stops.
"""

from datetime import datetime

from linked_list import ComplaintLinkedList
from models import Admin, Complaint, Student
import export_to_excel


# ---------------------------------------------------------------------
#  AUTHENTICATION
# ---------------------------------------------------------------------
class AuthService:
    def __init__(self, db):
        self.db = db

    def register_student(self, name, reg_no, hostel_block, room_no, password):
        """Returns True if registered, False if the reg. number already exists."""
        existing = self.db.fetch_one("SELECT id FROM users WHERE username = ?", (reg_no,))
        if existing is not None:
            return False
        if hostel_block not in Complaint.BLOCKS:
            return False
        if room_no not in Complaint.FLOOR_ROOMS.get(hostel_block, []):
            return False
        self.db.execute(
            "INSERT INTO users (name, username, password, role, reg_no, hostel_block, room_no) "
            "VALUES (?, ?, ?, 'student', ?, ?, ?)",
            (name, reg_no, password, reg_no, hostel_block, room_no),
        )
        export_to_excel.export_all()
        return True

    def login(self, username, password, role):
        """Returns a Student / Admin object if the login is correct, else None."""
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE username = ? AND role = ?", (username, role)
        )
        if row is None:
            return None
        user = self._build_user(row)
        if user.check_password(password):
            return user
        return None

    def get_user_by_id(self, user_id):
        row = self.db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
        if row is None:
            return None
        return self._build_user(row)

    def delete_student_account(self, user_id, password):
        """Permanently removes the student. Returns (ok, reason).
        Requires the correct password so nobody else can delete it."""
        row = self.db.fetch_one("SELECT * FROM users WHERE id = ? AND role = 'student'", (user_id,))
        if row is None:
            return False, "Account not found."
        user = self._build_user(row)
        if not user.check_password(password):
            return False, "Incorrect password. Account was NOT deleted."
        self.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        export_to_excel.export_all()
        return True, "Account deleted."

    def _build_user(self, row):
        """Creates the correct child object (polymorphism)."""
        if row["role"] == "admin":
            return Admin(row["id"], row["name"], row["username"], row["password"])
        return Student(
            row["id"], row["name"], row["username"], row["password"],
            row["reg_no"], row["hostel_block"], row["room_no"],
        )


# ---------------------------------------------------------------------
#  COMPLAINT MANAGER  (linked list + database)
# ---------------------------------------------------------------------
class ComplaintManager:
    def __init__(self, db):
        self.db = db
        self.complaints = ComplaintLinkedList()
        self.load_from_database()

    def load_from_database(self):
        """Fills the linked list with all complaints saved in the database."""
        rows = self.db.fetch_all("SELECT * FROM complaints ORDER BY id ASC")
        for row in rows:
            # row.keys() guard keeps old hostel.db files (without is_private) working
            is_private = row["is_private"] if "is_private" in row.keys() else 0
            complaint = Complaint(
                row["id"], row["student_id"], row["student_name"], row["room_no"],
                row["category"], row["description"], row["status"],
                row["remark"], row["date_filed"], is_private,
            )
            self.complaints.add_complaint(complaint)

    # ---------- student actions ----------
    def file_complaint(self, student, room_no, category, description, is_private=False):
        """Creates a complaint.

        `room_no` is the room number entered by the student (e.g. "218", "K205").
        """
        room_no = room_no if room_no else (student.room_no or "")
        date_filed = datetime.now().strftime("%d-%m-%Y %H:%M")
        new_id = self.db.execute(
            "INSERT INTO complaints (student_id, student_name, room_no, category, "
            "description, status, remark, date_filed, is_private) VALUES (?, ?, ?, ?, ?, 'Pending', '', ?, ?)",
            (student.user_id, student.name, room_no, category, description, date_filed, int(bool(is_private))),
        )
        complaint = Complaint(
            new_id, student.user_id, student.name, room_no,
            category, description, "Pending", "", date_filed, is_private,
        )
        self.complaints.add_complaint(complaint)
        export_to_excel.export_all()
        return complaint

    def get_student_complaints(self, student_id):
        """Newest complaint first."""
        return list(reversed(self.complaints.get_by_student(student_id)))

    def delete_own_complaint(self, student_id, complaint_id):
        """A student may delete only HIS OWN complaint and only while Pending."""
        complaint = self.complaints.search_by_id(complaint_id)
        if complaint is None or complaint.student_id != student_id:
            return False
        if complaint.status != "Pending":
            return False
        return self._delete(complaint_id)

    # ---------- admin actions ----------
    def get_all_complaints(self, status=None, category=None, hostel=None, floor=None, month=None, year=None):
        """Newest complaint first. Optional filter by status, category, hostel, floor, month and year.

        category/hostel/floor are matched with LIKE so a student can type a few
        letters and still get everything that matches (for example "Internet" or
        "Kanchenjunga"). floor is matched on the room number like "K205" or "K301".
        month: month name, e.g. "Jan", "Feb", "Dec"
        year:  4-digit year, e.g. "2026"
        """
        if status in Complaint.VALID_STATUSES:
            found = self.complaints.filter_by_status(status)
        else:
            found = self.complaints.display_all()

        if category:
            found = [c for c in found if category.lower() in c.category.lower()]
        if hostel:
            found = [c for c in found if self._student_hostel_of(c) is not None and hostel.lower() in self._student_hostel_of(c).lower()]
        if floor:
            found = [c for c in found if floor in Complaint.FLOOR_ROOMS.get(self._student_hostel_of(c), [])]
        if month:
            # Convert month name to numeric month (Jan=1, Feb=2, ...)
            import re as _re
            month_map = {n: str(i + 1).zfill(2) for i, n in enumerate(Complaint.MONTHS)}
            month_num = month_map.get(month)
            if month_num:
                found = [c for c in found if len(c.date_filed) >= 6 and c.date_filed[3:5] == month_num]
        if year:
            found = [c for c in found if (year + " ") in c.date_filed]
        return list(reversed(found))

    def _student_hostel_of(self, complaint):
        """Hostel of the complaint's student, looked up in the users table."""
        row = self.db.fetch_one(
            "SELECT hostel_block FROM users WHERE id = ?", (complaint.student_id,)
        )
        return row["hostel_block"] if row is not None else None

    def get_complaints_by_category(self, category):
        """All complaints whose category contains the given text (newest first)."""
        found = self.complaints.display_all()
        if category:
            found = [c for c in found if category.lower() in c.category.lower()]
        return list(reversed(found))

    def get_pie_data(self):
        """Complaint counts grouped by category, ordered largest first.

        Each item carries sweep angles plus a ready-to-render SVG path and a
        distinct colour, so the warden's dashboard can draw a pie chart without
        any math in the template.

        Returns a list of dicts:
        [{"category": ..., "count": ..., "color": "#...", "percent": 12.5,
          "start": 0, "end": 45, "path": "M ..."}, ...]
        """
        import math
        rows = self.complaints.display_all()
        totals = {}
        for c in rows:
            totals[c.category] = totals.get(c.category, 0) + 1
        # sort from most complaints to least
        items = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
        total = sum(item[1] for item in items)
        if total == 0:
            return []
        palette = [
            "#c9a227", "#1d4fa1", "#177245", "#b4232a", "#9a6b0f",
            "#7c3aed", "#0891b2", "#be185d", "#5d6f7f",
        ]
        cx, cy, r = 100, 100, 80
        collected = []
        accumulated = 0
        for idx, (cat, cnt) in enumerate(items):
            half = 360 * cnt / total
            start = accumulated
            end = accumulated + half
            color = palette[idx % len(palette)]
            if len(items) == 1:
                path = "M {} {} A {} {} 0 1 1 {} {} A {} {} 0 1 1 {} {} Z".format(
                    cx - r, cy, r, r, cx + r, cy, r, r, cx - r, cy)
            else:
                srad = math.radians(start - 90)
                erad = math.radians(end - 90)
                x1 = cx + r * math.cos(srad)
                y1 = cy + r * math.sin(srad)
                x2 = cx + r * math.cos(erad)
                y2 = cy + r * math.sin(erad)
                large = 1 if half > 180 else 0
                path = "M {} {} L {:.2f} {:.2f} A {} {} 0 {} 1 {:.2f} {:.2f} Z".format(
                    cx, cy, x1, y1, r, r, large, x2, y2)
            collected.append({
                "category": cat,
                "count": cnt,
                "color": color,
                "percent": round(100 * cnt / total, 1),
                "start": start,
                "end": end,
                "arc": 1 if end > start else 0,
                "path": path,
            })
            accumulated += half
        return collected

    def get_complaints_by_category(self, category):
        """All complaints whose category contains the given text (newest first)."""
        found = self.complaints.display_all()
        if category:
            found = [c for c in found if category.lower() in c.category.lower()]
        return list(reversed(found))

    def get_complaints_by_hostel(self, hostel):
        """All complaints from students of the given hostel (newest first)."""
        found = self.complaints.display_all()
        if hostel:
            found = [
                c for c in found
                if self._student_hostel_of(c) is not None and hostel.lower() in self._student_hostel_of(c).lower()
            ]
        return list(reversed(found))

    def search_complaint(self, complaint_id):
        return self.complaints.search_by_id(complaint_id)

    def update_status(self, complaint_id, new_status, remark):
        if new_status not in Complaint.VALID_STATUSES:
            return False
        if not self.complaints.update_status(complaint_id, new_status, remark):
            return False
        self.db.execute(
            "UPDATE complaints SET status = ?, remark = ? WHERE id = ?",
            (new_status, remark, complaint_id),
        )
        export_to_excel.export_all()
        return True

    def admin_delete_complaint(self, complaint_id):
        return self._delete(complaint_id)

    def delete_student_complaints(self, student_id):
        """Removes ALL complaints of a student (used when the account is deleted)."""
        for complaint in list(self.complaints.get_by_student(student_id)):
            self._delete(complaint.id)

    def get_counts(self):
        counts = self.complaints.count_by_status()
        counts["Total"] = len(self.complaints)
        return counts

    # ---------- internal ----------
    def _delete(self, complaint_id):
        if not self.complaints.delete_complaint(complaint_id):
            return False
        self.db.execute("DELETE FROM complaints WHERE id = ?", (complaint_id,))
        export_to_excel.export_all()
        return True

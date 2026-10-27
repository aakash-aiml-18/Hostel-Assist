"""
models.py
---------
The main classes of the project (OOP concepts used here):

  * Abstraction   -> User is an abstract class (cannot be used directly)
  * Inheritance   -> Student and Admin inherit from User
  * Polymorphism  -> Student and Admin each define get_role() and
                     get_dashboard_route() in their own way
  * Encapsulation -> private attributes (__password, __status ...) are
                     reached only through properties / methods
"""

from abc import ABC, abstractmethod
from datetime import datetime


# ---------------------------------------------------------------------
#  USER CLASSES
# ---------------------------------------------------------------------
class User(ABC):
    """Abstract base class for every person who can log in."""

    def __init__(self, user_id, name, username, password):
        self._user_id = user_id
        self._name = name
        self._username = username
        self.__password = password  # private (name-mangled)

    # --- read-only properties (encapsulation) ---
    @property
    def user_id(self):
        return self._user_id

    @property
    def name(self):
        return self._name

    @property
    def username(self):
        return self._username

    # --- password is never exposed, only checked ---
    def check_password(self, password):
        return self.__password == password

    # --- abstract methods: every child class MUST implement these ---
    @abstractmethod
    def get_role(self):
        pass

    @abstractmethod
    def get_dashboard_route(self):
        pass


class Student(User):
    """A hostel student. Logs in with the registration number."""

    def __init__(self, user_id, name, username, password, reg_no, hostel_block, room_no):
        super().__init__(user_id, name, username, password)
        self._reg_no = reg_no
        self._hostel_block = hostel_block
        self._room_no = room_no

    @property
    def room_no(self):
        """Room number saved with zero padding, e.g. "004" => Floor 2."""
        return self._room_no

    def room_floor(self):
        """Which floor this room sits on, based on the floor map."""
        return self._room_no.zfill(3) if self._room_no else None

    @property
    def reg_no(self):
        return self._reg_no

    @property
    def hostel_block(self):
        return self._hostel_block

    @property
    def room_no(self):
        return self._room_no

    def get_role(self):
        return "student"

    def get_dashboard_route(self):
        return "student_dashboard"


class Admin(User):
    """The hostel warden / admin."""

    def get_role(self):
        return "admin"

    def get_dashboard_route(self):
        return "admin_dashboard"


# ---------------------------------------------------------------------
#  COMPLAINT CLASS
# ---------------------------------------------------------------------
class Complaint:
    """One complaint filed by a student. This object is stored inside
    a Node of the linked list (see linked_list.py)."""

    VALID_STATUSES = ("Pending", "In Progress", "Resolved")
    CATEGORIES = (
        "Plumbing / Water",
        "Electrical",
        "Cleanliness",
        "Mess / Food",
        "Internet / Wi-Fi",
        "Furniture",
        "Security",
        "Personal / Roommate Issue",
        "Other",
    )
    BLOCKS = ("Kanchenjunga", "Nilgiri")
    # 3 floors in each hostel, 10 rooms per floor
    # Kanchenjunga: Floor 1 = K101-K110, Floor 2 = K201-K210, Floor 3 = K301-K310
    # Nilgiri:      Floor 1 = N101-N110, Floor 2 = N201-N210, Floor 3 = N301-N310
    FLOORS = ("Floor 1", "Floor 2", "Floor 3")
    FLOOR_ROOMS = {
        "Kanchenjunga": ["K101", "K102", "K103", "K104", "K105", "K106", "K107", "K108", "K109", "K110",
                         "K201", "K202", "K203", "K204", "K205", "K206", "K207", "K208", "K209", "K210",
                         "K301", "K302", "K303", "K304", "K305", "K306", "K307", "K308", "K309", "K310"],
        "Nilgiri": ["N101", "N102", "N103", "N104", "N105", "N106", "N107", "N108", "N109", "N110",
                    "N201", "N202", "N203", "N204", "N205", "N206", "N207", "N208", "N209", "N210",
                    "N301", "N302", "N303", "N304", "N305", "N306", "N307", "N308", "N309", "N310"],
    }
    MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    YEARS = [str(y) for y in range(2026, 2030)]

    def __init__(self, complaint_id, student_id, student_name, room_no,
                 category, description, status="Pending", remark="", date_filed=None,
                 is_private=False):
        self.__id = complaint_id
        self.__student_id = student_id
        self.__student_name = student_name
        self.__room_no = room_no
        self.__category = category
        self.__description = description
        self.__status = status
        self.__remark = remark
        self.__date_filed = date_filed or datetime.now().strftime("%d-%m-%Y %H:%M")
        self.__is_private = bool(is_private)  # personal/confidential note to warden

    # --- getters (properties) ---
    @property
    def id(self):
        return self.__id

    @property
    def student_id(self):
        return self.__student_id

    @property
    def student_name(self):
        return self.__student_name

    @property
    def room_no(self):
        return self.__room_no

    @property
    def category(self):
        return self.__category

    @property
    def description(self):
        return self.__description

    @property
    def status(self):
        return self.__status

    @property
    def remark(self):
        return self.__remark

    @property
    def date_filed(self):
        return self.__date_filed

    @property
    def is_private(self):
        return self.__is_private

    # --- the only way to change status/remark (validated) ---
    def update_status(self, new_status, remark=""):
        if new_status not in Complaint.VALID_STATUSES:
            raise ValueError("Invalid status: " + str(new_status))
        self.__status = new_status
        self.__remark = remark

    def __str__(self):
        return f"Complaint #{self.__id} [{self.__status}] {self.__category} - Room {self.__room_no}"

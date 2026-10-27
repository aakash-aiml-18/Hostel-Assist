# Hostel Complaint Box Management System

A simple website made with **Python (Flask)** and **SQLite**, built using **OOP concepts**
and a **singly linked list** as the data structure.

## How to run (VS Code)

1. Install Python 3 and open this folder in VS Code (File > Open Folder).
2. Open the terminal in VS Code (Ctrl + `) and install Flask:
   ```
   pip install -r requirements.txt
   ```
3. Start the website:
   ```
   python app.py
   ```
4. Open **http://127.0.0.1:5000** in the browser.

The database file `hostel.db` is created automatically the first time you run the project.

## Logins

| Portal  | Username / ID                   | Password   |
|---------|----------------------------------|------------|
| Admin   | `admin`                          | `admin123` |
| Student | Register first (reg. number = login ID) | your choice |

Passwords are stored as plain text, as decided for this project.

## Project files

| File             | What it contains |
|------------------|------------------|
| `app.py`         | Flask routes (web pages) for the student portal and admin portal |
| `models.py`      | `User` (abstract), `Student`, `Admin`, `Complaint` classes |
| `linked_list.py` | `Node` and `ComplaintLinkedList` (the data structure) |
| `services.py`    | `AuthService` (register/login) and `ComplaintManager` (linked list + database) |
| `database.py`    | `Database` class: all SQLite code |
| `templates/`     | HTML pages |
| `static/style.css` | Styling (hostel theme) |
| `static/fonts/`  | Fonts (Zilla Slab and Public Sans, open-source), so the site looks the same offline |

## OOP concepts used (where to point in the viva)

- **Abstraction:** `User` in `models.py` is an abstract class (`ABC`) with abstract methods `get_role()` and `get_dashboard_route()`.
- **Inheritance:** `Student` and `Admin` inherit from `User`.
- **Polymorphism:** `Student` and `Admin` implement the same methods differently, and `AuthService._build_user()` returns the right object.
- **Encapsulation:** private attributes such as `__password` in `User` and `__status` in `Complaint`, accessed only through properties and methods (`check_password()`, `update_status()`).
- **Composition:** `ComplaintManager` *has a* `ComplaintLinkedList` and a `Database`.

## Linked list

```
head -> [Complaint 1 | next] -> [Complaint 2 | next] -> [Complaint 3 | None]
                                                              ^ tail
```

Operations in `linked_list.py`: `add_complaint` (insert at end), `search_by_id`,
`delete_complaint`, `update_status`, `filter_by_status`, `get_by_student`,
`count_by_status`, `display_all` (traversal).

**How it works with the database:** when the server starts, all complaints are read from
SQLite into the linked list. Every new complaint, status change or deletion updates the
linked list *and* the database, so data is not lost when the server stops.

## Design

Hostel theme: pale green corridor walls, a bottle-green top bar, brass door plates for the
portals, a cork notice board for the student's complaints and rubber-stamp status marks
(Pending, In Progress, Resolved). Every page except the home page has a **Back to Home**
button in the top bar. When a user is logged in, the home page shows a link back to their dashboard.

## Features

**Student portal:** register, login, file a complaint (category + description + room),
view own complaints with status and admin remark, delete own complaint while it is still Pending.

**Admin portal:** login, dashboard counts (Total / Pending / In Progress / Resolved),
view all complaints, filter by status, search by complaint ID, update status with a remark,
delete a complaint.

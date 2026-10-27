
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for

from database import Database
from models import Complaint
from services import AuthService, ComplaintManager

# ---------------------------------------------------------------------
#  Site branding — change this one line to rename your whole website.
#  Recommended: "HostelDesk" (see alternate names in README / home page)
# ---------------------------------------------------------------------
SITE_NAME = "Hostel Assist"
SITE_TAGLINE = "Your Stay, Our Responsibility"

app = Flask(__name__)
app.secret_key = "hostel-complaint-box-secret"  # needed for login sessions

# Create the objects once, when the server starts
db = Database()
auth_service = AuthService(db)
complaint_manager = ComplaintManager(db)  # loads the linked list from the database

HOSTEL_BLOCKS = ["Kanchenjunga", "Nilgiri"]


# ---------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------
def current_user():
    """Returns the logged-in Student/Admin object (or None)."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return auth_service.get_user_by_id(user_id)


@app.context_processor
def inject_user():
    """Makes `logged_in_user` + site branding available in every template."""
    return {
        "logged_in_user": current_user(),
        "site_name": SITE_NAME,
        "site_tagline": SITE_TAGLINE,
    }


def login_required(role):
    """Decorator: allows the page only for a logged-in user of the given role."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if user is None or user.get_role() != role:
                flash("Please login first.", "error")
                return redirect(url_for(f"{role}_login"))
            return view(user, *args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------------
#  Home
# ---------------------------------------------------------------------
@app.route("/")
def home():
    # The home page is always reachable: the "Back to Home" button leads here.
    # If someone is logged in, home.html shows a link to their dashboard.
    return render_template("home.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


# ---------------------------------------------------------------------
#  STUDENT PORTAL
# ---------------------------------------------------------------------
@app.route("/student/register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        reg_no = (request.form.get("reg_no") or "").strip()
        hostel_block = request.form.get("hostel_block") or ""
        room_no = (request.form.get("room_no") or "").strip()
        password = request.form.get("password") or ""

        if not (name and reg_no and room_no and password):
            flash("Please fill in all the fields.", "error")
        elif hostel_block not in HOSTEL_BLOCKS:
            flash("Please select a valid hostel.", "error")
        elif auth_service.register_student(name, reg_no, hostel_block, room_no, password):
            flash("Registration successful! You can log in now.", "success")
            return redirect(url_for("student_login"))
        else:
            flash("This registration number is already registered.", "error")
    return render_template("student_register.html", blocks=HOSTEL_BLOCKS)


@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        user = auth_service.login((request.form.get("reg_no") or "").strip(), request.form.get("password") or "", "student")
        if user is not None:
            session["user_id"] = user.user_id
            return redirect(url_for("student_dashboard"))
        flash("Wrong registration number or password.", "error")
    return render_template("login.html", role="student")


@app.route("/student/dashboard")
@login_required("student")
def student_dashboard(student):
    complaints = complaint_manager.get_student_complaints(student.user_id)
    return render_template("student_dashboard.html", student=student, complaints=complaints)


@app.route("/student/file", methods=["GET", "POST"])
@login_required("student")
def file_complaint(student):
    if request.method == "POST":
        room_no = (request.form.get("room_no") or "").strip()
        floor = (request.form.get("floor") or "").strip()
        category = request.form.get("category") or ""
        description = (request.form.get("description") or "").strip()
        is_private = request.form.get("is_private") == "1"

        if not room_no or not description or category not in Complaint.CATEGORIES:
            flash("Please fill in all the fields.", "error")
        else:
            complaint = complaint_manager.file_complaint(student, room_no, category, description, is_private)
            if is_private:
                flash(f"Personal note #{complaint.id} sent directly to the warden.", "success")
            else:
                flash(f"Complaint #{complaint.id} filed successfully.", "success")
            return redirect(url_for("student_dashboard"))
    return render_template("file_complaint.html", student=student, categories=Complaint.CATEGORIES)


@app.route("/student/delete/<int:complaint_id>", methods=["POST"])
@login_required("student")
def student_delete(student, complaint_id):
    if complaint_manager.delete_own_complaint(student.user_id, complaint_id):
        flash(f"Complaint #{complaint_id} deleted.", "success")
    else:
        flash("Only your own pending complaints can be deleted.", "error")
    return redirect(url_for("student_dashboard"))


@app.route("/student/delete-account", methods=["GET", "POST"])
@login_required("student")
def student_delete_account(student):
    """Student leaves the hostel: permanently removes the account."""
    if request.method == "POST":
        password = request.form.get("password") or ""
        if request.form.get("confirm") != "DELETE":
            flash("Type DELETE exactly to confirm.", "error")
        else:
            ok, reason = auth_service.delete_student_account(student.user_id, password)
            if not ok:
                flash(reason, "error")
            else:
                complaint_manager.delete_student_complaints(student.user_id)
                session.pop("user_id", None)
                flash("Your account and all your complaints have been permanently deleted.", "success")
                return redirect(url_for("home"))
    return render_template("student_delete_account.html", student=student)


# ---------------------------------------------------------------------
#  ADMIN PORTAL
# ---------------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        user = auth_service.login((request.form.get("username") or "").strip(), request.form.get("password") or "", "admin")
        if user is not None:
            session["user_id"] = user.user_id
            return redirect(url_for("admin_dashboard"))
        flash("Wrong username or password.", "error")
    return render_template("login.html", role="admin")


@app.route("/admin/dashboard")
@login_required("admin")
def admin_dashboard(admin):
    status = request.args.get("status", "")
    search_id = request.args.get("search_id", "").strip()
    category = request.args.get("category", "").strip()
    hostel = request.args.get("hostel", "").strip()
    floor = request.args.get("floor", "").strip()
    month = request.args.get("month", "").strip()
    year = request.args.get("year", "").strip()

    if search_id:                                   # search by complaint id
        found = complaint_manager.search_complaint(int(search_id)) if search_id.isdigit() else None
        complaints = [found] if found is not None else []
    else:                                           # filter by status (+ category / hostel / floor / month / year)
        complaints = complaint_manager.get_all_complaints(
            status=status, category=category, hostel=hostel, floor=floor, month=month, year=year
        )

    # data used by the comparison chart
    chart = complaint_manager.get_pie_data()

    return render_template(
        "admin_dashboard.html",
        admin=admin,
        complaints=complaints,
        counts=complaint_manager.get_counts(),
        statuses=Complaint.VALID_STATUSES,
        selected_status=status,
        categories=Complaint.CATEGORIES,
        hostels=Complaint.BLOCKS,
        floors=Complaint.FLOORS,
        selected_category=category,
        selected_hostel=hostel,
        selected_floor=floor,
        selected_month=month,
        selected_year=year,
        months=Complaint.MONTHS,
        years=Complaint.YEARS,
        search_id=search_id,
        chart=chart,
    )


@app.route("/admin/update/<int:complaint_id>", methods=["POST"])
@login_required("admin")
def admin_update(admin, complaint_id):
    new_status = request.form.get("status") or ""
    remark = (request.form.get("remark") or "").strip()
    if complaint_manager.update_status(complaint_id, new_status, remark):
        flash(f"Complaint #{complaint_id} updated to {new_status}.", "success")
    else:
        flash("Could not update the complaint.", "error")
    return redirect(request.referrer or url_for("admin_dashboard"))


@app.route("/admin/delete/<int:complaint_id>", methods=["POST"])
@login_required("admin")
def admin_delete(admin, complaint_id):
    if complaint_manager.admin_delete_complaint(complaint_id):
        flash(f"Complaint #{complaint_id} deleted.", "success")
    else:
        flash("Complaint not found.", "error")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    app.run(debug=True)

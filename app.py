from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from datetime import datetime, timedelta
from models import db, User, Homework, Thread, Resource, Submission
import os

# -------------------------------
# App Factory
# -------------------------------
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "app.db")


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = "dev-secret-key"

    db.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


# -------------------------------
# Routes
# -------------------------------
def register_routes(app):
    @app.route("/")
    def index():
        """Homepage → upcoming assignments"""
        now = datetime.utcnow()
        upcoming = (
            Homework.query.filter(Homework.due_date >= now)
            .order_by(Homework.due_date)
            .limit(10)
            .all()
        )
        return render_template("index.html", upcoming=upcoming)

    # -------------------------------
    # Calendar
    # -------------------------------
    @app.route("/calendar")
    def calendar_view():
        return render_template("calendar.html")

    @app.route("/api/homeworks")
    def api_homeworks():
        """Return homework events formatted for FullCalendar"""
        homeworks = Homework.query.all()
        events = [
            {
                "id": hw.id,
                "title": f"{hw.subject}: {hw.title}",
                "start": hw.due_date.isoformat(),
                "url": url_for("homework_detail", hw_id=hw.id),
                "color": hw.color,
            }
            for hw in homeworks
        ]
        return jsonify(events)

    # -------------------------------
    # Homework CRUD
    # -------------------------------
    @app.route("/homework/create", methods=["GET", "POST"])
    def create_homework():
        if request.method == "POST":
            title = request.form["title"]
            subject = request.form["subject"]
            description = request.form.get("description")
            due_date = datetime.fromisoformat(request.form["due_date"])
            color = request.form.get("color") or "#2d9cdb"

            hw = Homework(
                title=title,
                subject=subject,
                description=description,
                due_date=due_date,
                color=color,
            )
            db.session.add(hw)
            db.session.commit()
            flash("✅ Homework created", "success")
            return redirect(url_for("index"))

        return render_template("create_homework.html")

    @app.route("/homework/<int:hw_id>", methods=["GET", "POST"])
    def homework_detail(hw_id):
        hw = Homework.query.get_or_404(hw_id)

        # Post a thread message
        if request.method == "POST":
            author = request.form.get("author") or "Anonymous"
            message = request.form.get("message", "").strip()
            if message:
                t = Thread(homework=hw, author=author, message=message)
                db.session.add(t)
                db.session.commit()
                flash("💬 Comment posted", "success")
            return redirect(url_for("homework_detail", hw_id=hw_id))

        submissions = Submission.query.filter_by(homework_id=hw.id).all()
        return render_template("homework_detail.html", hw=hw, submissions=submissions)

    @app.route("/homework/<int:hw_id>/resource/add", methods=["POST"])
    def add_resource(hw_id):
        hw = Homework.query.get_or_404(hw_id)
        title = request.form.get("title")
        url = request.form.get("url")

        if url:
            r = Resource(homework=hw, title=title, url=url)
            db.session.add(r)
            db.session.commit()
            flash("📎 Resource added", "success")

        return redirect(url_for("homework_detail", hw_id=hw_id))

    @app.route("/homework/<int:hw_id>/submit", methods=["POST"])
    def submit_homework(hw_id):
        hw = Homework.query.get_or_404(hw_id)

        student_name = request.form.get("student_name") or "Student"
        student = User.query.filter_by(name=student_name).first()
        if not student:
            student = User(name=student_name)
            db.session.add(student)
            db.session.commit()

        content = request.form.get("content")
        if not content:
            flash("⚠️ Submission cannot be empty", "warning")
            return redirect(url_for("homework_detail", hw_id=hw_id))

        sub = Submission(homework=hw, student=student, content=content)
        db.session.add(sub)
        db.session.commit()
        flash("✅ Submitted successfully", "success")
        return redirect(url_for("homework_detail", hw_id=hw_id))

    # -------------------------------
    # Dashboard
    # -------------------------------
    @app.route("/dashboard")
    def dashboard():
        """Simple progress metrics"""
        total = Homework.query.count()
        now = datetime.utcnow()
        pending = Homework.query.filter(Homework.due_date >= now).count()
        completed = Submission.query.with_entities(Submission.homework_id).distinct().count()

        grades = [s.grade for s in Submission.query.filter(Submission.grade.isnot(None)).all()]
        avg_grade = sum(grades) / len(grades) if grades else None

        subjects = {}
        for hw in Homework.query.all():
            subj = hw.subject
            subjects.setdefault(subj, {"total": 0, "submitted": 0})
            subjects[subj]["total"] += 1
        for s in Submission.query.all():
            subj = s.homework.subject
            subjects[subj]["submitted"] += 1

        return render_template(
            "dashboard.html",
            total=total,
            pending=pending,
            completed=completed,
            avg_grade=avg_grade,
            subjects=subjects,
        )

    # -------------------------------
    # Dev seed route
    # -------------------------------
    @app.route("/_seed")
    def seed():
        """Create sample data for testing (dev only)"""
        if Homework.query.count() > 0:
            return "Already seeded"

        now = datetime.utcnow()
        hw1 = Homework(
            title="Algebra worksheet",
            subject="Math",
            description="Exercises 1-10",
            due_date=now + timedelta(days=3),
            color="#ff6b6b",
        )
        hw2 = Homework(
            title="Short essay",
            subject="English",
            description="Topic: Climate",
            due_date=now + timedelta(days=7),
            color="#ffd93d",
        )
        hw3 = Homework(
            title="Chemistry lab",
            subject="Science",
            description="Write the lab report",
            due_date=now + timedelta(days=1),
            color="#2d9cdb",
        )
        db.session.add_all([hw1, hw2, hw3])
        db.session.commit()

        # Add sample resource & thread
        r = Resource(
            homework=hw1,
            title="Video explanation",
            url="https://example.com/algebra-video",
        )
        t = Thread(homework=hw1, author="Teacher A", message="Remember to show your steps.")
        db.session.add_all([r, t])
        db.session.commit()

        return "✅ Seeded sample data"


# -------------------------------
# Run app
# -------------------------------
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

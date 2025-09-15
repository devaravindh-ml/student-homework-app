from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# -------------------------------
# User model (student/teacher)
# -------------------------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    is_teacher = db.Column(db.Boolean, default=False)

    # Relationships
    submissions = db.relationship(
        "Submission", back_populates="student", cascade="all, delete"
    )


# -------------------------------
# Homework model
# -------------------------------
class Homework(db.Model):
    __tablename__ = "homeworks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=False)
    color = db.Column(db.String(7), default="#2d9cdb")  # Hex color for calendar
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    threads = db.relationship(
        "Thread", back_populates="homework", cascade="all, delete"
    )
    resources = db.relationship(
        "Resource", back_populates="homework", cascade="all, delete"
    )
    submissions = db.relationship("Submission", back_populates="homework")


# -------------------------------
# Thread model (discussion under homework)
# -------------------------------
class Thread(db.Model):
    __tablename__ = "threads"

    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer, db.ForeignKey("homeworks.id"), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    homework = db.relationship("Homework", back_populates="threads")


# -------------------------------
# Resource model (study materials)
# -------------------------------
class Resource(db.Model):
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer, db.ForeignKey("homeworks.id"), nullable=False)
    title = db.Column(db.String(200))
    url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    homework = db.relationship("Homework", back_populates="resources")


# -------------------------------
# Submission model (student submissions)
# -------------------------------
class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer, db.ForeignKey("homeworks.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    grade = db.Column(db.Float, nullable=True)  # None until graded
    feedback = db.Column(db.Text, nullable=True)

    # Relationships
    homework = db.relationship("Homework", back_populates="submissions")
    student = db.relationship("User", back_populates="submissions")

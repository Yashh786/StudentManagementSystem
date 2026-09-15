import os
import secrets
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory, session
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    students = db.relationship("Student", back_populates="owner", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    course = db.Column(db.String(120), nullable=False)
    attendance = db.Column(db.Float, nullable=False, default=100)
    math = db.Column(db.Float, nullable=False)
    science = db.Column(db.Float, nullable=False)
    english = db.Column(db.Float, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    owner = db.relationship("User", back_populates="students")
    __table_args__ = (UniqueConstraint("owner_id", "student_id", name="uq_student_owner_id"),)

    @property
    def average(self):
        return (self.math + self.science + self.english) / 3

    @property
    def grade(self):
        if self.average >= 90:
            return "A"
        if self.average >= 75:
            return "B"
        if self.average >= 60:
            return "C"
        return "Fail"

    def to_dict(self):
        return {
            "id": self.student_id,
            "name": self.name,
            "age": self.age,
            "course": self.course,
            "attendance": self.attendance,
            "marks": {"Math": self.math, "Science": self.science, "English": self.english},
            "average": round(self.average, 1),
            "grade": self.grade,
        }


def create_app(test_config=None):
    app = Flask(__name__, static_folder=None)
    secret_key = os.getenv("SECRET_KEY")
    if os.getenv("FLASK_ENV") == "production" and not secret_key:
        raise RuntimeError("SECRET_KEY must be set in production.")
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'atlas.sqlite3'}")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    app.config.from_mapping(
        SECRET_KEY=secret_key or secrets.token_urlsafe(32),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "0") == "1",
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    def json_error(message, status=400):
        return jsonify({"error": message}), status

    def csrf_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            token = request.headers.get("X-CSRF-Token")
            if not token or not secrets.compare_digest(token, session.get("csrf_token", "")):
                return json_error("Invalid CSRF token.", 403)
            return view(*args, **kwargs)
        return wrapped

    def auth_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return json_error("Authentication required.", 401)
            return view(*args, **kwargs)
        return wrapped

    def validate_student(payload):
        if not isinstance(payload, dict):
            raise ValueError("Student data must be an object.")
        student_id = str(payload.get("id", "")).strip()
        name = str(payload.get("name", "")).strip()
        course = str(payload.get("course", "")).strip()
        age = payload.get("age")
        attendance = payload.get("attendance", 100)
        marks = payload.get("marks") or {}
        if not student_id.isdigit() or len(student_id) > 32:
            raise ValueError("Student ID must be numeric and no longer than 32 digits.")
        if not name or len(name) > 120 or not course or len(course) > 120:
            raise ValueError("Name and course are required and must be under 120 characters.")
        try:
            age = int(age)
            attendance = float(attendance)
            math = float(marks.get("Math"))
            science = float(marks.get("Science"))
            english = float(marks.get("English"))
        except (TypeError, ValueError):
            raise ValueError("Age, attendance, and marks must be numeric.") from None
        if not 0 <= age <= 120 or any(not 0 <= value <= 100 for value in (attendance, math, science, english)):
            raise ValueError("Age must be 0-120 and attendance and marks must be 0-100.")
        return {"student_id": student_id, "name": name, "age": age, "course": course, "attendance": attendance, "math": math, "science": science, "english": english}

    @app.get("/")
    def index():
        return send_from_directory(BASE_DIR, "index.html")

    @app.get("/<path:filename>")
    def public_file(filename):
        allowed_files = {"index.html", "app-api.js", "manifest.json", "sw.js", "icon.svg"}
        if filename not in allowed_files:
            return json_error("Not found.", 404)
        return send_from_directory(BASE_DIR, filename)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/auth/csrf")
    def csrf():
        session.setdefault("csrf_token", secrets.token_urlsafe(32))
        return jsonify({"csrf_token": session["csrf_token"]})

    @app.get("/api/auth/me")
    def me():
        if not current_user.is_authenticated:
            return jsonify({"authenticated": False})
        return jsonify({"authenticated": True, "user": {"id": current_user.id, "name": current_user.name, "email": current_user.email}})

    @app.post("/api/auth/register")
    @csrf_required
    def register():
        payload = request.get_json(silent=True) or {}
        name = str(payload.get("name", "")).strip()
        email = str(payload.get("email", "")).strip().lower()
        password = str(payload.get("password", ""))
        if len(name) < 2 or len(name) > 120 or "@" not in email or len(password) < 10:
            return json_error("Use a valid name, email, and password of at least 10 characters.")
        if User.query.filter_by(email=email).first():
            return json_error("An account with that email already exists.", 409)
        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return jsonify({"authenticated": True, "user": {"id": user.id, "name": user.name, "email": user.email}}), 201

    @app.post("/api/auth/login")
    @csrf_required
    def login():
        payload = request.get_json(silent=True) or {}
        email = str(payload.get("email", "")).strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(str(payload.get("password", ""))):
            return json_error("Email or password is incorrect.", 401)
        login_user(user)
        return jsonify({"authenticated": True, "user": {"id": user.id, "name": user.name, "email": user.email}})

    @app.post("/api/auth/logout")
    @auth_required
    @csrf_required
    def logout():
        logout_user()
        return jsonify({"authenticated": False})

    @app.get("/api/students")
    @auth_required
    def students():
        records = Student.query.filter_by(owner_id=current_user.id).all()
        return jsonify({"students": {record.student_id: record.to_dict() for record in records}})

    @app.post("/api/students")
    @auth_required
    @csrf_required
    def create_student():
        try:
            data = validate_student(request.get_json(silent=True))
        except ValueError as error:
            return json_error(str(error))
        if Student.query.filter_by(owner_id=current_user.id, student_id=data["student_id"]).first():
            return json_error("That student ID is already in use.", 409)
        record = Student(owner_id=current_user.id, **data)
        db.session.add(record)
        db.session.commit()
        return jsonify(record.to_dict()), 201

    @app.put("/api/students/<student_id>")
    @auth_required
    @csrf_required
    def update_student(student_id):
        record = Student.query.filter_by(owner_id=current_user.id, student_id=student_id).first()
        if not record:
            return json_error("Student not found.", 404)
        try:
            data = validate_student({**(request.get_json(silent=True) or {}), "id": student_id})
        except ValueError as error:
            return json_error(str(error))
        for key, value in data.items():
            if key != "student_id":
                setattr(record, key, value)
        db.session.commit()
        return jsonify(record.to_dict())

    @app.delete("/api/students/<student_id>")
    @auth_required
    @csrf_required
    def delete_student(student_id):
        record = Student.query.filter_by(owner_id=current_user.id, student_id=student_id).first()
        if not record:
            return json_error("Student not found.", 404)
        db.session.delete(record)
        db.session.commit()
        return jsonify({"deleted": True})

    @app.post("/api/students/import")
    @auth_required
    @csrf_required
    def import_students():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return json_error("Import data must be an object keyed by student ID.")
        records = []
        try:
            for student_id, student in payload.items():
                records.append(validate_student({**student, "id": student_id}))
        except (TypeError, ValueError) as error:
            db.session.rollback()
            return json_error(str(error))
        ids = [record["student_id"] for record in records]
        if len(ids) != len(set(ids)):
            return json_error("Import contains duplicate student IDs.")
        Student.query.filter_by(owner_id=current_user.id).delete()
        db.session.add_all([Student(owner_id=current_user.id, **record) for record in records])
        db.session.commit()
        return jsonify({"imported": len(records)})

    @app.get("/api/students/export")
    @auth_required
    def export_students():
        records = Student.query.filter_by(owner_id=current_user.id).all()
        return jsonify({record.student_id: record.to_dict() for record in records})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")

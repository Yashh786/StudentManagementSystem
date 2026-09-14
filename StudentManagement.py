import json
from pathlib import Path


DATA_FILE = Path(__file__).with_name("students_data.json")


def load_data(filename=DATA_FILE):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


students_dict = load_data()


def add_student(student_id, name, age, course, m_marks, s_marks, e_marks, attendance=100):
    if not str(student_id).isdigit():
        raise ValueError("Student ID must be numeric.")
    if not name.strip() or not course.strip():
        raise ValueError("Name and course are required.")
    if age < 0:
        raise ValueError("Age must be non-negative.")
    marks = (m_marks, s_marks, e_marks)
    if any(mark < 0 or mark > 100 for mark in marks):
        raise ValueError("Marks must be between 0 and 100.")
    if attendance < 0 or attendance > 100:
        raise ValueError("Attendance must be between 0 and 100.")
    students_dict[str(student_id)] = {
        "name": name.strip(),
        "age": age,
        "course": course.strip(),
        "attendance": attendance,
        "marks": {"Math": m_marks, "Science": s_marks, "English": e_marks},
    }


def view_student(student_id):
    return students_dict.get(str(student_id))


def see_marks(student_id):
    student = view_student(student_id)
    return student.get("marks") if student else None


def calc_avg(m_marks, s_marks, e_marks):
    return (m_marks + s_marks + e_marks) / 3


def assign_grades(average):
    if average < 0 or average > 100:
        raise ValueError("Average marks should be between 0 and 100.")
    if average >= 90:
        return "A"
    if average >= 75:
        return "B"
    if average >= 60:
        return "C"
    return "Fail"


def top_performer():
    if not students_dict:
        return None
    student_id, details = max(
        students_dict.items(),
        key=lambda item: calc_avg(*item[1]["marks"].values()),
    )
    average = calc_avg(*details["marks"].values())
    return student_id, details["name"], average


def _read_mark(subject):
    while True:
        try:
            mark = int(input(f"Enter {subject} Marks: "))
            if 0 <= mark <= 100:
                return mark
        except ValueError:
            pass
        print("Marks should be numeric and between 0 and 100.")


def run_cli():
    print("Welcome to the Student Management System")
    while True:
        choice = input(
            "\n1 Add student\n2 View student\n3 See marks\n4 View all students\n"
            "5 Calculate average\n6 Assign grade\n7 Top performer\n8 Attendance watchlist\n9 Exit\nChoose: "
        ).strip()
        if choice == "1":
            try:
                student_id = input("Enter Student ID: ").strip()
                name = input("Enter Student Name: ")
                age = int(input("Enter Student Age: "))
                course = input("Enter Student Course: ")
                marks = [_read_mark(subject) for subject in ("Math", "Science", "English")]
                attendance = _read_mark("Attendance percentage")
                add_student(student_id, name, age, course, *marks, attendance)
                save_data(DATA_FILE, students_dict)
                print("Student saved successfully.")
            except ValueError as error:
                print(f"Unable to save student: {error}")
        elif choice in {"2", "3", "5", "6"}:
            student_id = input("Enter Student ID: ").strip()
            student = view_student(student_id)
            if not student:
                print("Student not found.")
                continue
            marks = student["marks"]
            if choice == "2":
                attendance = student.get("attendance", 100)
                print(f"{student['name']} | Age {student['age']} | {student['course']} | Attendance {attendance}%")
            elif choice == "3":
                print(" | ".join(f"{subject}: {mark}" for subject, mark in marks.items()))
            else:
                average = calc_avg(*marks.values())
                print(f"Average: {average:.2f} | Grade: {assign_grades(average)}")
        elif choice == "4":
            for student_id, student in students_dict.items():
                print(f"#{student_id} {student['name']} | {student['course']}")
        elif choice == "7":
            result = top_performer()
            print(f"Top performer: {result[1]} (#{result[0]}) | {result[2]:.2f}") if result else print("No students found.")
        elif choice == "8":
            watchlist = [
                (student_id, student)
                for student_id, student in students_dict.items()
                if student.get("attendance", 100) < 75
            ]
            if watchlist:
                for student_id, student in watchlist:
                    print(f"#{student_id} {student['name']} | Attendance {student.get('attendance', 100)}%")
            else:
                print("No students currently need attendance support.")
        elif choice == "9":
            save_data(DATA_FILE, students_dict)
            print("Data saved. Goodbye.")
            break
        else:
            print("Please choose a number from 1 to 9.")


if __name__ == "__main__":
    run_cli()
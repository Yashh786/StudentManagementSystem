import json


def load_data(filename):
    try:
        with open(filename,"r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("No previous data found. Starting fresh.")
        return {}
    
students_dict = load_data("students_data.json")

def save_data(filename, data):
    with open(filename,"w") as file:
        json.dump(data,file,indent=4)




def add_student(student_id, name, age, course,m_marks, s_marks, e_marks):
    students_dict[student_id] = {
        "name": name,
        "age": age,
        "course": course,
        "marks" : {
            "Math": m_marks,
            "Science": s_marks,
            "English": e_marks  
        }
    }
    print(f"Student {name} added successfully.")

def view_student(student_id):
        students = students_dict.get(student_id)
        return students 

def see_marks(student_id):
    students = students_dict.get(student_id)
    return students 

def calc_avg(m_marks,s_marks,e_marks):
    avg = float(m_marks + s_marks + e_marks)/3
    return avg

def assign_grades(average):
    if average>100 or average<0:
        raise ValueError("Average marks should be between 0 and 100.")
    if average >=90:
        return "A"
    elif average>=75:
        return "B"
    elif average>=60:
        return "C"
    else:
        return "Fail"
    
def top_performer():
    if students_dict:
        top_student = None
        highest_avg = -1
        for sid,details in students_dict.items():
            marks = details["marks"]
            avg = calc_avg(marks["Math"],marks["Science"],marks["English"])
            if avg > highest_avg:
                highest_avg = avg
                top_student = (sid, details["name"], avg)
        return top_student
    else:
        return None

    

print("Welcome to the Student Management System")
flag = True
while flag==True:
    choice = input("Enter Your Choice:\n"
    "1 = Add Student\n"
    "2 = View Student\n"
    "3 = See Marks\n"
    "4 = View All Students\n"
    "5 = Calculate Average Marks\n"
    "6 = Assign Grades\n"
    "7 = Top Performer\n"
    "8 = Exit\n")
    if choice == "1":
        sid = input("Enter Student ID:")
        if sid.isdigit():
            name = input("Enter Student Name: ")
            try:
                age = int(input("Enter Student Age: "))
                if age>=0:
                    age=int(age)
                else:
                    print("Invalid Age. Please enter a non-negative numeric value.")
                    continue
            except ValueError:
                print("Invalid Age. Please enter a numeric value.")
                continue
            course = input("Enter Student Course: ")

            while True:
                try:
                    m_marks = int(input("Enter Math Marks: "))
                    if 0<=m_marks<=100: 
                        break
                    else:
                        print("Invalid Marks. Please enter marks between 0 and 100.")
                except ValueError:
                    print("Marks should be numeric!")
            while True:       
                try:
                    s_marks = int(input("Enter Science Marks: "))
                    if 0<=s_marks<=100: 
                        break
                    else:
                        print("Invalid Marks. Please enter marks between 0 and 100.")
                except ValueError:
                    print("Marks should be numeric!")
            while True:       
                try:
                    e_marks = int(input("Enter English Marks: "))
                    if 0<=e_marks<=100: 
                        break
                    else:
                        print("Invalid Marks. Please enter marks between 0 and 100.")
                except ValueError:
                    print("Marks should be numeric!")
        else :
            print("Invalid ID. Please enter a numeric value.")
            continue
        add_student(sid,name,age,course,m_marks,s_marks,e_marks)
    
    elif choice == "2":
        if students_dict:
            sid = input("Enter Student ID to view details: ")
            details = view_student(sid)
            if details:
                print(f"Student ID: {sid}")
                print(f"Name: {details['name']}")
                print(f"Age: {details['age']}")
                print(f"Course: {details['course']}")
            else:
                print("Student not found.")
        else:
            print("No students found.")


    elif choice == "3":
        sid  = input("Enter Student ID to see marks: ")
        details = see_marks(sid)
        if details:
            print(f"Marks for Student ID: {sid}")
            print(f"Math: {details['marks']['Math']}")
            print(f"Science: {details['marks']['Science']}")
            print(f"English: {details['marks']['English']}")  
        else:
            print("Student not found.")

    elif choice == "4":
        if students_dict:
            for sid, details in students_dict.items():
                print(f"Student ID: {sid}, Name: {details['name']}, Age: {details['age']}, Course: {details['course']}")
        else:
            print("No students found.")

    elif choice == "5":
        if students_dict=={}:
            print("No students found.")
            
        else:
            sid = input('Enter Student ID to calculate average marks: ')
            details = see_marks(sid)
            if details:
                m_marks = details["marks"]["Math"]
                s_marks = details["marks"]["Science"]
                e_marks = details["marks"]["English"]  
                average = calc_avg(m_marks,s_marks,e_marks)
                print(f"Average Marks for Student ID {sid}: {average:.2f}")
            else:
                print("Student not found.")

    elif choice == "6":
        if students_dict:
            sid = input("Enter Student ID to assign Grade: ")
            details = see_marks(sid)
            if details:
                m_marks = details["marks"]["Math"]
                s_marks = details["marks"]["Science"]
                e_marks = details["marks"]["English"]
                average = calc_avg(m_marks,s_marks,e_marks)
                try:
                    grade =  assign_grades(average)
                    print(f"The Average for student ID {sid} is: {average:.2f} with Grade {grade}")
                except ValueError as ve:
                    print(ve)
        else:
            print("No students found.")


    elif choice == "7":
        top_student = top_performer()
        if top_student:
            sid,name,avg = top_student
            print(f"Top Performer is Student ID: {sid}, Name: {name}, with Average Marks: {avg:.2f}")
        else:
            print("No students found.")

    elif choice == "8":
         save_data("students_data.json",students_dict)
         flag = False
         print("Bye Bye!")

    else:
        print("Please enter a valid choice.")   

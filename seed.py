from app import db, app
from app.models import Student, Finance, Teacher, User, Country, StudentIDCounter, Enrollment
from faker import Faker
from datetime import datetime

fake = Faker()

def reset_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset successfully.")

def seed_countries():
    countries = [
        {'name': 'Kenya', 'code': 'KE'},
        {'name': 'United States', 'code': 'US'},
        {'name': 'United Kingdom', 'code': 'GB'},
        {'name': 'Canada', 'code': 'CA'},
        {'name': 'Australia', 'code': 'AU'},
        {'name': 'India', 'code': 'IN'},
        {'name': 'Germany', 'code': 'DE'},
        {'name': 'France', 'code': 'FR'},
        {'name': 'South Africa', 'code': 'ZA'},
        {'name': 'Nigeria', 'code': 'NG'},
        {'name': 'Japan', 'code': 'JP'},
        {'name': 'China', 'code': 'CN'},
        {'name': 'Brazil', 'code': 'BR'},
        {'name': 'Mexico', 'code': 'MX'},
        {'name': 'Argentina', 'code': 'AR'},
    ]
    
    for country in countries:
        new_country = Country(name=country['name'], code=country['code'])
        db.session.add(new_country)

    db.session.commit()
    print("Countries seeded successfully.")

def seed_users():
    users = [
        User(
            email=fake.email(),
            username=fake.user_name(),
            role="admin"
        ),
        User(
            email=fake.email(),
            username=fake.user_name(),
            role="teacher"
        ),
        User(
            email=fake.email(),
            username=fake.user_name(),
            role="teacher"
        ),
        User(
            email=fake.email(),
            username=fake.user_name(),
            role="student"
        ),
        User(
            email=fake.email(),
            username=fake.user_name(),
            role="student"
        )
    ]
    
    for user in users:
        user.password = "defaultpassword"  

    db.session.add_all(users)
    db.session.commit()
    print("Users seeded successfully.")

def seed_teachers():
    teacher_users = User.query.filter_by(role="teacher").all()
    
    teachers = []
    subjects = ["Mathematics", "Science", "Kiswahili", "History", "Geography", "English", "Physical Education"]

    for user in teacher_users:
        teacher = Teacher(
            name=fake.name(),
            subject=fake.random_element(subjects),
            hire_date=datetime.now(),
            user_id=user.id
        )
        teachers.append(teacher)

    db.session.add_all(teachers)
    db.session.commit()
    print("Teachers seeded successfully.")

def seed_students():
    student_users = User.query.filter_by(role="student").all()
    assigned_user_ids = {student.user_id for student in Student.query.all()}
    
    available_student_users = [user for user in student_users if user.id not in assigned_user_ids]
    
    countries = Country.query.all()
    teachers = Teacher.query.all()
    students = []
    
    for i, user in enumerate(available_student_users, start=1):
        country = fake.random_element(countries)
        teacher = fake.random_element(teachers)

        student = Student(
            name=fake.name(),
            phone_number=fake.phone_number(),
            email=user.email,
            student_id=Student.generate_student_id(country.code, i),
            enrolled_date=datetime.now(),
            country_id=country.id,
            user_id=user.id,
            teacher_id=teacher.id
        )
        
        students.append(student)

    db.session.add_all(students)
    db.session.commit()
    print("Students seeded successfully.")

def seed_finance():
    students = Student.query.all() 
    users = User.query.filter_by(role="admin").all()  
    
    transaction_types = ['tuition', 'maintanance', 'fee']  
    finances = []

    for student in students:
        for _ in range(fake.random_int(min=1, max=3)): 
            finance_record = Finance(
                student_id=student.id,
                user_id=fake.random_element(users).id, 
                amount=fake.random_number(digits=4), 
                transaction_type=fake.random_element(transaction_types),  
                date=fake.date_time_this_year(),  
                description=fake.sentence(nb_words=6)  
            )
            finances.append(finance_record)

    db.session.add_all(finances)
    db.session.commit()
    print("Finance records seeded successfully.")
def seed_student_id_counters():
    countries = Country.query.all() 

    student_id_counters = []
    for country in countries:
        student_id_counter = StudentIDCounter(
            country_id=country.id,
            count=0  
        )
        student_id_counters.append(student_id_counter)

    db.session.add_all(student_id_counters)
    db.session.commit()
    print("Student ID Counters seeded successfully.")

def seed_enrollments():
    with app.app_context():
        students = Student.query.all()  
        courses_list = ["Math", "Science", "History", "English", "Geography", "Art"]

        enrollments = []

        for student in students:
            for _ in range(fake.random_int(min=1, max=3)):
                courses = ", ".join(fake.random_elements(courses_list, unique=True, length=fake.random_int(min=1, max=3)))
                enrollment = Enrollment(
                    student_id=student.id,
                    courses=courses,
                    phone_number=student.phone_number,  
                    enrollment_date=fake.date_time_this_year() 
                )
                enrollments.append(enrollment)

        db.session.add_all(enrollments)
        db.session.commit()
        print("enrollments seeded successfully.")

if __name__ == "__main__":
    with app.app_context():
        reset_database()
        seed_countries()
        seed_users()
        seed_teachers()
        seed_students()
        seed_finance()
        seed_student_id_counters() 
        seed_enrollments()
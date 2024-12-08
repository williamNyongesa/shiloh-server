from app import db, app
from app.models import Student, Finance, Teacher, User, Country, StudentIDCounter, Enrollment, Quiz, Question
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
    users_data = [
        {"email": fake.email(), "username": fake.user_name(), "role": "admin"},
        {"email": fake.email(), "username": fake.user_name(), "role": "teacher"},
        {"email": fake.email(), "username": fake.user_name(), "role": "teacher"},
        {"email": fake.email(), "username": fake.user_name(), "role": "student"},
        {"email": fake.email(), "username": fake.user_name(), "role": "student"}
    ]

    for data in users_data:
        # Check if a user with the same email already exists
        existing_user = User.query.filter_by(email=data["email"]).first()
        
        if existing_user is None:
            new_user = User(
                email=data["email"],
                username=data["username"],
                role=data["role"],
                password="defaultpassword"  # Ensure all users get a default password
            )
            db.session.add(new_user)

    db.session.commit()
    print("Users seeded successfully.")

def seed_teachers():
    teacher_users = User.query.filter_by(role="teacher").all()

    teachers = []
    subjects = ["Mathematics", "Science", "Kiswahili", "History", "Geography", "English", "Physical Education"]

    for user in teacher_users:
        # Check if the teacher with the same user_id already exists
        existing_teacher = Teacher.query.filter_by(user_id=user.id).first()

        if existing_teacher is None:
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

        student_id = Student.generate_student_id(country.code, i)[:15]  # Ensure student_id fits within 15 chars
        phone_number = fake.phone_number()[:15]  # Truncate phone number to 15 characters max
        name = fake.name()[:50]  # Truncate name if longer than 50 characters
        email = user.email[:100]  # Truncate email if longer than 100 characters

        # Check if the student already exists in the database
        existing_student = Student.query.filter_by(user_id=user.id).first()
        
        if existing_student is None:
            student = Student(
                name=name,
                phone_number=phone_number,
                email=email,
                student_id=student_id,
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
        # Check if counter already exists for the country
        existing_counter = StudentIDCounter.query.filter_by(country_id=country.id).first()
        
        if existing_counter is None:
            student_id_counter = StudentIDCounter(
                country_id=country.id,
                count=0  # Initializing counter
            )
            student_id_counters.append(student_id_counter)

    db.session.add_all(student_id_counters)
    db.session.commit()
    print("Student ID Counters seeded successfully.")

def seed_enrollments():
    students = Student.query.all()
    courses_list = ["Math", "Science", "History", "English", "Geography", "Art"]
    
    enrollments = []
    
    for student in students:
        for _ in range(fake.random_int(min=1, max=3)):
            courses = ", ".join(fake.random_elements(courses_list, unique=True, length=fake.random_int(min=1, max=3)))
            
            # Check if the student is already enrolled in these courses
            existing_enrollment = Enrollment.query.filter_by(student_id=student.id, courses=courses).first()
            
            if existing_enrollment is None:
                enrollment = Enrollment(
                    student_id=student.id,
                    courses=courses,
                    phone_number=student.phone_number,
                    enrollment_date=fake.date_time_this_year()
                )
                enrollments.append(enrollment)

    db.session.add_all(enrollments)
    db.session.commit()
    print("Enrollments seeded successfully.")

# Seed quizzes
def seed_quizzes():
    quizzes_data = [
        {'title': 'Math Quiz', 'questions': [
            {'text': 'What is 2 + 2?', 'options': '3,4,5,6', 'correct_answer': '4'},
            {'text': 'What is 3 + 5?', 'options': '7,8,9,10', 'correct_answer': '8'}
        ]},
        {'title': 'Science Quiz', 'questions': [
            {'text': 'What is the chemical symbol for water?', 'options': 'H2O,O2,CO2,H2O2', 'correct_answer': 'H2O'},
            {'text': 'What planet is closest to the Sun?', 'options': 'Earth,Venus,Mars,Mercury', 'correct_answer': 'Mercury'}
        ]},
        {'title': 'History Quiz', 'questions': [
            {'text': 'Who was the first president of the United States?', 'options': 'Abraham Lincoln,George Washington,Thomas Jefferson,Theodore Roosevelt', 'correct_answer': 'George Washington'},
            {'text': 'In which year did World War II end?', 'options': '1940,1945,1950,1955', 'correct_answer': '1945'}
        ]}
    ]

    for quiz_data in quizzes_data:
        # Create a new quiz
        quiz = Quiz(title=quiz_data['title'])
        db.session.add(quiz)
        db.session.commit()  # Commit to get the quiz ID for associating questions

        for question_data in quiz_data['questions']:
            question = Question(
                text=question_data['text'],
                options=question_data['options'],
                correct_answer=question_data['correct_answer'],
                quiz_id=quiz.id  # Link question to the quiz
            )
            db.session.add(question)
        
        db.session.commit()

    print("Quizzes seeded successfully.")

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
        seed_quizzes()
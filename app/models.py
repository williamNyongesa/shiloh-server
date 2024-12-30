import base64
from app import db, bcrypt
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from flask_mail import Mail, Message

# Student Model
class Student(db.Model, SerializerMixin):
    __tablename__ = 'students'
    serialize_rules = ('-country', '-user', '-teacher', '-finances', '-first_name', '-middle_name', '-last_name')

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Basic information fields
    name = db.Column(db.String(100), nullable=True)
    first_name = db.Column(db.String(100), nullable=True)
    middle_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(15), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)

    # Enrollment date, defaults to the current UTC datetime
    enrolled_date = db.Column(db.DateTime, default=func.now())

    # Foreign key to Country model
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    country = db.relationship('Country', back_populates='students')

    # Foreign key to User model
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    user = db.relationship('User', backref='student', uselist=False)

    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)  
    teacher = db.relationship('Teacher', back_populates='students')

    # Relationship with Finance model
    finances = db.relationship('Finance', back_populates='student')
    enrollments = db.relationship('Enrollment', back_populates='student', cascade='all, delete-orphan')

    # Static method to generate unique student ID
    @staticmethod
    def generate_student_id(country_code, count):
        """Generates a student ID using the country code and student count."""
        return f"{country_code}{str(count).zfill(3)}"

    # Class method to create a student with a unique ID
    @classmethod
    def create_with_unique_id(cls, first_name, middle_name, last_name, phone_number, email, country_name, password):
        """Create a student with a unique ID based on the country."""
            # List all available countries for debugging or selection
        available_countries = Country.query.all()
        country_names = [country.name for country in available_countries]
        country_name = country_name.strip().lower()

        # Fetch the country (using ilike for case-insensitive search and normalize input)
        country = Country.query.filter(Country.name.ilike(country_name)).first()  # 'ilike' for case-insensitive search
        
        # Debugging: log the query result
        if country:
            print(f"Found country: {country.name}")
        else:
            print(f"Country not found for: {country_name}")
        if not country:
            # Provide the list of available countries if the selected country is not found
            raise ValueError(f"Invalid country name provided. Available countries are: {', '.join(country_names)}")
            
        # Create or update the student ID counter
        counter = StudentIDCounter.query.filter_by(country_id=country.id).first()
        if not counter:
            counter = StudentIDCounter(country_id=country.id, count=1)
            db.session.add(counter)
        else:
            counter.count += 1

        # Commit the transaction to update the counter
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Failed to generate a unique student ID.")

        # Generate the student ID
        student_id = cls.generate_student_id(country.code, counter.count)

        # Create a new User object for the student (responsible for password)
        user = User(
            email=email,
            username=email.split('@')[0],  # Use the part before the '@' as username, or customize as needed
            password=password,  # Set the password securely (bcrypt will hash it)
            role='student'  # Set a default role for students
        )
        print(user)
        # Add the user to the session
        db.session.add(user)
        db.session.commit()  # Commit to get the user_id for the student

        # Create a new Student instance
        new_student = cls(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            name=f"{first_name} {last_name}",  # Set 'name' by combining first and last name
            phone_number=phone_number,
            email=email,
            student_id=student_id,
            country=country,
            user=user  # Associate this student with the user
        )

        db.session.add(new_student)
        db.session.commit()

        return new_student
    
    def to_dict(self):
        """Convert the Student object to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'first_name': self.first_name,
            'middle_name': self.middle_name,
            'last_name': self.last_name,
            'phone_number': self.phone_number,
            'email': self.email,
            'student_id': self.student_id,
            'enrolled_date': self.enrolled_date.isoformat() if self.enrolled_date else None,
            'country': self.country.name if self.country else None,
            'user_id': self.user_id,
            'teacher_id': self.teacher_id,
            'teacher': self.teacher.name if self.teacher else None,  # Assuming teacher has a 'name' attribute
            'finances': [finance.to_dict() for finance in self.finances],  # Assuming 'to_dict()' exists on Finance model
            'enrollments': [enrollment.to_dict() for enrollment in self.enrollments]  # Assuming 'to_dict()' exists on Enrollment model
        }


# Country Model
class Country(db.Model, SerializerMixin):
    __tablename__ = 'countries'
    serialize_rules = ('-students',)  # Serialization rules to avoid circular references

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Name and country code
    name = db.Column(db.String(50), unique=True, nullable=False)
    code = db.Column(db.String(2), unique=True, nullable=False)  # KE, US, etc.

    # Relationship with Student model
    students = db.relationship('Student', back_populates='country')

    def __repr__(self):
        return f"<Country {self.name} ({self.code})>"

# StudentIDCounter Model
class StudentIDCounter(db.Model, SerializerMixin):
    __tablename__ = 'student_id_counters'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Country ID and count of students for unique ID generation
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False, unique=True)
    count = db.Column(db.Integer, default=0, nullable=False)

    # Relationship with Country model
    country = db.relationship('Country')

    def __repr__(self):
        return f"<StudentIDCounter {self.country.code} - {self.count}>"

# User Model
class User(db.Model):
    __tablename__ = 'users'
    
    serialize_rules = ('-_password',)

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    _password = db.Column('password', db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    user_profile_picture = db.Column(db.LargeBinary)

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute.")

    @password.setter
    def password(self, password):
        # Hash password securely using bcrypt
        self._password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        # Use bcrypt's check_password_hash directly to compare the hashes
        return bcrypt.check_password_hash(self._password, password)
    
    def generate_password_hash(self, password):
        # This method is not necessary for checking the password, but it's fine to keep for future use
        return bcrypt.generate_password_hash(password).decode('utf-8')

    def __repr__(self):
        return f'<User {self.username}>'

    def __str__(self):
        return f'{self.username} - {self.role}'

    def to_dict(self):
        user_data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'role': self.role
        }
        
        # Convert the profile picture to base64 string for easy use on the front-end
        if self.user_profile_picture:
            user_data['profile_picture'] = base64.b64encode(self.user_profile_picture).decode('utf-8')
        else:
            user_data['profile_picture'] = None

        return user_data
# Teacher Model
class Teacher(db.Model, SerializerMixin):
    __tablename__ = 'teachers'
    serialize_rules = ('-user', '-students')  # Serialization rules to avoid circular references

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Teacher's name, subject expertise, and hire date
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    hire_date = db.Column(db.DateTime, default=func.now())

    # Foreign key to User model (one-to-one relationship)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    user = db.relationship('User', backref='teacher', uselist=False)

    # Relationship with Student model (one-to-many relationship)
    students = db.relationship('Student', back_populates='teacher')  # back_populates links with Student model


    def __repr__(self):
        return f'<Teacher {self.name} - {self.subject}>'

# Finance Model
class Finance(db.Model, SerializerMixin):
    __tablename__ = 'finances'
    serialize_rules = ('-student', '-user')  # Serialization rules to avoid circular references

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign key to Student model
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    student = db.relationship('Student', back_populates='finances')

    # Foreign key to User model (optional, if you want to track who handled the finance record)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='finances')

    # Financial details
    amount = db.Column(db.Float, nullable=False)  # Amount of the transaction
    transaction_type = db.Column(db.String(50), nullable=False)  # e.g., 'tuition', 'payment', 'fee'
    date = db.Column(db.DateTime, default=func.now())  # Date of the transaction
    description = db.Column(db.String(255))  # Optional description for the transaction

    def __repr__(self):
        return f'<Finance Record: {self.transaction_type} - Amount: {self.amount} for Student ID: {self.student_id}>'

# Enrollment Model
class Enrollment(db.Model, SerializerMixin):
    __tablename__ = 'enrollments'
    serialize_rules = ('-student',)  # Avoid circular references during serialization

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign key to the Student model
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    student = db.relationship('Student', back_populates='enrollments')

    # Attributes
    courses = db.Column(db.String(255), nullable=False)  # e.g., "Math, Science, History"
    phone_number = db.Column(db.String(15), nullable=False)  # Phone number of the student
    enrollment_date = db.Column(db.DateTime, default=func.now())  # Defaults to current datetime
    document_file = db.Column(db.LargeBinary)  # BYTEA or LargeBinary

    def __repr__(self):
        return f'<Enrollment {self.courses} for Student ID {self.student_id}>'
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'courses': self.courses,
            'phone_number': self.phone_number,
            'enrollment_date': self.enrollment_date.isoformat(),
        }

class Quiz(db.Model):
    __tablename__ = 'quizzes'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)

    # One-to-many relationship with Question model
    questions = db.relationship('Question', backref='quiz', lazy=True)

    def __repr__(self):
        return f'<Quiz {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'questions': [{'id': q.id, 'text': q.text, 'options': q.options.split(', ')} for q in self.questions]
        }

class Question(db.Model):
    __tablename__ = 'questions'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Question attributes
    text = db.Column(db.String(255), nullable=False)  # The question text
    options = db.Column(db.String(255), nullable=False)  # Store options as a comma-separated string
    correct_answer = db.Column(db.String(255), nullable=True)  # The correct answer
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)  # Foreign key to Quiz

    def __repr__(self):
        return f'<Question {self.text}>'
    
class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    time = db.Column(db.String(50))
    location = db.Column(db.String(255))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date.isoformat(),  # Format the date to string
            "description": self.description,
            "time": self.time,
            "location": self.location
        }

class FileUpload(db.Model):
    __tablename__ = 'file_uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)  # Store the original filename
    file_type = db.Column(db.String(50), nullable=False)  # Store the file type (e.g., 'csv', 'xlsx')
    file_data = db.Column(db.LargeBinary, nullable=False)  # Store the actual file data as binary
    upload_time = db.Column(db.DateTime, default=lambda: datetime.now(datetime.timezone.utc))  # Store the upload timestamp
    
    def __init__(self, filename, file_type, file_data):
        self.filename = filename
        self.file_type = file_type
        self.file_data = file_data
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'file_type': self.file_type,
            'upload_time': self.upload_time
        }

class Invoice(db.Model, SerializerMixin):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='unpaid')
    student = db.relationship('Student', backref='invoices')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'amount': self.amount,
            'due_date': self.due_date.isoformat(),
            'status': self.status
        }

class Payment(db.Model, SerializerMixin):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    invoice = db.relationship('Invoice', backref='payments')

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'amount': self.amount,
            'payment_date': self.payment_date.isoformat()
        }

class ClassSchedule(db.Model, SerializerMixin):
    __tablename__ = 'class_schedules'
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(100), nullable=False)
    room_number = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'class_name': self.class_name,
            'room_number': self.room_number,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat()
        }

class Notification(db.Model, SerializerMixin):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'subject': self.subject,
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }

class Grade(db.Model, SerializerMixin):
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course = db.Column(db.String(255), nullable=False)
    grade = db.Column(db.String(10), nullable=False)
    date_recorded = db.Column(db.DateTime, default=func.now())

    student = db.relationship('Student', backref='grades')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'course': self.course,
            'grade': self.grade,
            'date_recorded': self.date_recorded.isoformat()
        }

# Helper functions for communication tools
def send_email(recipient, message):
    mail = Mail()
    msg = Message(
        subject="Notification",
        sender="noreply@shilohproject.com",
        recipients=[recipient]
    )
    msg.body = message
    mail.send(msg)

def send_sms(recipient, message):
    # Implement SMS sending logic here
    pass

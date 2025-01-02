import base64
from app import db, bcrypt
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Table, func
from flask_mail import Mail, Message


class Student(db.Model, SerializerMixin):
    __tablename__ = 'students'
    serialize_rules = ('-country', '-user', '-teacher', '-finances', '-first_name', '-middle_name', '-last_name')

    
    id = db.Column(db.Integer, primary_key=True)

    
    name = db.Column(db.String(100), nullable=True)
    first_name = db.Column(db.String(100), nullable=True)
    middle_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(15), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)

    
    enrolled_date = db.Column(db.DateTime, default=func.now())

    
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    country = db.relationship('Country', back_populates='students')

    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    user = db.relationship('User', backref='student', uselist=False)

    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)  
    teacher = db.relationship('Teacher', back_populates='students')

    
    finances = db.relationship('Finance', back_populates='student')
    enrollments = db.relationship('Enrollment', back_populates='student', cascade='all, delete-orphan')

    
    @staticmethod
    def generate_student_id(country_code, count):
        """Generates a student ID using the country code and student count."""
        return f"{country_code}{str(count).zfill(3)}"

    
    @classmethod
    def create_with_unique_id(cls, first_name, middle_name, last_name, phone_number, email, country_name, password):
        """Create a student with a unique ID based on the country."""
            
        available_countries = Country.query.all()
        country_names = [country.name for country in available_countries]
        country_name = country_name.strip().lower()

        
        country = Country.query.filter(Country.name.ilike(country_name)).first()  
        
        
        if country:
            print(f"Found country: {country.name}")
        else:
            print(f"Country not found for: {country_name}")
        if not country:
            
            raise ValueError(f"Invalid country name provided. Available countries are: {', '.join(country_names)}")
            
        
        counter = StudentIDCounter.query.filter_by(country_id=country.id).first()
        if not counter:
            counter = StudentIDCounter(country_id=country.id, count=1)
            db.session.add(counter)
        else:
            counter.count += 1

        
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Failed to generate a unique student ID.")

        
        student_id = cls.generate_student_id(country.code, counter.count)

        
        user = User(
            email=email,
            username=email.split('@')[0],  
            password=password,  
            role='student'  
        )
        print(user)
        
        db.session.add(user)
        db.session.commit()  

        
        new_student = cls(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            name=f"{first_name} {last_name}",  
            phone_number=phone_number,
            email=email,
            student_id=student_id,
            country=country,
            user=user  
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
            'teacher': self.teacher.name if self.teacher else None,  
            'finances': [finance.to_dict() for finance in self.finances],  
            'enrollments': [enrollment.to_dict() for enrollment in self.enrollments]  
        }



class Country(db.Model, SerializerMixin):
    __tablename__ = 'countries'
    serialize_rules = ('-students',)  

    
    id = db.Column(db.Integer, primary_key=True)

    
    name = db.Column(db.String(50), unique=True, nullable=False)
    code = db.Column(db.String(2), unique=True, nullable=False)  

    
    students = db.relationship('Student', back_populates='country')

    def __repr__(self):
        return f"<Country {self.name} ({self.code})>"


class StudentIDCounter(db.Model, SerializerMixin):
    __tablename__ = 'student_id_counters'

    
    id = db.Column(db.Integer, primary_key=True)

    
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False, unique=True)
    count = db.Column(db.Integer, default=0, nullable=False)

    
    country = db.relationship('Country')

    def __repr__(self):
        return f"<StudentIDCounter {self.country.code} - {self.count}>"


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
        
        self._password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        
        return bcrypt.check_password_hash(self._password, password)
    
    def generate_password_hash(self, password):
        
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
        
        
        if self.user_profile_picture:
            user_data['profile_picture'] = base64.b64encode(self.user_profile_picture).decode('utf-8')
        else:
            user_data['profile_picture'] = None

        return user_data


class Finance(db.Model, SerializerMixin):
    __tablename__ = 'finances'
    serialize_rules = ('-student', '-user')  

    
    id = db.Column(db.Integer, primary_key=True)

    
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    student = db.relationship('Student', back_populates='finances')

    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='finances')

    
    amount = db.Column(db.Float, nullable=False)  
    transaction_type = db.Column(db.String(50), nullable=False)  
    date = db.Column(db.DateTime, default=func.now())  
    description = db.Column(db.String(255))  

    def __repr__(self):
        return f'<Finance Record: {self.transaction_type} - Amount: {self.amount} for Student ID: {self.student_id}>'


class Enrollment(db.Model, SerializerMixin):
    __tablename__ = 'enrollments'
    serialize_rules = ('-student',)  

    
    id = db.Column(db.Integer, primary_key=True)

    
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    student = db.relationship('Student', back_populates='enrollments')
    courses = db.Column(db.String(255), nullable=False) 

    
    teachers = db.relationship(
        'Teacher', 
        secondary='enrollment_teacher_association', 
        back_populates='enrollments'
    )

    
    phone_number = db.Column(db.String(15), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=func.now())
    document_file = db.Column(db.LargeBinary)

    def __repr__(self):
        return f'<Enrollment {self.id} for Student ID {self.student_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'teachers': [teacher.to_dict() for teacher in self.teachers],
            'phone_number': self.phone_number,
            'enrollment_date': self.enrollment_date.isoformat(),
        }


class Quiz(db.Model):
    __tablename__ = 'quizzes'

    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)

    
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

    
    id = db.Column(db.Integer, primary_key=True)

    
    text = db.Column(db.String(255), nullable=False)  
    options = db.Column(db.String(255), nullable=False)  
    correct_answer = db.Column(db.String(255), nullable=True)  
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)  

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
            "date": self.date.isoformat(),  
            "description": self.description,
            "time": self.time,
            "location": self.location
        }

class FileUpload(db.Model):
    __tablename__ = 'file_uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)  
    file_type = db.Column(db.String(50), nullable=False)  
    file_data = db.Column(db.LargeBinary, nullable=False)  
    upload_time = db.Column(db.DateTime, default=func.now())  
    
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

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course = db.Column(db.String(255), nullable=False)  
    date = db.Column(db.Date, default=func.now(), nullable=False)
    status = db.Column(db.String(20), nullable=False)  

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "course": self.course,
            "date": self.date.strftime('%Y-%m-%d'),
            "status": self.status,
        }


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
    
    pass


teacher_course_association = Table(
    'teacher_course_association',
    db.Model.metadata,
    db.Column('teacher_id', db.Integer, db.ForeignKey('teachers.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True)
)


class Course(db.Model, SerializerMixin):
    __tablename__ = 'courses'
    serialize_rules = ('-enrollments', '-teachers')  

    
    id = db.Column(db.Integer, primary_key=True)

    
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))

    
    enrollments = db.relationship('Enrollment', back_populates='course')

    
    teachers = db.relationship(
        'Teacher',
        secondary=teacher_course_association,
        back_populates='courses'
    )

    def __repr__(self):
        return f'<Course {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'teachers': [teacher.to_dict() for teacher in self.teachers],
        }



enrollment_teacher_association = db.Table('enrollment_teacher_association',
    db.Column('enrollment_id', db.Integer, db.ForeignKey('enrollments.id'), primary_key=True),
    db.Column('teacher_id', db.Integer, db.ForeignKey('teachers.id'), primary_key=True)
)

class Enrollment(db.Model, SerializerMixin):
    __tablename__ = 'enrollments'
    __table_args__ = {'extend_existing': True}

    serialize_rules = ('-student',)  

    
    id = db.Column(db.Integer, primary_key=True)

    
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    student = db.relationship('Student', back_populates='enrollments')

    
    teachers = db.relationship(
        'Teacher', 
        secondary=enrollment_teacher_association, 
        back_populates='enrollments'
    )

    
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    course = db.relationship('Course', back_populates='enrollments')

    
    phone_number = db.Column(db.String(15), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=func.now())
    document_file = db.Column(db.LargeBinary)

    def __repr__(self):
        return f'<Enrollment {self.id} for Student ID {self.student_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'teachers': [teacher.to_dict() for teacher in self.teachers],
            'course': self.course.to_dict() if self.course else None,
            'phone_number': self.phone_number,
            'enrollment_date': self.enrollment_date.isoformat(),
        }

class Teacher(db.Model, SerializerMixin):
    __tablename__ = 'teachers'
    serialize_rules = ('-user', '-students', '-courses')  

    
    id = db.Column(db.Integer, primary_key=True)

    
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    hire_date = db.Column(db.DateTime, default=func.now())

    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    user = db.relationship('User', backref='teacher', uselist=False)

    
    students = db.relationship('Student', back_populates='teacher')

    
    enrollments = db.relationship(
        'Enrollment',
        secondary=enrollment_teacher_association,
        back_populates='teachers'
    )

    
    courses = db.relationship(
        'Course',
        secondary=teacher_course_association,
        back_populates='teachers'
    )

    def __repr__(self):
        return f'<Teacher {self.name} - {self.subject}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'hire_date': self.hire_date.isoformat(),
            'courses': [course.to_dict() for course in self.courses],
        }

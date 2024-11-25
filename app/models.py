from app import db, bcrypt
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime
from sqlalchemy.exc import IntegrityError

# Student Model
class Student(db.Model, SerializerMixin):
    __tablename__ = 'students'
    serialize_rules = ('-country', '-user', '-teacher', '-finances') 

    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic information fields
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    
    # Enrollment date, defaults to the current datetime
    enrolled_date = db.Column(db.DateTime, default=datetime.now())
    
    # Foreign key to Country model
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    country = db.relationship('Country', back_populates='students')

    # Foreign key to User model
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))

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
    def create_with_unique_id(cls, name, phone_number, email, country_name):
        """Create a student with a unique ID based on the country."""
        country = Country.query.filter_by(name=country_name).first()
        if not country:
            raise ValueError("Invalid country name provided.")
        
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
        new_student = cls(
            name=name,
            phone_number=phone_number,
            email=email,
            student_id=student_id,
            country=country
        )
        db.session.add(new_student)
        db.session.commit()
        
        return new_student

    def __repr__(self):
        return f'<Student {self.name}, {self.student_id}>'

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
class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    serialize_rules = ('-_password',)  # Serialization rule to hide password

    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Email and username
    email = db.Column(db.String(50), nullable=False, unique=True)
    username = db.Column(db.String(50), nullable=False)
    
    # Password (stored hashed) and user role
    _password = db.Column('password', db.String(255), nullable=True)
    role = db.Column(db.String(50), nullable=False)

    # Password property for secure handling
    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute.")

    @password.setter
    def password(self, password):
        """Hashes the password and stores it."""
        self._password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Checks a password against the stored hash."""
        return bcrypt.check_password_hash(self._password, password)

    def __repr__(self):
        return f'<User {self.username}>'

    def __str__(self):
        return f'{self.username} - {self.role}'

# Teacher Model
class Teacher(db.Model, SerializerMixin):
    __tablename__ = 'teachers'
    serialize_rules = ('-user', '-students ',)  # Serialization rules to avoid circular references

    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Teacher's name, subject expertise, and hire date
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    hire_date = db.Column(db.DateTime, default=datetime.now)

    # Foreign key to User model (one-to-one relationship)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    user = db.relationship('User', backref='teacher', uselist=False)

    # Relationship with Student model (one-to-many relationship)
    students = db.relationship('Student', backref='teacher')

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
    date = db.Column(db.DateTime, default=datetime.now)  # Date of the transaction
    description = db.Column(db.String(255))  # Optional description for the transaction

    def __repr__(self):
        return f'<Finance Record: {self.transaction_type} - Amount: {self.amount} for Student ID: {self.student_id}>'

# Admin Model
# class Admin(db.Model, SerializerMixin):
#     __tablename__ = 'admins'
#     serialize_rules = ('-user',)  # Serialization rules to avoid circular references

#     # Primary key
#     id = db.Column(db.Integer, primary_key=True)

#     # Admin's name and hire date
#     name = db.Column(db.String(100), nullable=False)
#     hire_date = db.Column(db.DateTime, default=datetime.now)

#     # Foreign key to User model (one-to-one relationship)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
#     user = db.relationship('User', backref=db.backref('admin', uselist=False))

#     def __repr__(self):
#         return f'<Admin {self.name}>'

# # Adding back reference in Student model for finances
# Student.finances = db.relationship('Finance', back_populates='student')

class Enrollment(db.Model, SerializerMixin):
    _tablename_ = 'enrollments'
    serialize_rules = ('-student',)  # Avoid circular references during serialization

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign key to the Student model
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    student = db.relationship('Student', back_populates='enrollments')

    # Attributes
    courses = db.Column(db.String(255), nullable=False)  # e.g., "Math, Science, History"
    phone_number = db.Column(db.String(15), nullable=False)  # Phone number of the student
    enrollment_date = db.Column(db.DateTime, default=datetime.now)  # Defaults to current datetime

    def _repr_(self):
        return f'<Enrollment {self.courses} for Student ID {self.student_id}>'
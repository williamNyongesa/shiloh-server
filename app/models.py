from app import db, bcrypt
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime
from sqlalchemy.exc import IntegrityError

class Student(db.Model, SerializerMixin):
    __tablename__ = 'students'
    serialize_rules = ('-country', '-user',)
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    enrolled_date = db.Column(db.DateTime, default=datetime.now())
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False)
    country = db.relationship('Country', back_populates='students')

    # Foreign key to User model
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)

    @staticmethod
    def generate_student_id(country_code, count):
        """Generates a student ID using the country code and student count."""
        return f"{country_code}{str(count).zfill(3)}"  # Changed to zfill(3) to match '001' format

    @classmethod
    def create_with_unique_id(cls, name, phone_number, email, country_name):
        """Create a student with a unique ID based on the country."""
        country = Country.query.filter_by(name=country_name).first()
        if not country:
            raise ValueError("Invalid country name provided.")
        
        # Fetch the student count for the country atomically
        counter = StudentIDCounter.query.filter_by(country_id=country.id).first()
        if not counter:
            counter = StudentIDCounter(country_id=country.id, count=1)
            db.session.add(counter)
        else:
            counter.count += 1

        try:
            # Commit the session to lock in the count
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Failed to generate a unique student ID.")

        # Generate student ID
        student_id = cls.generate_student_id(country.code, counter.count)
        
        # Create the student record
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

class Country(db.Model, SerializerMixin):
    __tablename__ = 'countries'
    serialize_rules = ('-students',) 
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    code = db.Column(db.String(2), unique=True, nullable=False)  # KE, US, etc.

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

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    serialize_rules = ('-_password',)

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    username = db.Column(db.String(50), nullable=False)
    _password = db.Column('password', db.String(255), nullable=True)
    role = db.Column(db.String(50), nullable=False)

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

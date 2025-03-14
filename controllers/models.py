from datetime import date, datetime, timezone
from controllers import db, login_manager
from flask_login import UserMixin
from sqlalchemy import CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_property


# Function to load user based on ID and role
@login_manager.user_loader
def load_user(user_id):
    try:
        user_type, id = user_id.split('-')
        id = int(id)
        if user_type == 'admin':
            return Admin.query.get(id)
        else:
            return User.query.get(id)
    except (ValueError, AttributeError):
        print(f"ERROR: Invalid user_id: {user_id}")
        return None
    
class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"<Email={self.email}>"
    def get_id(self):
        return f"admin-{self.id}"
    
    
# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    dob = db.Column(db.Date, nullable=False)
    qualification = db.Column(db.String(200))
    document_path = db.Column(db.String(length=200), nullable=False)  # Path to uploaded document
    password = db.Column(db.String(60), nullable=False)

    def get_id(self):
        return f"user-{self.id}"


# Subject model
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    # image_path = db.Column(db.String(length=200), nullable=False)  # Path to uploaded image
    chapters = db.relationship('Chapter', backref='subject', cascade='all, delete-orphan')


# Chapter model
class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    no_of_quizes = db.Column(db.Integer, nullable=False) # I don't know how to use this stuff.
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    quizzes = db.relationship('Quiz', backref='chapter', cascade='all, delete-orphan')

# Quiz model
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    date_of_quiz = db.Column(db.DateTime, default=datetime.utcnow)
    time_duration = db.Column(db.String(10))  # HH:MM format
    no_of_questions = db.Column(db.Integer) # Need some work
    remarks = db.Column(db.Text)
    questions = db.relationship('Question', backref='quiz', cascade='all, delete-orphan')
    scores = db.relationship('Score', backref='quiz', cascade='all, delete-orphan')    
    subject = db.relationship('Subject', backref='quizzes')
    
    # Dynamically count the number of related questions
    @hybrid_property
    def no_of_questions(self):
        return len(self.questions)
    
    @hybrid_property
    def formatted_date(self):
        return self.date_of_quiz.strftime("%d/%m/%Y") if self.date_of_quiz else None
# Question model
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_title = db.Column(db.String(30), nullable=False)
    question_statement = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(255), nullable=False)
    option2 = db.Column(db.String(255), nullable=False)
    option3 = db.Column(db.String(255), nullable=False)
    option4 = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)  # Stores option number (1-4)

# Score model
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_stamp_of_attempt = db.Column(db.DateTime, default=datetime.utcnow)
    total_scored = db.Column(db.Integer, nullable=False)

    user = db.relationship('User', backref='scores')
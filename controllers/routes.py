import matplotlib
matplotlib.use('Agg')
import time
from datetime import datetime
from email_validator import validate_email
from flask import render_template, session, request, flash, redirect, url_for, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from controllers import app, db
from controllers.models import Admin, User, Subject, Chapter,  Question, Score, Quiz
import os
import matplotlib.pyplot as plt
from sqlalchemy import or_, and_, func
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify


# Testing
@app.route('/add_question/<int:quiz_id>', methods=['GET', 'POST'])
def add_question(quiz_id):
    print("Got Quiz ID in add_question: ", quiz_id) #Debug
    if request.method == 'POST':
        quiz_id = request.form.get('quiz_id')
        question_title = request.form.get('question_title')
        question_statement = request.form.get('question_statement')
        option1 = request.form.get('option1')
        option2 = request.form.get('option2')
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        correct_option = request.form.get('correct_option')

        new_question = Question(
            quiz_id=quiz_id,
            question_title=question_title,
            question_statement=question_statement,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option
        )
        try:
            db.session.add(new_question)
            db.session.commit()
            flash("Question added successfully!", "success")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
    subject_id = Quiz.query.filter_by(id=quiz_id).first().subject_id
    print("Subject ID: ", subject_id) #Debug
    chapters=Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('add_question.html', chapters=chapters, quiz_id=quiz_id)

@app.route('/')
@app.route('/home')
def home():
    return render_template('base.html')

@app.route('/signin', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        print(f"Email: {email}, Type: {type(email)}") #Debug
        password = request.form.get('password')

        # if email==session.get('deleted email'):
        #     flash("Your account have been deleted due to malpractices. Contact admin!", "danger")
        #     return redirect(request.url)
        # # if user is Admin
        admin = Admin.query.filter_by(email=email).first()
        # print(Admin.query.filter_by(email=email).first())
        if admin and check_password_hash(admin.password, password) and validate_email(email):
            # user_id = f"admin-{admin.id}"
            login_user(admin)
            # session['user_type'] = 'admin'
            # session['user_id'] = admin.id
            flash(f"Success! You are logged in as Admin with email {email}", "success")
            return redirect(url_for('dashboard'))
        
        # Check if user is a User
        user = User.query.filter_by(email=email).first()
        print(f"User: {user}, Email={email}")
        if User and check_password_hash(user.password, password) and validate_email(email):
            # user_id = f"User-{User.id}"
            try:
                login_user(user)
                return redirect(url_for('dashboard'))
            except Exception as e:
                print(f"Error: {e}, line 60")
            # if user.is_approved:
            #     flash(f"Success! You are logged in as User with username {user.username}", "success")
            #     if session.get("accept_request") and session.get("category"):
            #         flash(session["accept_request"], session["category"])
            #         session.pop('accept_request')
            #         session.pop('category')

            #     return redirect(url_for('dashboard'))
            # # If login fails
            # elif not user.is_approved:
            #     flash("Your account has been blocked by admin due to fraudulent activity. Please contact admin at 'Ay@yahoo.com'", "danger")
            #     return render_template('login.html')
        flash('Invalid email or password. Please check!', 'danger')
    
    return render_template('login.html')

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email=request.form['email']
        username = request.form['username']
        dob = datetime.strptime(request.form['dob'], '%Y-%m-%d').date()
        password=generate_password_hash(request.form['password'])
        qualification = request.form['qualification']




        # Handle file upload
        if 'document' not in request.files or not request.files['document'].filename:
            flash('No file uploaded.', 'danger')
            return redirect(request.url)

        file = request.files['document']

        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{int(time.time())}_{filename}"

            # Save file to the uploads folder
            upload_folder = os.path.join(app.root_path, 'static', 'uploads')
            file_path = os.path.join(upload_folder, filename)

            os.makedirs(upload_folder, exist_ok=True)

            file.save(file_path)

            # Save relative path to db
            relative_path = f'uploads/{filename}'
            new_User = User(
                fullname=fullname,
                email=email,
                username=username,
                dob=dob,
                password=password,
                document_path=relative_path,
                qualification=qualification
            )  # Save relative path

            try:
                db.session.add(new_User)
                db.session.commit()
                flash('Registration successful!', 'success')
                return redirect(url_for('login'))
            except IntegrityError as e:
                    db.session.rollback()  # Rollback the transaction to avoid corruption
                    print("The errior is: ", e)
                    if 'UNIQUE constraint failed' in str(e.orig):
                        # Determine which field caused the issue
                        if 'username' in str(e.orig):
                            flash('Username is already taken. Please choose a different one.', 'danger')
                        elif 'email' in str(e.orig):
                            flash('Email is already registered. Please use a different email.', 'danger')
                        elif 'contact_no' in str(e.orig):
                            flash('Contact number is already in use. Please provide a unique contact number.', 'danger')
                        else:
                            flash('A unique constraint failed. Please ensure all unique fields are distinct.', 'danger')
                    else:
                        flash('An error occurred during registration. Please try again later.', 'danger')

                    return redirect(request.url)
        else:
            flash('Invalid file type. Only PDFs are allowed.', 'danger')
            return redirect(request.url)
        
    return render_template('signup.html', qualifications=['XII', 'B.Tech', 'M.Tech', 'PhD'])


                            # Admin Action


@login_required                   
@app.route('/admin/add_subject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        # Extract data from the form
        sub_name = request.form.get('subName')
        description = request.form.get('description')

        # Validate the form data (not necessary but for precaution because using required attribute in form)
        if not sub_name  or not description:
            flash("'Subject Name' and 'description' are the required fileds", "danger")
            return redirect(url_for('add_service'))

        # Create a new service instance
        new_subject = Subject(
            name=sub_name,
            description=description
        )

        # Add to the database
        try:
            db.session.add(new_subject)
            db.session.commit()
            flash("Subject added successfully!", "success")
            return redirect(url_for('dashboard'))
        except IntegrityError as e:
            db.session.rollback()
            # Check for unique constraint failure
            if "UNIQUE constraint failed" in str(e.orig):
                # Parse the error message to extract the field name
                error_field = str(e.orig).split(".")[-1]
                flash(f"Error: A service with the same {error_field} already exists.", "danger")
            else:
                flash("An error occurred while adding the service.", "danger")
            return redirect(url_for('add_subject'))
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {str(e)}", "danger")
            return redirect(url_for('add_subject'))

    return render_template('add_subject.html')

@login_required                   
@app.route('/admin/add_quiz/<int:chapter_id>/<int:subject_id>', methods=['GET', 'POST'])
def add_quiz(chapter_id=None, subject_id=None):
    print("Got Chapter ID: ", chapter_id) #Debug
    print("Got Subject ID: ", subject_id) #Debug
    chapter = Chapter.query.filter_by(id=chapter_id).first()
    if request.method == 'POST':
        # Extract data from the form
        # chapter_id = int(request.form.get('chapterId'))
        # subject_id = int(request.form.get('subjectId'))
        date_of_quiz = request.form.get('dateOfQuiz')
        time_duration = request.form.get('timeDuration')

        # Create a new service instance
        new_quiz = Quiz(
            chapter_id=chapter_id,
            date_of_quiz=date_of_quiz,
            time_duration=time_duration,
            subject_id=subject_id
            # no_of_questions=no_of_questions,
            # remarks=remarks
        )

        # Add to the database
        try:
            db.session.add(new_quiz)
            db.session.commit()
            flash("Quiz added successfully!", "success")
            return redirect(url_for('quiz_management'))
        except IntegrityError as e:
            db.session.rollback()
            # Check for unique constraint failure
            if "UNIQUE constraint failed" in str(e.orig):
                # Parse the error message to extract the field name
                error_field = str(e.orig).split(".")[-1]
                flash(f"Error: A service with the same {error_field} already exists.", "danger")
            else:
                print(f"Error: {e}")
                flash("An error occurred while adding the service.", "danger")
            return redirect(url_for('add_quiz'))
        except Exception as e:
            db.session.rollback()
            print(f"Bahut Error: {e}")
            flash(f"An unexpected error occurred: {str(e)}", "danger")
            # return redirect(request.url)

    return render_template('add_quiz.html', subjects=Subject.query.all(), chap_id=chapter_id, chap=chapter, sub_id=subject_id)


@app.route('/get_chapters/<int:subject_id>')
def get_chapters(subject_id):
    # Query chapters belonging to the selected subject
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    
    # Convert to JSON format
    chapters_data = [{"id": chapter.id, "name": chapter.name} for chapter in chapters]
    
    return jsonify({"chapters": chapters_data})

@app.route('/admin/quiz_management')
@login_required
def quiz_management():
    quizes = Quiz.query.all()
    return render_template('quiz_management.html', quizes=quizes)

@app.route('/admin/add_chapter/<int:subject_id>', methods=['GET', 'POST'])
@login_required                   
def add_chapter(subject_id=None):
    print("Got Subject ID: ", subject_id) #Debug 
    # subject_id = Subject.query.filter_by(id=subject_id).first()
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')


        new_chapter = Chapter(
            name=name,
            description=description,
            no_of_quizes=0,  # Initialize with 0 quizzes
            subject_id=subject_id
        )
        try:
            db.session.add(new_chapter)
            db.session.commit()
            flash("Chapter added successfully!", "success")
            return redirect(url_for('dashboard'))
        except IntegrityError as e:
            db.session.rollback()
            if "UNIQUE constraint failed" in str(e):
                flash(f"Error: A chapter with this {request.form.get('name')} already exists!", "danger")
            else:
                flash(f"Database error: {str(e)}", "danger")  # General error message
            return redirect(url_for('add_chapter'))
    return render_template('add_chapter.html', sub_id=subject_id)

# @login_required                   
# @app.route('/admin/add_question', methods=['GET', 'POST'])
# def add_question():
#     return render_template('add_question.html')


@app.route('/dashboard')
@login_required
def dashboard(): 
    
    # if role == 'admin':
    if isinstance(current_user, Admin):
        subjects = Subject.query.all()

        # prof = Professional.query.all()
        # custs = Customer.query.all()
        # requests = ServiceRequests.query.all()
        return render_template('dashboard.html', subjects=subjects)
    
    # if role == 'customer':
    if isinstance(current_user, User):
        quizes = Quiz.query.all()
        # services = Service.query.all()
        # customer=Customer.query.filter_by(id=user_id).first()
        # available_services = (
        # db.session.query(Service)
        # .join(ServiceLocation)
        # .filter(ServiceLocation.pin_code == customer.pin_code)
        # .all()
        # )
        # service_history = ServiceRequests.query.filter_by(customer_id=session.get('user_id')).order_by(ServiceRequests.date_of_request.desc()).all()
        return render_template('student_dashboard.html', quizes=quizes)
    
    return render_template('dashboard.html')

# Student Interactions
@app.route('/student/view_details<int:quiz_id>', methods=['GET', 'POST'])
def view_quiz(quiz_id):
    if request.method=='POST':
        print('Post Method invoked')
    quiz = Quiz.query.filter_by(id=quiz_id).first()
    return render_template('quiz_details.html', quiz=quiz)




@app.route('/test/<int:quiz_id>')
def exam_portal(quiz_id):
    quiz = Quiz.query.filter_by(id=quiz_id).first()
    # print(f"Got Time: {quiz.time_duration}", type({quiz.time_duration})) #Debug
    if isinstance(quiz.time_duration, set):
        quiz.time_duration = list(quiz.time_duration)[0] #extract the time in the str format
    hrs, mins = map(int, quiz.time_duration.split(":"))
    print(f"Quiz time duration: {quiz.time_duration}", type(quiz.time_duration))
    total_secs = (hrs * 3600) + (mins * 60)
    # print(f"Converted Time Duration: {total_secs} seconds")  # Debug

    questions = quiz.questions
    current_question_index = 1  # Start with the first question
    print(questions)
    return render_template('exam_portal.html', quiz=quiz, quiz_duration=total_secs, questions=quiz.questions, current_question_index=current_question_index)




@app.route('/submit_quiz', methods=['POST'])
@login_required  # Ensure only logged-in users can submit quizzes
def submit_quiz():
    if request.method == 'POST':
        # Extract the user's selected option (if any)
        selected_option = request.form.get('option')

        # Save the score or answers in the database
        score = Score(user_id=current_user.id, quiz_id=session.get('quiz_id'), selected_option=selected_option)
        db.session.add(score)
        db.session.commit()

        flash("Quiz submitted successfully!", "success")
        return redirect(url_for('dashboard'))  # Redirect to the user's dashboard after submission

    flash("Invalid quiz submission!", "danger")
    return redirect(url_for('exam_portal'))  # Redirect back to quiz page in case of an issue



@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # Clears all session data for a fresh start
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))  # Redirect to login page instead of home page

@app.route('/search')
@login_required
def search():
    return render_template('search.html')
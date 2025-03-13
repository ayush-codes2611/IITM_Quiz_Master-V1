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

# Testing
@app.route('/create_quiz/<int:chapter_id>')
def create_quiz(chapter_id=None):
    # Your logic here
    return render_template('quiz_management.html')

@app.route('/')
@app.route('/home')
def home():
    return render_template('base.html')

@app.route('/signin', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        print(f"Email: {email}, Type: {type(email)}")
        password = request.form.get('password')

        # if email==session.get('deleted email'):
        #     flash("Your account have been deleted due to malpractices. Contact admin!", "danger")
        #     return redirect(request.url)
        # # if user is Admin
        admin = Admin.query.filter_by(email=email).first()
        print(Admin.query.filter_by(email=email).first())
        # print(f"Admin: {admin}, Email={email}")
        # print(f"Boolean_Email: {validate_email(email)}")
        # print(f"Boolean_Password: {check_password_hash(admin.password, password)}")
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
@app.route('/admin/add_quiz', methods=['GET', 'POST'])
def add_quiz():
    if request.method == 'POST':
        # Extract data from the form
        chapter_id = int(request.form.get('chapterId'))
        date_of_quiz = request.form.get('dateOfQuiz')
        time_duration = request.form.get('timeDuration')

        # Create a new service instance
        new_quiz = Quiz(
            chapter_id=chapter_id,
            date_of_quiz=date_of_quiz,
            time_duration=time_duration,
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

    return render_template('add_quiz.html')

@app.route('/admin/quiz_management')
@login_required
def quiz_management():
    return render_template('quiz_management.html', quizes=Quiz.query.all())

@login_required                   
@app.route('/admin/add_chapter', methods=['GET', 'POST'])
def add_chapter():
    if request.method == 'POST':
        name = request.form.get('name')
        no_of_quizes = request.form.get('noOfQuizes')
        description = request.form.get('description')
        subject_id = int(request.form.get('subjectId'))
        print(f"Subject ID: {subject_id}")

        new_chapter = Chapter(
            name=name,
            no_of_quizes=no_of_quizes,
            description=description,
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
    return render_template('add_chapter.html')


@app.route('/dashboard')
@login_required
def dashboard(chapter_id=None): 
    
    # if role == 'admin':
    if isinstance(current_user, Admin):
        subjects = Subject.query.all()

        # prof = Professional.query.all()
        # custs = Customer.query.all()
        # requests = ServiceRequests.query.all()
        return render_template('dashboard.html', subjects=subjects)
    
    # if role == 'customer':
    if isinstance(current_user, User):
        quizes = Question.query.filter_by(chapter_id=chapter_id).all()
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
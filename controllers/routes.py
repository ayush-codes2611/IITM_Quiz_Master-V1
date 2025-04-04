import matplotlib
matplotlib.use('Agg')
import time, random
from datetime import datetime
from email_validator import validate_email
from flask import render_template, session, request, flash, redirect, url_for, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from controllers import app, db
from controllers.models import Admin, User, Subject, Chapter,  Question, Score, Quiz
import os
import matplotlib.pyplot as plt
from sqlalchemy import or_, and_, func, distinct
from sqlalchemy.orm import joinedload, load_only
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify
from collections import defaultdict


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
            login_user(admin, remember=False)
            # session['user_type'] = 'admin'
            # session['user_id'] = admin.id
            flash(f"Success! You are logged in as Admin with email {email}", "success")
            return redirect(url_for('dashboard'))
        
        # Check if user is a User
        user = User.query.filter_by(email=email).first()
        print(f"User: {user}, Email={email}")
        if user and check_password_hash(user.password, password) and validate_email(email):
            # user_id = f"User-{User.id}"
            try:
                login_user(user, remember=False)
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
        else: 
            flash('Invalid email or password. Please check!', 'danger')
            return redirect(url_for('login'))
    
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
        # Convert date string to datetime object (assuming format 'YYYY-MM-DD')
        time_duration = request.form.get('timeDuration')
        date_of_quiz_str = request.form.get('quiz_date')
        try:
            date_of_quiz = datetime.strptime(date_of_quiz_str, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
            return redirect(request.url)

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
            chapter.no_of_quizes +=1            
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


@app.route('/api/get_chapters/<int:subject_id>')
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
        return render_template('admin_dashboard.html', subjects=subjects)
    
    # if role == 'customer':
    if isinstance(current_user, User):
        quizes = Quiz.query.all()
        # return render_template('student_admin_dashboard.html', quizes=quizes)
        return redirect(url_for('student_dashboard'))
    
    return render_template('admin_dashboard.html')

# Student Interactions
@app.route('/student_dashboard')
@login_required
def student_dashboard():
    today = datetime.now().date()
    print(today)
    
    # Fetch all quizzes
    quizes = Quiz.query.all()

    # Separate upcoming and previous quizzes
    upcoming_quizzes = [quiz for quiz in quizes if quiz.date_of_quiz.date() >= today]
    # print(upcoming_quizzes.date_of_quiz)
    previous_quizzes = [quiz for quiz in quizes if quiz.date_of_quiz.date() < today]
    # print(previous_quizzes.date_of_quiz)

    return render_template('student_dashboard.html', 
                           upcoming_quizzes=upcoming_quizzes, 
                           previous_quizzes=previous_quizzes)


@app.route('/student/view_details<int:quiz_id>', methods=['GET', 'POST'])
def view_quiz(quiz_id):
    if request.method=='POST':
        print('Post Method invoked')
    quiz = Quiz.query.filter_by(id=quiz_id).first()
    return render_template('quiz_details.html', quiz=quiz)


@app.route('/exam_portal/<int:quiz_id>')
@login_required
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
    # Convert questions into a JSON-serializable list (dictionary format)
    questions_data = [
        {
            "id": q.id,
            "question_title": q.question_title,
            "question_statement": q.question_statement,
            "option1": q.option1,
            "option2": q.option2,
            "option3": q.option3,
            "option4": q.option4,
            "correct_option": q.correct_option
        }
        for q in quiz.questions
    ]
    # print(questions_data) #Debug
    return render_template('exam_portal.html', quiz=quiz, quiz_duration=total_secs, questions=questions_data, current_question_index=current_question_index)

@app.route('/quiz_scores/<int:user_id>')
@login_required
def quiz_scores(user_id=None):
    scores = (
        Score.query
        .join(Quiz)  # Join to access Quiz fields
        .filter(Score.user_id == user_id)
        .order_by(Quiz.chapter_id, Score.time_stamp_of_attempt.desc())  # Order by chapter and time_stamp_of_attempt
        .options(joinedload(Score.quiz))  # Eager load to reduce queries
        .all()
    )
    return render_template('quiz_scores.html', scores=scores)


@app.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    try:
        data = request.get_json()  # Receive JSON from frontend
        print(data)
        user_id = data.get("user_id")
        quiz_id = data.get("quiz_id")
        answers = data.get("answers", [])  # Extract answers list

        total_score = 0  # Initialize score
        for answer in answers:
            question_id = answer['question_id']
            attempted_option = answer['attempted_option']

            # Fetch the correct option from the database
            question = Question.query.get(question_id)
            correct_option = question.correct_option if question else None

            # Compare attempted option with the correct one
            if attempted_option and attempted_option == str(correct_option):  # Ensure comparison is string-based
                total_score += 1  # Add points for correct answers

        # print("Success")
        # Save the score to the database
        new_score = Score(user_id=user_id, quiz_id=quiz_id, total_scored=total_score)
        # print("Agian Success")
        db.session.add(new_score)
        db.session.commit()

        return jsonify({"score": total_score})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500  # Handle errors properly





@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # Clears all session data for a fresh start
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))  # Redirect to login page instead of home page


@app.route('/search', methods=['GET'])
def search():
    # Step 1: Determine if user is 'admin' or 'user'
    user_role = "admin" if  current_user.__tablename__=='admin' else "user"

    # Step 2: Define accessible models for each role
    possible_models = {
        "admin": {'user': User, 'subject': Subject, 'quiz': Quiz},
        "user": {'subject': Subject, 'quiz': Quiz, 'score': Score, "chapter": Chapter}
    }

    # Step 3: Define filterable and displayable columns
    col = {
        "filterable_cols": {
            "user": ['fullname', 'email', 'username', 'qualification'],
            "subject": ["name"],
            "quiz": ["date_of_quiz", "time_duration"],
            "score": ["total_scored"], #need to add the date of quiz too.
            "chapter": ["name"]
        },
        "displayable_columns": {
            "admin": {
                "user": ["id", "fullname", "username", "qualification", "document_path"],
                "subject": ["id", "name", "description"],
                "quiz": ["id", "date_of_quiz", "time_duration"]
            },
            "user": {
                "chapter": ["name", "description"],
                "subject": ["id", "name", "description"],
                "quiz": ["date_of_quiz", "time_duration"],
                "score": ["time_stamp_of_attempt", "total_scored"]
            }
        }
    }

    # Step 4: Get user input (default to empty if missing)
    search_by = request.args.get('search_by', '').lower()
    search_text = request.args.get('search_text', '').lower()

    # Step 5: Pass possible models to template (for dropdown)
    model_options = possible_models[user_role]

    # If the user has not selected a model yet, just show the search page
    if not search_by:
        return render_template('search.html', possible_models=model_options, results=[])

    # Step 6: Validate search_by and fetch model
    selected_model = model_options.get(search_by)
    if not selected_model or search_by not in col["filterable_cols"]:
        return render_template('search.html', possible_models=model_options, results=[])

    # Step 7: Construct filter conditions
    filter_conditions = [
        getattr(selected_model, col_name).ilike(f"%{search_text}%")
        for col_name in col["filterable_cols"][search_by]
    ]

    # # Step 8: Query the database
    # results = selected_model.query \
    #     .filter(or_(*filter_conditions)) \
    #      .options(load_only(*[getattr(selected_model, col) for col in col["displayable_columns"][user_role][search_by]])) \
    #     .all()
    # print(results)

    query = selected_model.query.filter(or_(*filter_conditions))
    # If querying the Score model, filter by current user
    if selected_model == Score:
        print(current_user.id)
        query = query.filter(and_(Score.user_id == current_user.id, or_(*filter_conditions)))
        print(query)
    results = query.options(
        load_only(*[getattr(selected_model, col) for col in col["displayable_columns"][user_role][search_by]])
    ).all()

    print(f"Results: {results}")
    print(f"Column_names: {col['displayable_columns'][current_user.__tablename__][search_by]}")

    # Step 9: Render template with possible models and results
    return render_template('search.html', possible_models=model_options, results=results, search_by=search_by, search_text=search_text, column_names=col['displayable_columns'][current_user.__tablename__][search_by])


# @app.route('/summary')
# def summary():
#     save_dir = os.path.join(app.root_path, 'static', "summary_images") #Here the the root is controllers we are making summaary_images dir. 
#     os.makedirs(save_dir, exist_ok=True)  # Create the directory if it doesn't exist
#     try: 
#         if isinstance(current_user, Admin):
@app.route('/api/admin-summary-stats')
@login_required
def admin_summary_stats():
    subjects = [row[0] for row in db.session.query(Subject.name).all()]

    # Generate consistent colors for subjects
    subject_colors = {subj: f'rgba({random.randint(50, 255)}, {random.randint(50, 255)}, {random.randint(50, 255)}, 0.5)' for subj in subjects}
    subject_borders = {subj: subject_colors[subj].replace("0.5", "1") for subj in subjects}  # Stronger border color

    # Fetch Total Counts
    total_users = db.session.query(User.id).count()
    total_quizzes = db.session.query(Quiz.id).count()
    total_attempts = db.session.query(Score.id).count()
    total_subjects = db.session.query(Subject.id).count()

    # Most Popular Subject (by quiz attempts)
    most_popular_subject = (
        db.session.query(Subject.name, func.count(Score.id))
        .join(Quiz, Subject.id == Quiz.subject_id)
        .join(Score, Quiz.id == Score.quiz_id)
        .group_by(Subject.name)
        .order_by(func.count(Score.id).desc())
        .limit(1)
        .first()
    )
    most_popular_subject = most_popular_subject[0] if most_popular_subject else "N/A"

    # Top Scorer (Overall)
    top_scorer = (
        db.session.query(User.fullname, func.sum(Score.total_scored))
        .join(Score, User.id == Score.user_id)
        .group_by(User.id)
        .order_by(func.sum(Score.total_scored).desc())
        .limit(1)
        .first()
    )
    top_scorer = top_scorer[0] if top_scorer else "N/A"

    # Fetch Subject-Wise Quiz Counts
    quiz_counts = (
        db.session.query(Subject.name, func.count(Quiz.id))
        .outerjoin(Quiz, Subject.id == Quiz.subject_id)
        .group_by(Subject.name)
        .all()
    )

    # Fetch Subject-Wise Quiz Attempts
    quiz_attempts = (
        db.session.query(Subject.name, func.count(Score.id))
        .join(Quiz, Subject.id == Quiz.subject_id)
        .join(Score, Quiz.id == Score.quiz_id)
        .group_by(Subject.name)
        .all()
    )

    # Fetch Top Performer and Average Scores per Subject
    performance_stats = (
        db.session.query(
            Subject.name,
            func.max(Score.total_scored).label("top_score"),
            func.avg(Score.total_scored).label("avg_score")
        )
        .join(Quiz, Subject.id == Quiz.subject_id)
        .join(Score, Quiz.id == Score.quiz_id)
        .group_by(Subject.name)
        .all()
    )

    # Fetch Monthly Quiz Attempts (For Line Chart)
    monthly_attempts = defaultdict(int)
    scores = db.session.query(Score.time_stamp_of_attempt).all()
    
    for score in scores:
        month_year = score.time_stamp_of_attempt.strftime('%b %Y')  # Example: "Mar 2025"
        monthly_attempts[month_year] += 1

    # Sort monthly data by date order
    sorted_monthly_attempts = sorted(monthly_attempts.items(), key=lambda x: datetime.strptime(x[0], '%b %Y'))
    monthly_labels = [entry[0] for entry in sorted_monthly_attempts]
    monthly_values = [entry[1] for entry in sorted_monthly_attempts]

    # Structure Data for Each Graph
    data = {
         "summary": {
            "total_users": total_users,
            "total_quizzes": total_quizzes,
            "total_attempts": total_attempts,
            "total_subjects": total_subjects,
            "most_popular_subject": most_popular_subject,
            "top_scorer": top_scorer
        },
        "quiz_counts": {
            "title": "Number of Quizzes per Subject",
            "labels": [row[0] for row in quiz_counts],
            "values": [row[1] for row in quiz_counts],
            "backgroundColors": [subject_colors[row[0]] for row in quiz_counts],
            "borderColors": [subject_borders[row[0]] for row in quiz_counts]
        },
        "quiz_attempts": {
            "title": "Total Quiz Attempts per Subject",
            "labels": [row[0] for row in quiz_attempts],
            "values": [row[1] for row in quiz_attempts],
            "backgroundColors": [subject_colors[row[0]] for row in quiz_attempts],
            "borderColors": [subject_borders[row[0]] for row in quiz_attempts]
        },
        "performance_stats": {
            "title": "Top Performer vs. Average Score per Subject",
            "labels": [row[0] for row in performance_stats],
            "top_scores": [row[1] for row in performance_stats],
            "avg_scores": [round(row[2], 2) for row in performance_stats],
            "backgroundColors": [subject_colors[row[0]] for row in performance_stats],
            "borderColors": [subject_borders[row[0]] for row in performance_stats]
        },
        "monthly_attempts": {
            "title": "User Participation Over Time",
            "labels": monthly_labels,
            "values": monthly_values
        }

    }

    return jsonify(data)

from flask import jsonify
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func, extract

@app.route('/api/user_summary_data')
@login_required
def user_summary_data():
    today = datetime.now()

    # Fetch all subjects
    subjects = db.session.query(Subject).all()

    # Fetch past quizzes (before today)
    past_quizzes = (
        db.session.query(Subject.name, func.count(Quiz.id))
        .join(Quiz, Quiz.subject_id == Subject.id)
        .filter(Quiz.date_of_quiz < today)
        .group_by(Subject.name)
        .all()
    )

    # Fetch ongoing quizzes (today or later)
    ongoing_quizzes = (
        db.session.query(Subject.name, func.count(Quiz.id))
        .join(Quiz, Quiz.subject_id == Subject.id)
        .filter(Quiz.date_of_quiz >= today)
        .group_by(Subject.name)
        .all()
    )

    # Fetch monthly quiz attempts (only one attempt per quiz per month per user)
    monthly_attempts = (
        db.session.query(
            extract('year', Score.time_stamp_of_attempt).label("year"),
            extract('month', Score.time_stamp_of_attempt).label("month"),
            func.count(func.distinct(Score.quiz_id)).label("attempts")
        )
        .filter(Score.user_id == current_user.id)
        .group_by("year", "month")
        .order_by("year", "month")
        .all()
    )

    # Convert subject-wise quiz data to a dictionary
    quiz_data = {sub.name: {"past": 0, "ongoing": 0} for sub in subjects}

    for subject_name, count in past_quizzes:
        quiz_data[subject_name]["past"] = count

    for subject_name, count in ongoing_quizzes:
        quiz_data[subject_name]["ongoing"] = count

    # Convert subject-wise quiz data to list format
    quiz_data_list = [
        {"subject": sub, "past": data["past"], "ongoing": data["ongoing"]}
        for sub, data in quiz_data.items()
    ]

    # Convert monthly attempts data to JSON format
    monthly_attempts_data = [
        {"month": f"{int(year)}-{int(month):02d}", "attempts": attempts}
        for year, month, attempts in monthly_attempts
    ]

    # Summary Metrics
    total_quizzes = Quiz.query.count()
    past_quiz_count = sum(data["past"] for data in quiz_data.values())
    ongoing_quiz_count = sum(data["ongoing"] for data in quiz_data.values())
    total_subjects = len(subjects)

    summary = {
        "total_quizzes": total_quizzes,
        "past_quizzes": past_quiz_count,
        "ongoing_quizzes": ongoing_quiz_count,
        "total_subjects": total_subjects
    }

    return jsonify({
        "summary": summary,
        "quiz_data": quiz_data_list,
        "monthly_attempts": monthly_attempts_data
    })






@app.route('/summary')
@login_required
def summary():
    if isinstance(current_user, Admin):
        return render_template('admin_summary.html')
    elif isinstance(current_user, User):
        return render_template('user_summary.html')
    else: 
        flash("Sorry something went wrong", "danger")
        return redirect(request.url)


@app.route("/test")
def test():
    subject = Subject.query.filter_by(id=1).first()
    return render_template('edit_subject.html', subject=subject) #hardcoded



@app.route('/admin/chapter/edit/<int:chapter_id>', methods=['GET', 'POST'])
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    
    if request.method == 'POST':
        updated_name = request.form['name'].strip()
        updated_description = request.form['description'].strip()

        # Check if no changes were made
        if chapter.name == updated_name and chapter.description == updated_description:
            flash('No changes were made.', 'info')
            return redirect(url_for('dashboard'))

        # Check if another chapter with the same name or description exists in the same subject
        existing_chapter = Chapter.query.filter(
            Chapter.subject_id == chapter.subject_id,
            (Chapter.name == updated_name) | (Chapter.description == updated_description),
            Chapter.id != chapter.id  # Exclude the current chapter itself
        ).first()

        if existing_chapter:
            flash('A chapter with this name or description already exists in this subject!', 'danger')
            return redirect(url_for('edit_chapter', chapter_id=chapter.id))

        # Update chapter details
        chapter.name = updated_name
        chapter.description = updated_description
        
        try:
            db.session.commit()
            flash('Chapter updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating chapter: {e}', 'danger')

        return redirect(url_for('dashboard'))

    return render_template('edit_chapter.html', chapter=chapter)


@app.route('/delete_chapter/<int:chapter_id>', methods=['POST'])
@login_required
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)

    try:
        db.session.delete(chapter)
        db.session.commit()
        flash("Chapter and its related quizzes & questions deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting chapter: {str(e)}", "danger")

    return redirect(url_for('dashboard'))

@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)

    if request.method == 'POST':
        # Get the form data
        new_statement = request.form['statement'].strip()
        new_option_a = request.form['option_a'].strip()
        new_option_b = request.form['option_b'].strip()
        new_option_c = request.form['option_c'].strip()
        new_option_d = request.form['option_d'].strip()
        new_correct_answer = request.form['correct_answer'].strip()

        # Check if any changes were made
        if (
            question.question_statement == new_statement and
            question.option1 == new_option_a and
            question.option2 == new_option_b and
            question.option3 == new_option_c and
            question.option4 == new_option_d and
            question.correct_option == new_correct_answer
        ):
            flash('No changes made!', 'warning')
        else:
            # Update the question
            question.question_statement = new_statement
            question.option1 = new_option_a
            question.option2 = new_option_b
            question.option3 = new_option_c
            question.option4= new_option_d
            question.correct_option = new_correct_answer

            db.session.commit()
            flash('Question updated successfully!', 'success')

        return redirect(url_for('quiz_management'))  # Change to your appropriate route

    return render_template('edit_question.html', question=question)


@app.route('/delete_question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)

    # Delete the question
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!', 'danger')

    return redirect(url_for('quiz_management'))


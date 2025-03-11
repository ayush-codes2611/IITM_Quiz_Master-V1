import matplotlib
matplotlib.use('Agg')
import time
from datetime import datetime
from email_validator import validate_email
from flask import render_template, session, request, flash, redirect, url_for, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from controllers import app, db
from controllers.models import Admin, Professional, Service, Customer, ServiceRequests, ServiceLocation
import os
import matplotlib.pyplot as plt
from sqlalchemy import or_, and_, func
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/')
@app.route('/home')
def home():
    return render_template('base.html')

@app.route('/base2')
def base2():
    return render_template('base2.html')

@app.route('/signin')
@app.route('/login')
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # if email==session.get('deleted email'):
        #     flash("Your account have been deleted due to malpractices. Contact admin!", "danger")
        #     return redirect(request.url)
        # # if user is Admin
        admin = Admin.query.filter_by(email=email).first()
        if admin and check_password_hash(admin.password, password) and validate_email(email):
            # user_id = f"admin-{admin.id}"
            login_user(admin)
            session['user_type'] = 'admin'
            session['user_id'] = admin.id
            flash(f"Success! You are logged in as Admin with email {email}", "success")
            # return redirect(url_for('dashboard'))
            return "Within the dashboard"
        
        # Check if user is a Customer
        customer = Customer.query.filter_by(email=email).first()
        if customer and check_password_hash(customer.password, password) and validate_email(email):
            # user_id = f"customer-{customer.id}"
            login_user(customer)
            session['user_type'] = 'customer'
            session['user_id'] = customer.id
            if customer.is_approved:
                flash(f"Success! You are logged in as Customer with username {customer.username}", "success")
                if session.get("accept_request") and session.get("category"):
                    flash(session["accept_request"], session["category"])
                    session.pop('accept_request')
                    session.pop('category')

                return redirect(url_for('dashboard'))
            # If login fails
            elif not customer.is_approved:
                flash("Your account has been blocked by admin due to fraudulent activity. Please contact admin at 'Ay@yahoo.com'", "danger")
                return render_template('login.html')
        flash('Invalid email or password. Please check!', 'danger')
    
    return render_template('login.html')

# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, redirect, request, url_for
from flask_login import (
    current_user,
    login_user,
    logout_user
)

from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import *

from apps.authentication.util import verify_pass
from google_auth_oauthlib.flow import InstalledAppFlow
from flask import Flask, render_template, request, redirect, url_for, flash

from simplegmail import Gmail
from simplegmail.query import construct_query
import os
from datetime import datetime
import re 
from weasyprint import HTML

@blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))


# Login & Registration

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = Users.query.filter_by(username=username).first()

        # Check the password
        if user and verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for('authentication_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template('accounts/login.html',
                               msg='Wrong user or password',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html',
                               form=login_form)
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username = request.form['username']
        email = request.form['email']

        # Check usename exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Username already registered',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Email already registered',
                                   success=False,
                                   form=create_account_form)

        # else we can create the user
        user = Users(**request.form)
        db.session.add(user)
        db.session.commit()

        # Delete user from session
        logout_user()
        
        return render_template('accounts/register.html',
                               msg='Account created successfully.',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('accounts/register.html', form=create_account_form)


def create_email_creds():
    scopes = ['https://www.googleapis.com/auth/gmail.readonly']
    credentials_file = 'client_secret.json'  # Path to your OAuth 2.0 credentials file

    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
    creds = flow.run_local_server(port=0)
    return creds

@blueprint.route('/add-email', methods=['POST'])
def add_email():
    if not current_user.is_authenticated:
        return redirect(url_for('authentication_blueprint.login'))  # Ensure user is logged in
    
    creds = create_email_creds()  # Call the function
    
    # Create a new Emails instance with current user's ID, example email, and token data
    new_email = Emails(
        user_id=current_user.get_id(),  # Get the current user's ID
        email=current_user.email,       # Optionally use current user's email or another input
        token_data=creds.to_json()      # Save the credentials as a JSON string (adjust as needed)
    )
    
    # Add the new email to the database session
    db.session.add(new_email)
    
    try:
        db.session.commit()  # Commit the transaction
        flash("Email credentials added successfully!")  # Optional success message
    except Exception as e:
        db.session.rollback()  # Rollback in case of an error
        flash(f"Error adding email credentials: {e}", 'error')  # Display error message
    
    # Redirect to the index page or another relevant page
    return redirect(url_for('home_blueprint.index'))

@blueprint.route('/save-invoices', methods=['POST'])
def save_invoices():
    user_email = Emails.query.filter_by(user_id=current_user.get_id()).first()
    if user_email:
        creds = user_email.token_data
    invoices_folder = r'D:\Projects\invoisaver\Invoices'

    gmail = Gmail()  # Pass the credentials to the Gmail class

    query_params = { # select the list of email you want to get from the Gmail inbox
    "newer_than": (31, "day"),
    #"unread": False,
    }
    mails = gmail.get_messages(query=construct_query(query_params)) # run the query and get list of emails
    
    for message in mails:
        # Changing the date format to be more clear
        date_string = message.date.split()[0]
        date_obj = datetime.strptime(date_string, '%Y-%m-%d')
        clear_date = date_obj.strftime('%d-%m-%Y')
        clear_time = ":".join(message.date.split()[1].split(":")[:2])
        clear_time_date = re.sub(r'[<>:"/\\|?*]', '-', clear_date + '_' + clear_time)
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', message.subject + '_' + clear_time_date) # change the file name to a safe name so you can save it on your pc
        email_id = user_email.id
        
        os.makedirs(invoices_folder + '\\' + str(email_id), exist_ok=True)  # exist_ok=True prevents errors if the folder already exists

        file_path = invoices_folder + '\\' + str(email_id) + '\\' + safe_filename + '.pdf' # set the new pdf name

        if os.path.exists(file_path): # checks if the pdf name already exists in the directory, if not continue
            print('All invoices are saved!')
            break
        else: 
            if any(word in message.subject for word in ['חשבונית', 'invoice', 'receipt', 'קבלה', 'bill']): # if the email subject contains these words continue 
                if message.attachments: # if the mail contains pdf/image/file save the attachments
                    for attm in message.attachments:
                        attm.save(filepath=file_path) # save the file
                        print('Saved attachment of : ' + safe_filename)
                                                
                        new_invoice = Invoices(
                            email_id= email_id,
                            sender=message.sender,      
                            amount= None,
                            date = clear_date,
                            file_path = file_path
                        )
                        db.session.add(new_invoice)
       
                elif message.html: # if the email doesn't contain attachments, save the mail content as pdf
                    html_content = message.html
                    try:
                        HTML(string=html_content).write_pdf(file_path, optimize_size=False)# Convert the HTML content to PDF and save it
                        print('Saved: ' + safe_filename + " content as pdf")
                        print(message.sender)

                    except Exception:
                        print('Cannot save this mail as html: ' + safe_filename)
                    else:
                        continue
                            
                db.session.commit()  # Commit the transaction

            else:
                continue
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))


# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('accounts/login.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('accounts/login.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500

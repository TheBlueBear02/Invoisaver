# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound
from apps.authentication.models import *
from flask_login import (
    current_user,
    login_user,
    logout_user
)
def get_invoices():
    user_email = Emails.query.filter_by(user_id=current_user.get_id()).first()
    invoices = Invoices.query.filter_by(email_id=user_email.id)
    return invoices

@blueprint.route('/index')
@login_required
def index():
    invoices = []
    invoices_count = 0
    try:
        invoices = get_invoices()
        invoices_count = invoices.count()
    except:
        print(f"no invoices")
    return render_template('home/index.html', segment='index', invoices = invoices, invoices_count= invoices_count)


@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500





# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None

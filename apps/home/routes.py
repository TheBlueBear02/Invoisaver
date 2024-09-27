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

@blueprint.route('/index')
@login_required
def index():
    invoices = []
    invoices_count = 0
    user_email = None
    try:
        # get the invoices data to present in dashboard
        user_email = Emails.query.filter_by(user_id=current_user.get_id()).first()
        invoices = Invoices.query.filter_by(email_id=user_email.id)
        invoices_count = invoices.count()
    
        # get the invoices data to present in dashboard
        suppliers = Suppliers.query.filter_by(user_id=current_user.get_id(),)
        suppliers_counter = suppliers.count()
        invoices_per_supplier = []
        i = 0
        for supplier in suppliers:
            supplier_invoices = Invoices.query.filter_by(email_id=user_email.id,supplier=supplier.id)
            invoices_per_supplier[i] = supplier_invoices.count()
    except:
        print(f"no invoices")
    return render_template('home/index.html', segment='index', invoices = invoices, invoices_count= invoices_count, suppliers=suppliers,supplier_count=suppliers_counter,invoices_per_supplier=invoices_per_supplier)


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

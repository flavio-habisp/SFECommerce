# -*- coding: utf-8 -*-

import re
from flask import Blueprint, g, session, request, abort, Response

import json

from sfec.models.user import *
from sfec.models.views import *
from sfec.database.runtime import get_default_store
from sfec.controllers.decorators import *
from time import mktime

user_api = Blueprint('user_api', __name__)

def is_email_address_valid(email):
    """Validate the email address using a regex."""
    if not re.match("^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$", email):
        return False
    return True

@user_api.route("/register", methods=['POST'])
def register():
	"""Register a new user."""
	if not is_email_address_valid(request.form['email']):
		abort(403)

	store = get_default_store()
	# Default user is customer, an admin must change the user to staff member (admin or vendor)
	found = store.find(User, User.email == request.form['email']).one()
	if found is not None:
		abort(403)
	new_customer = Customer()
	user = User()
	user.name = request.form['name']
	user.email = request.form['email']
	user.set_password(request.form['password'])
	store = get_default_store()
	new_customer.user = user
	store.add(new_customer)
	store.commit()
	session['user'] = user.id
	return user.json()



@user_api.route('/login', methods=['POST'])
def login():
	"""Log the user in."""
	store = get_default_store()
	user = User.authenticate(store, request.form['email'],request.form['password'])
	if user:
		session['user'] = user.id
		return user.json()
	abort(403)


@user_api.route('/login_check', methods=['GET'])
def login_check():
    user_id = session.pop('user', None)
    store = get_default_store()
    user = store.find(User, id=user_id).one()
    if user:
        return user.json()
    abort(403)


@user_api.route('/logout', methods=['GET'])
@require_login
def logout():
	""" Logout the user """
	session.pop('user',None)
	return "True"

@user_api.route('/users/<int:user_id>/set_vendor', methods=['GET'])
@require_admin
def set_vendor(user_id):
	""" Turn an user into a Vendor """
	store = get_default_store()
	user = store.find(User, User.id == user_id).one()
	if user is None:
		abort(404)
	user = store.find(VendorView, VendorView.id == user_id).one()
	if user is not None:
		return "Already Vendor!"
	vendor = Vendor()
	vendor.user = user
	store.add(vendor)
	return "True"

@user_api.route('/users/<int:user_id>/set_admin', methods=['GET'])
@require_admin
def set_admin(user_id):
	""" Turn an user into a Admin """
	store = get_default_store()
	user = store.find(User, User.id == user_id).one()
	if user is None:
		abort(404)
	user = store.find(AdminView, AdminView.id == user_id).one()
	if user is not None:
		return "Already Admin!"
	admin = Admin()
	admin.user = user
	store.add(admin)
	return "True"

@user_api.route('/me', methods=['GET'])
@require_login
def me():
	""" Get data of the logged user """
	store = get_default_store()
	user_id = session['user']
	user = store.find(User, User.id == user_id).one()
	if user is None:
		abort(404)
	userd = {'id': user.id,
        'name': user.name,
        'email': user.email,
        'birth_date': int(mktime(user.birth_date.timetuple()) * 1000),
        'register_date': int(mktime(user.register_date.timetuple()) * 1000)}
	json_str = json.dumps(userd)
	return Response(json_str, mimetype='application/json')

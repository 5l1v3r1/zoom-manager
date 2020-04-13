#!/usr/bin/env python3

from os import environ
from http import cookies
import datetime
import config
from hashlib import sha256
import database
import request
from datetime import datetime
import forms

def is_authenticated():
    session = get_session()
    return session is not None

def auth_test():
    response = request.Response()
    if is_authenticated():
        response.data = "Logged in"
    else:
        response.data = "Not logged in"
    response.send()

def login():
    response = request.Response()

    data = forms.get_form_data()
    if "username" not in data or "password" not in data:
        login_failure(response, "bad form data")

    username = data["username"]
    password = data["password"]

    user = database.get_user_by_name(username)
    if not user:
        login_failure(response, "no matching user")
        return

    correct = user["password"]
    check = hash(password)

    if not check == correct:
        login_failure(response, "wrong password")
        return

    new_session(response, user)

def new_session(response, user, message="success"):
    new_session_id = hash(str(datetime.now()) + user["username"])
    session = database.new_session(user["id"], new_session_id)
    set_cookie(response, "session", new_session_id)
    response.data = message
    response.send()

def get_session():
    cookie = get_cookie()
    if "session" not in cookie:
        return None
    session_id = cookie["session"].value
    session = database.get_session(session_id)
    return session

def login_failure(response, message="failure"):
    response.status = 401
    response.data = message
    response.send()

def change_password():
    response = request.Response()
    data = forms.get_form_data()
    if "old" not in data or "new" not in data:
        login_failure(response, "old or new is undefined")
        return
    
    session = get_session()
    user_id = session["user_id"]
    user = database.get_user_by_id(user_id)
    old_pw = user["password"]
    old_pw_check = hash(data["old"])

    if old_pw != old_pw_check:
        login_failure(response, data["old"])
        return

    new_pw = hash(data["new"])
    database.update_password(user_id, new_pw)

    response.data = "success"
    response.send()

def get_cookie():
    cookie = cookies.SimpleCookie()
    if "HTTP_COOKIE" in environ:
        cookie.load(environ["HTTP_COOKIE"])
    return cookie

def set_cookie(response, name, value):
    cookie = cookies.SimpleCookie()
    cookie[name] = value
    cookie[name]["secure"] = True
    response.add_header(cookie)

def hash(text):
    salted = config.db_salt + text
    return sha256(salted.encode("utf-8")).hexdigest()


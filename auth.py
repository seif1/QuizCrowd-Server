from flask import Blueprint, render_template, request
from . import db

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return 'Login'

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        print("A")

@auth.route('/logout')
def logout():
    return 'Logout'
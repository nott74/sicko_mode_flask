import functools
import hashlib

import mysql.connector
from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from mysql.connector import errorcode
from mysql.connector.errors import IntegrityError, DatabaseError

from sicko_mode.database import get_connection
from sicko_mode.models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))

        user_row = cursor.fetchone()
        if user_row is not None:
            # Create a user object using the constructor
            g.user = User(*user_row)
        else:
            g.user = None


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        connection = get_connection()
        cursor = connection.cursor()
        error = None

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        columns = [column[0] for column in cursor.description]

        if user is None:
            error = "Incorrect username."
        else:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if hashed_password != user[columns.index('password')]:
                error = "Incorrect password."

        if error is None:
            # store the user id in a new session and return to the index
            session['logedin'] = True
            session['username'] = user[columns.index('username')]
            session['user_id'] = user[columns.index('user_id')]
            session['rgpd'] = user[columns.index('rgpd')]
            if session['rgpd'] == '1':
                return redirect(url_for('clinic.home'))
            else:
                return redirect(url_for('clinic.home_rgpd'))

        flash(error)

        connection.commit()
        cursor.close()
        connection.close()

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("index"))


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        birth_date = request.form['birth_date']
        tlm = request.form['tlm']
        nif = request.form['nif']

        conn = get_connection()
        cursor = conn.cursor()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not birth_date:
            error = 'Password is required.'

        if error is None:
            try:
                cursor.execute(
                    "INSERT INTO users (username, password, first_name, last_name, birth_date, tlm, nif)" \
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (username, hashlib.sha256(password.encode()).hexdigest(), first_name, last_name, birth_date, tlm, nif),
                )
                conn.commit()
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_DUP_ENTRY:
                    error = f"User {username} is already registered."
                elif isinstance(err, IntegrityError):
                    # Handle integrity error
                    error = f"An error occurred: {err}"
                elif isinstance(err, DatabaseError):
                    # Handle other database errors
                    error = f"An error occurred: {err}"

                flash(error)
                return render_template('auth/register.html')

            return render_template('auth/login.html')
        else:
            return render_template('auth/register.html')

    return render_template('auth/register.html')
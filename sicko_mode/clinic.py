import mysql.connector
from flask import render_template, session, redirect, url_for, Blueprint, request

from sicko_mode.database import get_connection
from sicko_mode.models import User

bp = Blueprint("clinic", __name__, url_prefix="/clinic")


@bp.route("/home")
def home():
    if session['rgpd'] and session['rgpd'] == '1':
        return redirect(url_for('clinic.home_greeting'))
    else:
        return render_template('home_rgpd.html', username=session['username'])


@bp.route("/homegreeting")
def home_greeting():
    rendered_greeting = render_template('greeting.html')
    return render_template('home.html', content=rendered_greeting)


@bp.route("/home_rgpd")
def home_rgpd():
    return render_template('home_rgpd.html', username=session['username'])


@bp.route('/accept_rgpd')
def accept_rgpd():
    # Get a cursor object to execute SQL queries
    connection = get_connection()
    cursor = connection.cursor()

    username = session.get('username')

    if username is None:
        return "Error: no username in session"
    # Update the users table to set rgpd to 1
    sql = "UPDATE users SET rgpd = '1' WHERE username = %s"
    val = (username,)
    try:
        cursor.execute(sql, val)

        # Commit the changes to the database and close the cursor and connection
        connection.commit()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))

    cursor.close()
    connection.close()

    return redirect(url_for('clinic.home_greeting'))


@bp.route('/profile')
def profile():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users WHERE username = %s", (session['username'],))

    user_row = cursor.fetchone()
    if user_row is not None:
        # Create a user object using the constructor
        user = User(*user_row)

    cursor.close()
    connection.close()

    rendered_profile = render_template('profile.html', user=user)
    return render_template('home.html', content=rendered_profile)

@bp.route('/profile/update/<string:username>', methods=['POST'])
def update_profile(username):
    connection = get_connection()
    cursor = connection.cursor()

    first_name = request.form['first_name']
    last_name = request.form['last_name']
    birth_date = request.form['birth_date']
    tlm = request.form['tlm']
    nif = request.form['nif']

    sql = "UPDATE users SET first_name=%s, last_name=%s, birth_date=%s, tlm=%s, nif=%s WHERE username = %s"
    val = (first_name, last_name, birth_date, tlm, nif, username)

    try:
        cursor.execute(sql, val)
        connection.commit()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        return "Error: Failed to add prescription"

    cursor.close()
    connection.close()

    return redirect(url_for('clinic.profile'))







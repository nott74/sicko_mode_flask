import mysql.connector
from flask import render_template, session, redirect, url_for, Blueprint

from sicko_mode.database import get_connection
from sicko_mode.models.pacient import Pacient
from sicko_mode.models.user import User

bp = Blueprint("clinic", __name__, url_prefix="/clinic")


@bp.route("/home")
def home():
    if session['rgpd'] == '1':
        return redirect(url_for('clinic.home_greeting'))
    else:
        return render_template('home_rgpd.html', username=session['username'])


@bp.route("/homegreeting")
def home_greeting():
    rendered_greeting = render_template('greeting.html')
    return render_template('home.html', content=rendered_greeting, username=session['username'])


@bp.route("/home_rgpd")
def home_rgpd():
    return render_template('home_rgpd.html', username=session['username'])


@bp.route('/pacients')
def pacients():
    connection = get_connection()
    cursor = connection.cursor()

    query = ("SELECT "
             + "  pacients.id as id, "
             + "  pacients.first_name as first_name, "
             + "  pacients.last_name as last_name, "
             + "  pacients.care_taker as care_taker, "
             + "  pacients.doctor_id as doctor_id, "
             + "  pacients.birth_date as birth_date, "
             + "  CONCAT(doctors.first_name, ' ' , doctors.last_name) as doctor_name "
             + "FROM pacients "
             + "INNER JOIN doctors on doctors.id = pacients.doctor_id")

    cursor.execute(query)

    pacient_list = []

    for id, first_name, last_name, care_taker, doctor_id, birth_date, doctor_name in cursor.fetchall():
        pacient_list.append(Pacient(id, first_name, last_name, care_taker, doctor_id, birth_date, doctor_name))

    cursor.close()
    connection.close()

    rendered_pacients = render_template('pacients.html', pacients=pacient_list)
    return render_template('home.html', content=rendered_pacients)


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

    return redirect(url_for('login'))


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

import hashlib

from flask import Flask, render_template, request, session, redirect, url_for
from database import get_connection
from models import Pacient
import mysql.connector

app = Flask(__name__)
app.secret_key = "sicko secret key"


@app.route('/')
def hello_world():
    return render_template("index.html")


@app.route("/home")
def home():
    if session['rgpd'] == '1':
        return redirect(url_for('home_greeting'))
    else:
        return render_template('homeRgpd.html', username=session['username'])


@app.route("/homegreeting")
def home_greeting():
    rendered_greeting = render_template('greeting.html')
    return render_template('home.html', content=rendered_greeting, username=session['username'])


@app.route("/homeRgpd")
def homeRgpd():
    return render_template('homeRgpd.html', username=session['username'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    connection = get_connection()
    cursor = connection.cursor()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Retrieve the user from the database
        cursor.execute('SELECT * FROM users WHERE username=%s', (username,))
        record = cursor.fetchone()
        columns = [column[0] for column in cursor.description]

        if record:
            # Check the entered password against the stored password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if hashed_password == record[columns.index('password')]:
                session['logedin'] = True
                session['username'] = record[columns.index('username')]
                session['rgpd'] = record[columns.index('rgpd')]
                if session['rgpd'] == '1':
                    return redirect(url_for('home'))
                else:
                    return redirect(url_for('homeRgpd'))
            else:
                msg = 'Incorrect username or password. Try again.'
        else:
            msg = 'Incorrect username or password. Try again.'

        connection.commit()
        cursor.close()
        connection.close()

    return render_template('index.html', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/pacients')
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


@app.route('/acceptRGPD')
def acceptRGPD():
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


if __name__ == '__main__':
    app.run()

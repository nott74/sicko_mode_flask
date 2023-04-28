from flask import Flask, render_template, send_file, request, session, redirect, url_for
from database import get_connection
import mysql.connector

app = Flask(__name__)
app.secret_key = "sicko secret key"


@app.route('/')
def hello_world():
    return render_template("index.html")


@app.route("/home")
def home():
    if session['rgpd'] == '1':
        return render_template('home.html', username=session['username'])
    else:
        return render_template('homeRgpd.html', username=session['username'])


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
        cursor.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
        record = cursor.fetchone()
        columns = [column[0] for column in cursor.description]
        if record:
            session['logedin'] = True
            session['username'] = record[columns.index('username')]
            session['rgpd'] = record[columns.index('rgpd')]
            if session['rgpd'] == '1':
                return redirect(url_for('home'))
            else:
                return redirect(url_for('homeRgpd'))
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

from flask import Flask, render_template, send_file, request, session, redirect, url_for
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
    connection = mysql.connector.connect(host='localhost', port='3306', database='sicko_db', user='root',
                                         password='p.142230561')

    cursor = connection.cursor()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute('SELECT * FROM USERS WHERE username=%s AND password=%s', (username, password))
        record = cursor.fetchone()
        if record:
            session['logedin'] = True
            session['username'] = record[1]
            session['rgpd'] = record[3]
            if record[3] == '1':
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
    # Connect to the MySQL database
    mydb = mysql.connector.connect(host='localhost',
                                   port='3306',
                                   database='sicko_db',
                                   user='root',
                                   password='p.142230561')

    # Get a cursor object to execute SQL queries
    cursor = mydb.cursor()

    username = session.get('username')

    if username is None:
        return "Error: no username in session"
    # Update the users table to set rgpd to 1
    sql = "UPDATE users SET rgpd = 1 WHERE username = %s"
    val = (username,)
    cursor.execute(sql, val)

    # Commit the changes to the database and close the cursor and connection
    mydb.commit()
    cursor.close()
    mydb.close()

    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run()

import mysql.connector
from flask import render_template, session, redirect, url_for, Blueprint, request

from sicko_mode.database import get_connection
from sicko_mode.models.doctor import Doctor
from sicko_mode.models.medication import Medication
from sicko_mode.models.pacient import Pacient
from sicko_mode.models.prescription import Prescription
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


@bp.route('/prescriptions')
def prescriptions():
    connection = get_connection()
    cursor = connection.cursor()

    query = ("SELECT "
             " CONCAT('P' , prescriptions.id) as prescription_id, "
             " CONCAT(pacients.first_name, ' ' , pacients.last_name) as patient_name, "
             " CONCAT(users.first_name, ' ' , users.last_name) as doctor_name, "
             " medication.name as medication, "
             " prescriptions.dosage as dosage, "
             " prescriptions.instructions as instructions, "
             " prescriptions.prescription_date as prescription_date "
             " FROM "
             " prescriptions "
             " INNER JOIN pacients on "
             " pacients.id = prescriptions.patient_id "
             " INNER JOIN users on "
             " users.user_id = prescriptions.prescribing_doctor_id "
             " INNER JOIN medication on "
             " medication.id = prescriptions.medication; ")

    cursor.execute(query)

    prescriptions_list = []

    for prescription_id, patient_name, doctor_name, medication, dosage, instructions, prescription_date in cursor.fetchall():
        prescriptions_list.append(
            Prescription(prescription_id, patient_name, doctor_name, medication, dosage, instructions,
                         prescription_date))

    # Query the patient names for the select field
    patients_query = """
                SELECT id, pacients.first_name, pacients.last_name, pacients.care_taker, doctor_id, pacients.birth_date, CONCAT(users.first_name, ' ', users.last_name) as doctor_name
                FROM pacients
                INNER JOIN users ON users.user_id = pacients.doctor_id
            """

    cursor.execute(patients_query)
    patients = []

    for row in cursor.fetchall():
        patient_id, first_name, last_name, care_taker, doctor_id, birth_date, doctor_name = row
        patient = Pacient(patient_id, first_name, last_name, care_taker, doctor_id, birth_date, doctor_name)
        patients.append(patient)

    # Query the doctor names for the select field
    doctors_query = "SELECT user_id, first_name, last_name FROM users WHERE user_type='Doctor'"

    cursor.execute(doctors_query)
    doctors = []

    for row in cursor.fetchall():
        doctor_id, first_name, last_name = row
        doctor = Doctor(doctor_id, first_name, last_name, "")
        doctors.append(doctor)

    # Query the medication names for the select field
    medications_query = "SELECT id, name as medication, description FROM medication"
    cursor.execute(medications_query)
    medications = []

    for row in cursor.fetchall():
        medication_id, medication_name, medication_description = row
        medication = Medication(medication_id, medication_name, medication_description)
        medications.append(medication)

    cursor.close()
    connection.close()

    rendered_prescriptions = render_template('prescriptions.html', prescriptions=prescriptions_list, patients=patients, doctors=doctors, medications=medications)
    return render_template('home.html', content=rendered_prescriptions)


@bp.route('/add_prescription', methods=['POST'])
def add_prescription():
    connection = get_connection()
    cursor = connection.cursor()

    patient_id = request.form['patient_name']
    doctor_id = request.form['doctor_name']
    medication_id = request.form['medication']
    dosage = request.form['dosage']
    instructions = request.form['instructions']
    prescription_date = request.form['prescription_date']

    sql = "INSERT INTO prescriptions (patient_id, prescribing_doctor_id, medication, dosage, instructions, prescription_date) " \
          "VALUES (%s, %s, %s, %s, %s, %s)"
    val = (patient_id, doctor_id, medication_id, dosage, instructions, prescription_date)

    try:
        cursor.execute(sql, val)
        connection.commit()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        return "Error: Failed to add prescription"

    cursor.close()
    connection.close()

    return redirect(url_for('clinic.prescriptions'))

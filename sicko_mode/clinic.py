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


@bp.route('/patients')
def patients():
    connection = get_connection()
    cursor = connection.cursor()

    query = ("SELECT "
             + "  patients.id as id, "
             + "  patients.first_name as first_name, "
             + "  patients.last_name as last_name, "
             + "  patients.care_taker as care_taker, "
             + "  patients.doctor_id as doctor_id, "
             + "  patients.birth_date as birth_date, "
             + "  CONCAT(users.first_name, ' ' , users.last_name) as doctor_name,"
             + "  patients.address as address, "
             + "  patients.phone_number as phone_number, "
             + "  patients.email as email, "
             + "  patients.gender as gender, "
             + "  patients.emergency_contact_name as emergency_contact_name, "
             + "  patients.emergency_contact_number as emergency_contact_number "
             + "FROM patients "
             + "INNER JOIN users on users.user_id = patients.doctor_id "
             + " WHERE  patients.rmv = 0 ")

    cursor.execute(query)

    pacient_list = []

    for id, first_name, last_name, care_taker, doctor_id, birth_date, doctor_name, address, phone_number, email, gender, emergency_contact_name, emergency_contact_number in cursor.fetchall():
        pacient_list.append(Pacient(id, first_name, last_name, care_taker, doctor_id, birth_date, doctor_name, address, phone_number, email, gender, emergency_contact_name, emergency_contact_number))

        # Query the doctor names for the select field
        doctors_query = "SELECT user_id, first_name, last_name FROM users WHERE user_type='Doctor' and rmv = '0'"

        cursor.execute(doctors_query)
        doctors = []

        for row in cursor.fetchall():
            doctor_id, first_name, last_name = row
            doctor = Doctor(doctor_id, first_name, last_name, "")
            doctors.append(doctor)

    cursor.close()
    connection.close()

    rendered_patients = render_template('patients.html', patients=pacient_list, doctors=doctors)
    return render_template('home.html', content=rendered_patients)


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
             " prescriptions.id as prescription_id, "
             " CONCAT(patients.first_name, ' ' , patients.last_name) as patient_name, "
             " CONCAT(users.first_name, ' ' , users.last_name) as doctor_name, "
             " medication.name as medication, "
             " prescriptions.dosage as dosage, "
             " prescriptions.instructions as instructions, "
             " prescriptions.prescription_date as prescription_date "
             " FROM "
             " prescriptions "
             " INNER JOIN patients on "
             " patients.id = prescriptions.patient_id "
             " INNER JOIN users on "
             " users.user_id = prescriptions.prescribing_doctor_id "
             " INNER JOIN medication on "
             " medication.id = prescriptions.medication "
             " WHERE prescriptions.rmv = 0; ")

    cursor.execute(query)

    prescriptions_list = []

    for prescription_id, patient_name, doctor_name, medication, dosage, instructions, prescription_date in cursor.fetchall():
        prescriptions_list.append(
            Prescription(prescription_id, patient_name, doctor_name, medication, dosage, instructions,
                         prescription_date))

    # Query the patient names for the select field
    patients_query = """
                SELECT id, patients.first_name, patients.last_name, patients.care_taker, doctor_id, patients.birth_date, CONCAT(users.first_name, ' ', users.last_name) as doctor_name
                FROM patients
                INNER JOIN users ON users.user_id = patients.doctor_id
                WHERE patients.rmv = 0
            """

    cursor.execute(patients_query)
    patients = []

    for row in cursor.fetchall():
        patient_id, first_name, last_name, care_taker, doctor_id, birth_date, doctor_name = row
        patient = Pacient(patient_id, first_name, last_name, care_taker, doctor_id, birth_date, doctor_name, "", "", "", "", "", "")
        patients.append(patient)

    # Query the doctor names for the select field
    doctors_query = "SELECT user_id, first_name, last_name FROM users WHERE user_type='Doctor' and rmv = '0'"

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


@bp.route('/prescriptions/delete/<int:prescription_id>', methods=['POST'])
def delete_prescription(prescription_id):
    connection = get_connection()
    cursor = connection.cursor()

    # Update the 'rmv' column to 1 for the given prescription_id
    query = "UPDATE prescriptions SET rmv = 1 WHERE id = %s"
    cursor.execute(query, (prescription_id,))
    connection.commit()

    cursor.close()
    connection.close()

    # Redirect to the prescriptions page or any other desired page
    return redirect(url_for('clinic.prescriptions'))


@bp.route('/prescriptions/details/<int:prescription_id>')
def prescription_details(prescription_id):
    connection = get_connection()
    cursor = connection.cursor()

    # Retrieve the prescription details for the given prescription_id
    query = ("SELECT "
             " CONCAT('P', prescriptions.id) as prescription_id, "
             " CONCAT(patients.first_name, ' ', patients.last_name) as patient_name, "
             " CONCAT(users.first_name, ' ', users.last_name) as doctor_name, "
             " medication.name as medication, "
             " prescriptions.dosage as dosage, "
             " prescriptions.instructions as instructions, "
             " prescriptions.prescription_date as prescription_date "
             " FROM "
             " prescriptions "
             " INNER JOIN patients on "
             " patients.id = prescriptions.patient_id "
             " INNER JOIN users on "
             " users.user_id = prescriptions.prescribing_doctor_id "
             " INNER JOIN medication on "
             " medication.id = prescriptions.medication "
             " WHERE prescriptions.id = %s")
    cursor.execute(query, (prescription_id,))
    prescription_data = cursor.fetchone()

    cursor.close()
    connection.close()

    if prescription_data:
        # Create a Prescription object using the retrieved data
        prescription = Prescription(
            prescription_data[0],
            prescription_data[1],
            prescription_data[2],
            prescription_data[3],
            prescription_data[4],
            prescription_data[5],
            prescription_data[6]
        )

        # rendered_prescriptions = render_template('prescription_details.html', prescription=prescription)
        return render_template('prescription_details.html', prescription=prescription)
    else:
        # Prescription not found, handle accordingly (e.g., redirect or display an error message)
        return "Prescription not found"


@bp.route('/add_patient', methods=['POST'])
def add_patient ():
    connection = get_connection()
    cursor = connection.cursor()

    first_name = request.form['first_name']
    last_name = request.form['last_name']
    doctor_id = request.form['doctor_name']
    phone_number = request.form['phone_number']
    email = request.form['email']
    gender = request.form['gender']
    emergency_name = request.form['emergency_name']
    emergency_contact = request.form['emergency_contact']
    address = request.form['address']
    birth_date = request.form['birth_date']

    sql = "INSERT INTO patients (first_name, last_name, care_taker, doctor_id, birth_date, address, phone_number, email, gender, occupation, emergency_contact_name, emergency_contact_number) " \
          "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    val = (first_name, last_name, -1, doctor_id, birth_date, address, phone_number, email, gender, "", emergency_name, emergency_contact)

    try:
        cursor.execute(sql, val)
        connection.commit()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        return "Error: Failed to add patient"

    cursor.close()
    connection.close()

    return redirect(url_for('clinic.patients'))


@bp.route('/patients/delete/<int:patient_id>', methods=['POST'])
def delete_patient(patient_id):
    connection = get_connection()
    cursor = connection.cursor()

    # Update the 'rmv' column to 1 for the given patient_id
    query = "UPDATE patients SET rmv = 1 WHERE id = %s"
    cursor.execute(query, (patient_id,))
    connection.commit()

    cursor.close()
    connection.close()

    # Redirect to the prescriptions page or any other desired page
    return redirect(url_for('clinic.patients'))
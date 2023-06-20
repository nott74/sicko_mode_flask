import mysql.connector
from flask import render_template, redirect, url_for, Blueprint, request, g

from sicko_mode.database import get_connection
from sicko_mode.models import Patient, Doctor, Medication, Prescription

bp = Blueprint("prescriptions", __name__, url_prefix="/clinic/prescriptions")


@bp.route('/')
def prescription_list():
    connection = get_connection()
    cursor = connection.cursor()

    if g.user.user_type == 2:
        aux_where = " AND appointments.doctor_id = %s"
        values = (g.user.user_id,)
    elif g.user.user_type == 3:
        aux_where = " AND patients.care_taker = %s"
        values = (g.user.user_id,)
    else:
        aux_where = ""
        values = ()

    query = ("SELECT "
             " prescriptions.id as prescription_id, "
             " CONCAT(patients.first_name, ' ' , patients.last_name) as patient_name, "
             " CONCAT(users.first_name, ' ' , users.last_name) as doctor_name, "
             " medication.name as medication, "
             " prescriptions.dosage as dosage, "
             " prescriptions.instructions as instructions, "
             " appointments.appointment_date as prescription_date "
             " FROM "
             " prescriptions "
             " INNER JOIN patients on "
             " patients.id = prescriptions.patient_id "
             " INNER JOIN appointments on "
             " appointments.id = prescriptions.appointment_id "
             " INNER JOIN users on "
             " users.user_id = appointments.doctor_id "
             " INNER JOIN medication on "
             " medication.id = prescriptions.medication "
             " WHERE prescriptions.rmv = 0 "
             f"{aux_where}"
             " ORDER BY prescriptions.id DESC; ")

    cursor.execute(query, values)

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
        patient = Patient(patient_id, first_name, last_name, care_taker, doctor_id, birth_date, doctor_name, "", "", "",
                          "", "", "")
        patients.append(patient)

    # Query the doctor names for the select field
    doctors_query = "SELECT user_id, first_name, last_name FROM users WHERE user_type=2 and rmv = '0'"

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

    rendered_prescriptions = render_template('prescriptions/prescriptions.html', prescriptions=prescriptions_list,
                                             patients=patients,
                                             doctors=doctors, medications=medications)
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

    sql = "INSERT INTO prescriptions (patient_id, doctor_id, medication, dosage, instructions, prescription_date) " \
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

    return redirect(url_for('prescriptions.prescription_list'))


@bp.route('/add_prescription_from_appt/<int:appointment_id>/<int:doctor_id>/<int:patient_id>', methods=['POST'])
def add_prescription_from_appt(appointment_id, doctor_id, patient_id):
    connection = get_connection()
    cursor = connection.cursor()

    medication_id = request.form['medication']
    dosage = request.form['dosage']
    instructions = request.form['instructions']
    prescription_date = request.form['prescription_date']

    sql = "INSERT INTO prescriptions (appointment_id, doctor_id, patient_id, medication, dosage, instructions, prescription_date) " \
          "VALUES (%s, %s, %s, %s, %s, %s, %s)"
    val = (appointment_id, doctor_id, patient_id, medication_id, dosage, instructions, prescription_date)

    try:
        cursor.execute(sql, val)
        connection.commit()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        return "Error: Failed to add prescription"

    cursor.close()
    connection.close()

    return redirect(url_for('appointments.appointment_details', appointment_id=appointment_id))


@bp.route('/delete/<int:prescription_id>', methods=['POST'])
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
    return redirect(url_for('prescriptions.prescription_list'))


@bp.route('/delete/<int:appointment_id>/<int:prescription_id>', methods=['POST'])
def delete_prescription_from_appt(appointment_id, prescription_id):
    connection = get_connection()
    cursor = connection.cursor()

    # Update the 'rmv' column to 1 for the given prescription_id
    query = "UPDATE prescriptions SET rmv = 1 WHERE id = %s"
    cursor.execute(query, (prescription_id,))
    connection.commit()

    cursor.close()
    connection.close()

    # Redirect to the prescriptions page or any other desired page
    return redirect(url_for('appointments.appointment_details', appointment_id=appointment_id))


@bp.route('/details/<int:prescription_id>')
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
             " appointments.appointment_date as prescription_date "
             " FROM "
             " prescriptions "
             " INNER JOIN patients on "
             " patients.id = prescriptions.patient_id "
             " INNER JOIN appointments on "
             " appointments.id = prescriptions.appointment_id "
             " INNER JOIN users on "
             " users.user_id = appointments.doctor_id "
             " INNER JOIN medication on "
             " medication.id = prescriptions.medication "
             " WHERE prescriptions.id = %s"
             " ORDER BY prescriptions.id DESC; ")
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

        rendered_prescriptions = render_template('prescriptions/prescription_details.html', prescription=prescription)
        return render_template('home.html', content=rendered_prescriptions)
    else:
        # Prescription not found, handle accordingly (e.g., redirect or display an error message)
        return "Prescription not found"

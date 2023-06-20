import os
from datetime import datetime, timedelta

import mysql.connector
from flask import render_template, session, redirect, url_for, Blueprint, request
from werkzeug.utils import secure_filename

from sicko_mode.database import get_connection
from sicko_mode.models import Patient, Doctor, Medication, Appointment

bp = Blueprint("appointments", __name__, url_prefix="/clinic/appointments")


@bp.route('/')
def appointment_list():
    connection = get_connection()
    cursor = connection.cursor()

    query = ("SELECT "
             " appointments.id as appointment_id, "
             " CONCAT(patients.first_name, ' ' , patients.last_name) as patient_name, "
             " CONCAT(users.first_name, ' ' , users.last_name) as doctor_name, "
             " appointments.appointment_date as appointment_date, "
             " appointment_states.dsc as state "
             " FROM "
             " appointments "
             " INNER JOIN patients on "
             " patients.id = appointments.patient_id "
             " INNER JOIN users on "
             " users.user_id = appointments.doctor_id"
             " INNER JOIN appointment_states ON "
             " appointment_states.id = appointments.state AND appointment_states.rmv = '0'"
             " ORDER BY appointments.id DESC; ")

    cursor.execute(query)

    appointments_list = []

    for appointment_id, patient_name, doctor_name, appointment_date, state in cursor.fetchall():
        appointments_list.append(Appointment(appointment_id, appointment_date, state, patient_name, doctor_name))

    # Query the patient names for the select field
    patients_query = """
                SELECT id, patients.first_name, patients.last_name, patients.care_taker, doctor_id, patients.birth_date, CONCAT(users.first_name, ' ', users.last_name) as doctor_name
                FROM patients
                INNER JOIN users ON users.user_id = patients.doctor_id
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

    current_datetime = datetime.now() + timedelta(days=1)
    current_datetime_str = current_datetime.strftime('%Y-%m-%dT%H:%M')

    rendered_appointments = render_template('appointments/appointments.html', appointments=appointments_list,
                                            patients=patients,
                                            doctors=doctors, current_datetime=current_datetime_str)
    return render_template('home.html', content=rendered_appointments)


@bp.route('/add_appointment', methods=['POST'])
def add_appointment():
    connection = get_connection()
    cursor = connection.cursor()

    patient_id = request.form['patient_name']
    doctor_id = request.form['doctor_name']
    observations = request.form['observations']
    appointment_date = request.form['appointment_date']

    # Handle image file upload
    if 'image_file' in request.files:
        image_file = request.files['image_file']
        if image_file.filename != '':
            # Secure the filename to prevent any malicious file execution
            filename = secure_filename(image_file.filename)
            # Set the file path to save the image
            file_directory = os.path.join(os.path.dirname(__file__), 'static/user_files')
            os.makedirs(file_directory, exist_ok=True)
            # Create the directory if it doesn't exist
            file_path = os.path.join(file_directory, filename)
            # Save the file to the file path
            image_file.save(file_path)

            image_path = os.path.join('user_files', filename).replace('\\', '/')

    sql = "INSERT INTO appointments (patient_id, doctor_id, state, observations, appointment_date, rcd_user, rcd_date, image_path) " \
          "VALUES (%s, %s, 1, %s, %s, %s, sysdate(), %s)"
    val = (patient_id, doctor_id, observations, appointment_date, session.get('user_id'), image_path)

    try:
        cursor.execute(sql, val)
        connection.commit()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        return "Error: Failed to add appointment"

    cursor.close()
    connection.close()

    return redirect(url_for('clinic.appointments'))


@bp.route('/cancel/<int:appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    connection = get_connection()
    cursor = connection.cursor()

    # Update the 'rmv' column to 1 for the given appointment_id
    query = "UPDATE appointments SET state = '4' WHERE id = %s"
    cursor.execute(query, (appointment_id,))
    connection.commit()

    cursor.close()
    connection.close()

    # Redirect to the appointments page or any other desired page
    return redirect(url_for('clinic.appointments'))


@bp.route('/details/<int:appointment_id>')
def appointment_details(appointment_id):
    connection = get_connection()
    cursor = connection.cursor()

    # Retrieve the appointment details for the given appointment_id
    query = ("SELECT "
             " appointments.id as appointment_id, "
             " CONCAT(patients.first_name, ' ' , patients.last_name) as patient_name, "
             " CONCAT(u1.first_name, ' ' , u1.last_name) as doctor_name, "
             " appointments.appointment_date as appointment_date, "
             " appointment_states.dsc as state,"
             " appointments.observations as observations,"
             " CONCAT(u2.first_name, ' ' , u2.last_name) as record_user_name,"
             " appointments.rcd_date as record_date,"
             " appointments.image_path as image_file"
             " FROM "
             " appointments "
             " INNER JOIN patients on "
             " patients.id = appointments.patient_id "
             " INNER JOIN users u1 on "
             " u1.user_id = appointments.doctor_id"
             " INNER JOIN users u2 on "
             " u2.user_id = appointments.rcd_user"
             " INNER JOIN appointment_states ON "
             " appointment_states.id = appointments.state AND appointment_states.rmv = '0' "
             " WHERE appointments.id = %s;")

    cursor.execute(query, (appointment_id,))
    data = cursor.fetchone()
    columns = [column[0] for column in cursor.description]

    if data is not None:
        # Create an Appointment object using the retrieved data
        appointment = Appointment(data[columns.index('appointment_id')],
                                  data[columns.index('appointment_date')],
                                  data[columns.index('state')],
                                  data[columns.index('doctor_name')],
                                  data[columns.index('patient_name')],
                                  data[columns.index('observations')],
                                  data[columns.index('record_user_name')],
                                  data[columns.index('record_date')],
                                  data[columns.index('image_file')]
                                  )

        cursor.close()
        connection.close()

        current_datetime = datetime.now() + timedelta(days=1)
        current_datetime_str = current_datetime.strftime('%Y-%m-%dT%H:%M')

        rendered_appointment = render_template('appointments/appointment_details.html', appointment=appointment,
                                               current_datetime=current_datetime_str)
        return render_template('home.html', content=rendered_appointment)
    else:
        # Appointment not found, handle accordingly (e.g., redirect or display an error message)
        return "Appointment not found"

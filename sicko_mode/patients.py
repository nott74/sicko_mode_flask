import mysql.connector
from flask import render_template, redirect, url_for, Blueprint, request, g

from sicko_mode.database import get_connection
from sicko_mode.models import Patient, Doctor

bp = Blueprint("patients", __name__, url_prefix="/clinic/patients")


@bp.route('/')
def patient_list():
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
             "  patients.id as id, "
             "  patients.first_name as first_name, "
             "  patients.last_name as last_name, "
             "  patients.care_taker as care_taker, "
             "  patients.doctor_id as doctor_id, "
             "  patients.birth_date as birth_date, "
             "  CONCAT(users.first_name, ' ' , users.last_name) as doctor_name,"
             "  patients.address as address, "
             "  patients.phone_number as phone_number, "
             "  patients.email as email, "
             "  patients.gender as gender, "
             "  patients.emergency_contact_name as emergency_contact_name, "
             "  patients.emergency_contact_number as emergency_contact_number "
             "  FROM patients "
             "  INNER JOIN users on users.user_id = patients.doctor_id "
             "  WHERE patients.rmv = 0 "
             f"{aux_where}"
             "  ORDER BY patients.id DESC; ")

    cursor.execute(query, values)

    patient_list = []

    for id, first_name, last_name, care_taker, doctor_id, birth_date, doctor_name, address, phone_number, email, gender, emergency_contact_name, emergency_contact_number in cursor.fetchall():
        patient_list.append(
            Patient(id, first_name, last_name, care_taker, doctor_id, birth_date, doctor_name, address, phone_number,
                    email, gender, emergency_contact_name, emergency_contact_number))

    # Query the doctor names for the select field
    doctors_query = "SELECT user_id, first_name, last_name FROM users WHERE user_type=2 and rmv = '0'"

    cursor.execute(doctors_query)
    doctors = []

    for row in cursor.fetchall():
        doctor_id, first_name, last_name = row
        doctor = Doctor(doctor_id, first_name, last_name, "")
        doctors.append(doctor)

    cursor.close()
    connection.close()

    rendered_patients = render_template('patients.html', patients=patient_list, doctors=doctors)
    return render_template('home.html', content=rendered_patients)


@bp.route('/add_patient', methods=['POST'])
def add_patient():
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
    val = (first_name, last_name, -1, doctor_id, birth_date, address, phone_number, email, gender, "", emergency_name,
           emergency_contact)

    try:
        cursor.execute(sql, val)
        connection.commit()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        return "Error: Failed to add patient"

    cursor.close()
    connection.close()

    return redirect(url_for('clinic.patients'))


@bp.route('/delete/<int:patient_id>', methods=['POST'])
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

class Appointment:
    def __init__(self, appointment_id, appointment_date, state, doctor_name, patient_name, observations=None, rcd_user=None, rcd_date=None, image_file=None):
        self.appointment_id = appointment_id
        self.appointment_date = appointment_date
        self.state = state
        self.doctor_name = doctor_name
        self.patient_name = patient_name
        self.observations = observations
        self.rcd_user = rcd_user
        self.rcd_date = rcd_date
        self.image_file = image_file

class Prescription:
    def __init__(self, prescription_id, patient_name, doctor_name, medication, dosage, instructions, prescription_date):
        self.prescription_id = prescription_id
        self.patient_name = patient_name
        self.doctor_name = doctor_name
        self.medication = medication
        self.dosage = dosage
        self.instructions = instructions
        self.prescription_date = prescription_date
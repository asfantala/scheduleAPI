import json
import os
from datetime import datetime, timedelta

# Path to appointments JSON file
APPOINTMENTS_FILE = "appointments.json"

# Define daily time slots (9:00 AM - 6:00 PM, 30-minute slots, 12:00-13:00 lunch break)
DAILY_TIME_SLOTS = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30"]

# Holidays (can be customized - add specific dates here like "2026-01-01" for New Year)
HOLIDAYS = ["2026-01-01", "2026-07-20"]  # Example dates

def generate_schedule(days_ahead=90):
    """
    Generate schedule for workdays (Sunday-Thursday)
    Fridays and Saturdays are holidays
    """
    schedule = {}
    today = datetime.now().date()
    
    for i in range(days_ahead):
        date = today + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        
        # weekday(): Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6
        # We want: Sunday-Thursday as workdays (weekday 6, 0, 1, 2, 3)
        # Holidays: Friday=4, Saturday=5
        is_workday = date.weekday() not in [4, 5]  # Not Friday or Saturday
        is_holiday = date_str in HOLIDAYS
        
        if is_workday and not is_holiday:
            schedule[date_str] = DAILY_TIME_SLOTS.copy()
    
    return schedule

# Generate schedule automatically
SCHEDULE = generate_schedule()

# In-memory storage for appointments (with sample data)
APPOINTMENTS = {
    "sample-appt-001": {
        "service": "Dental Cleaning",
        "patient_name": "Sarah Johnson",
        "phone": "0791234567",
        "email": "sarah.j@example.com",
        "appointment_date": "2026-01-20",
        "time": "09:00",
        "insurance_provider": "BlueCross",
        "notes": "Regular checkup"
    },
    "sample-appt-002": {
        "service": "Root Canal",
        "patient_name": "Ahmed Ali",
        "phone": "0795555123",
        "email": "ahmed@example.com",
        "appointment_date": "2026-01-20",
        "time": "14:00",
        "insurance_provider": "HealthPlus",
        "notes": "Follow-up appointment"
    },
    "sample-appt-003": {
        "service": "Teeth Whitening",
        "patient_name": "Layla Hassan",
        "phone": "0797777888",
        "email": "layla.h@example.com",
        "appointment_date": "2026-01-21",
        "time": "10:00",
        "insurance_provider": "No Insurance",
        "notes": "First visit"
    },
    "sample-appt-004": {
        "service": "Filling",
        "patient_name": "Mohammad Khalil",
        "phone": "0798881234",
        "email": "mohammad.k@example.com",
        "appointment_date": "2026-01-21",
        "time": "14:30",
        "insurance_provider": "MediCare",
        "notes": "Cavity on upper right molar"
    },
    "sample-appt-005": {
        "service": "Checkup",
        "patient_name": "Rania Samir",
        "phone": "0799992345",
        "email": "rania.s@example.com",
        "appointment_date": "2026-01-22",
        "time": "09:30",
        "insurance_provider": "BlueCross",
        "notes": "Annual checkup"
    },
    "sample-appt-006": {
        "service": "Extraction",
        "patient_name": "Karim Nasser",
        "phone": "0790003456",
        "email": "karim.n@example.com",
        "appointment_date": "2026-01-22",
        "time": "13:00",
        "insurance_provider": "HealthPlus",
        "notes": "Wisdom tooth removal"
    },
    "sample-appt-007": {
        "service": "Dental Cleaning",
        "patient_name": "Nour Khalil",
        "phone": "0791114567",
        "email": "nour.k@example.com",
        "appointment_date": "2026-01-26",
        "time": "10:30",
        "insurance_provider": "No Insurance",
        "notes": "Deep cleaning requested"
    },
    "sample-appt-008": {
        "service": "Root Canal",
        "patient_name": "Omar Fares",
        "phone": "0792225678",
        "email": "omar.f@example.com",
        "appointment_date": "2026-01-27",
        "time": "09:00",
        "insurance_provider": "MediCare",
        "notes": "Severe tooth pain"
    },
    "sample-appt-009": {
        "service": "Teeth Whitening",
        "patient_name": "Dina Mahmoud",
        "phone": "0793336789",
        "email": "dina.m@example.com",
        "appointment_date": "2026-01-28",
        "time": "15:00",
        "insurance_provider": "BlueCross",
        "notes": "Wedding preparation"
    },
    "sample-appt-010": {
        "service": "Consultation",
        "patient_name": "Tariq Zayed",
        "phone": "0794447890",
        "email": "tariq.z@example.com",
        "appointment_date": "2026-01-29",
        "time": "13:30",
        "insurance_provider": "HealthPlus",
        "notes": "Braces consultation"
    }
}

# Load appointments from JSON file if exists
def load_appointments():
    """Load appointments from JSON file"""
    if os.path.exists(APPOINTMENTS_FILE):
        try:
            with open(APPOINTMENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading appointments: {e}")
            return APPOINTMENTS.copy()
    else:
        # Create initial file with sample data
        save_appointments(APPOINTMENTS)
        return APPOINTMENTS.copy()

def save_appointments(appointments_dict):
    """Save appointments to JSON file"""
    try:
        with open(APPOINTMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(appointments_dict, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving appointments: {e}")

# Initialize APPOINTMENTS from file
APPOINTMENTS = load_appointments()

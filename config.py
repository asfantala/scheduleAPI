# Service duration in minutes and slot requirements
SERVICE_DURATION = {
    "Dental Cleaning": 30,
    "تنظيف الأسنان": 30,
    "Root Canal": 90,
    "علاج العصب": 90,
    "Teeth Whitening": 60,
    "تبييض الأسنان": 60,
    "Filling": 45,
    "حشو": 45,
    "Extraction": 45,
    "خلع": 45,
    "Consultation": 30,
    "استشارة": 30,
    "Checkup": 30,
    "فحص": 30,
    "Default": 30  # Default duration for unlisted services
}

# Available dentists
DENTISTS = [
    "Dr. Sarah Ahmed",
    "Dr. Mohammad Hassan",
    "Dr. Layla Ibrahim"
]

# Dentist working schedules
# weekday: Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6
DENTIST_SCHEDULES = {
    "Dr. Sarah Ahmed": {
        "working_days": [6, 0, 1, 2],  # Sunday, Monday, Tuesday, Wednesday
        "vacation_dates": []  # Add specific dates like "2026-02-15"
    },
    "Dr. Mohammad Hassan": {
        "working_days": [0, 1, 2, 3],  # Monday, Tuesday, Wednesday, Thursday
        "vacation_dates": []
    },
    "Dr. Layla Ibrahim": {
        "working_days": [6, 1, 2, 3],  # Sunday, Tuesday, Wednesday, Thursday
        "vacation_dates": []
    }
}

# Business hours
CLINIC_OPEN_TIME = "09:00"
CLINIC_CLOSE_TIME = "18:00"

# Booking rules
MIN_ADVANCE_HOURS = 2  # Minimum 2 hours notice
MAX_ADVANCE_DAYS = 90  # Can book up to 90 days ahead
CANCELLATION_HOURS = 24  # Must cancel 24 hours before

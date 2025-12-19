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

# Business hours
CLINIC_OPEN_TIME = "09:00"
CLINIC_CLOSE_TIME = "18:00"

# Booking rules
MIN_ADVANCE_HOURS = 2  # Minimum 2 hours notice
MAX_ADVANCE_DAYS = 90  # Can book up to 90 days ahead
CANCELLATION_HOURS = 24  # Must cancel 24 hours before

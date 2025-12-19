from fastapi import FastAPI, HTTPException
from models import (
    AvailabilityRequest,
    AvailabilityResponse,
    BookingRequest,
    BookingResponse,
    TimeSlot,
    UpdateRequest,
    UpdateResponse,
    DeleteResponse,
    AppointmentDetail
)
from data import SCHEDULE, APPOINTMENTS
from config import SERVICE_DURATION, MIN_ADVANCE_HOURS, MAX_ADVANCE_DAYS, CANCELLATION_HOURS
import uuid
from dateutil import parser
from datetime import datetime, timedelta
import re

def get_service_duration(service: str) -> int:
    """Get duration in minutes for a service"""
    return SERVICE_DURATION.get(service, SERVICE_DURATION["Default"])

def calculate_required_slots(service: str, start_time: str) -> list:
    """Calculate all time slots needed for a service based on duration"""
    duration = get_service_duration(service)
    slots_needed = duration // 30  # Each slot is 30 minutes
    
    required_slots = []
    current_time = datetime.strptime(start_time, "%H:%M")
    
    for i in range(slots_needed):
        required_slots.append(current_time.strftime("%H:%M"))
        current_time += timedelta(minutes=30)
    
    return required_slots

def validate_booking_time(appointment_date: str, appointment_time: str) -> None:
    """Validate booking follows business rules"""
    try:
        appt_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
    except:
        raise HTTPException(status_code=400, detail="Invalid date or time format. Use YYYY-MM-DD for date and HH:MM for time")
    
    now = datetime.now()
    
    # Check minimum advance notice
    min_booking_time = now + timedelta(hours=MIN_ADVANCE_HOURS)
    if appt_datetime < min_booking_time:
        raise HTTPException(
            status_code=400,
            detail=f"Appointments must be booked at least {MIN_ADVANCE_HOURS} hours in advance"
        )
    
    # Check maximum advance booking
    max_booking_time = now + timedelta(days=MAX_ADVANCE_DAYS)
    if appt_datetime > max_booking_time:
        raise HTTPException(
            status_code=400,
            detail=f"Appointments can only be booked up to {MAX_ADVANCE_DAYS} days in advance"
        )
    
    # Check if date is in the past
    if appt_datetime < now:
        raise HTTPException(status_code=400, detail="Cannot book appointments in the past")
    
    # Check if it's a weekend (optional - uncomment if clinic is closed on weekends)
    # if appt_datetime.weekday() >= 5:  # 5=Saturday, 6=Sunday
    #     raise HTTPException(status_code=400, detail="Clinic is closed on weekends")

def check_patient_existing_appointments(phone: str, email: str, appointment_date: str, appointment_time: str, exclude_id: str = None) -> None:
    """Prevent patient from having multiple appointments at same time"""
    for appt_id, appt in APPOINTMENTS.items():
        if exclude_id and appt_id == exclude_id:
            continue
            
        # Check if same patient (by phone or email)
        if appt["phone"] == phone or appt["email"] == email:
            # Check if same date and time
            if appt["appointment_date"] == appointment_date and appt["time"] == appointment_time:
                raise HTTPException(
                    status_code=409,
                    detail=f"Patient already has an appointment on {appointment_date} at {appointment_time}"
                )

def check_slot_availability(service: str, appointment_date: str, start_time: str, exclude_id: str = None) -> None:
    """Check if all required time slots are available for the service duration"""
    required_slots = calculate_required_slots(service, start_time)
    
    # Check if all required slots exist in schedule
    available_slots = SCHEDULE.get(appointment_date, [])
    for slot in required_slots:
        if slot not in available_slots:
            raise HTTPException(
                status_code=400,
                detail=f"Time slot {slot} is not available in the clinic schedule"
            )
    
    # Check if any required slot is already booked
    for appt_id, appt in APPOINTMENTS.items():
        if exclude_id and appt_id == exclude_id:
            continue
            
        if appt["appointment_date"] == appointment_date:
            # Calculate slots for existing appointment
            existing_slots = calculate_required_slots(appt["service"], appt["time"])
            
            # Check for overlap
            overlap = set(required_slots) & set(existing_slots)
            if overlap:
                raise HTTPException(
                    status_code=409,
                    detail=f"Time slots {', '.join(overlap)} are already booked on {appointment_date}"
                )

def normalize_time(time_str: str) -> str:
    """Convert various time formats (English & Arabic) to HH:MM (24-hour format)"""
    time_str = time_str.strip().lower()
    
    # Arabic time mappings
    arabic_mappings = {
        'صباحا': 'am',
        'صباحاً': 'am',
        'ص': 'am',
        'مساء': 'pm',
        'مساءً': 'pm',
        'م': 'pm',
        'الصباح': 'am',
        'المساء': 'pm',
        'ظهرا': 'pm',
        'ظهراً': 'pm'
    }
    
    # Replace Arabic time indicators with English
    for arabic, english in arabic_mappings.items():
        time_str = time_str.replace(arabic, english)
    
    # Convert Arabic numerals to English
    arabic_to_english_nums = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    for arabic_num, english_num in arabic_to_english_nums.items():
        time_str = time_str.replace(arabic_num, english_num)
    
    # Handle times like "5pm", "5 pm", "5:00pm", "17:00"
    # Remove spaces between time and am/pm
    time_str = re.sub(r'(\d)\s+(am|pm)', r'\1\2', time_str)
    
    try:
        # Parse the time string
        parsed_time = parser.parse(time_str, fuzzy=True)
        return parsed_time.strftime("%H:%M")
    except:
        # If parsing fails, return as-is
        return time_str

app = FastAPI(title="Dental Clinic API")

@app.post("/check-availability", response_model=AvailabilityResponse)
def check_availability(req: AvailabilityRequest):
    slots = []
    all_times = SCHEDULE.get(req.preferred_date, [])
    
    # Filter out already booked times
    booked_times = [
        appt["time"] for appt in APPOINTMENTS.values() 
        if appt["appointment_date"] == req.preferred_date
    ]
    
    # Only show available times
    for t in all_times:
        if t not in booked_times:
            slots.append(TimeSlot(date=req.preferred_date, time=t))
    
    return AvailabilityResponse(
        available=len(slots) > 0,
        slots=slots
    )

@app.post("/book-appointment", response_model=BookingResponse)
def book_appointment(req: BookingRequest):
    # Normalize time format
    normalized_time = normalize_time(req.time)
    
    # Validate business rules
    validate_booking_time(req.appointment_date, normalized_time)
    
    # Check patient doesn't have conflicting appointment
    check_patient_existing_appointments(req.phone, req.email, req.appointment_date, normalized_time)
    
    # Check all required slots are available based on service duration
    check_slot_availability(req.service, req.appointment_date, normalized_time)
    
    appointment_id = str(uuid.uuid4())
    
    # Store appointment with normalized time
    APPOINTMENTS[appointment_id] = {
        "service": req.service,
        "patient_name": req.patient_name,
        "phone": req.phone,
        "email": req.email,
        "appointment_date": req.appointment_date,
        "time": normalized_time,
        "insurance_provider": req.insurance_provider,
        "notes": req.notes
    }

    return BookingResponse(
        success=True,
        appointment_id=appointment_id
    )

@app.get("/appointment/{appointment_id}", response_model=AppointmentDetail)
def get_appointment(appointment_id: str):
    if appointment_id not in APPOINTMENTS:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    appointment = APPOINTMENTS[appointment_id]
    return AppointmentDetail(
        appointment_id=appointment_id,
        **appointment
    )

@app.put("/update-appointment", response_model=UpdateResponse)
def update_appointment(req: UpdateRequest):
    if req.appointment_id not in APPOINTMENTS:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    appointment = APPOINTMENTS[req.appointment_id]
    
    # Get current or updated values
    new_date = req.appointment_date if req.appointment_date else appointment["appointment_date"]
    new_time = normalize_time(req.time) if req.time else appointment["time"]
    service = appointment["service"]
    
    # If date or time is being changed, validate
    if req.appointment_date or req.time:
        # Validate business rules
        validate_booking_time(new_date, new_time)
        
        # Check patient doesn't have conflicting appointment
        check_patient_existing_appointments(
            appointment["phone"], 
            appointment["email"], 
            new_date, 
            new_time,
            exclude_id=req.appointment_id
        )
        
        # Check slot availability (excluding current appointment)
        check_slot_availability(service, new_date, new_time, exclude_id=req.appointment_id)
    
    # Update fields
    if req.appointment_date:
        appointment["appointment_date"] = req.appointment_date
    if req.time:
        appointment["time"] = new_time
    if req.insurance_provider is not None:
        appointment["insurance_provider"] = req.insurance_provider
    if req.notes is not None:
        appointment["notes"] = req.notes
    
    return UpdateResponse(
        success=True,
        message=f"Appointment {req.appointment_id} updated successfully"
    )

@app.delete("/cancel-appointment/{appointment_id}", response_model=DeleteResponse)
def cancel_appointment(appointment_id: str):
    if appointment_id not in APPOINTMENTS:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    appointment = APPOINTMENTS[appointment_id]
    
    # Check cancellation policy
    try:
        appt_datetime = datetime.strptime(
            f"{appointment['appointment_date']} {appointment['time']}", 
            "%Y-%m-%d %H:%M"
        )
        min_cancel_time = appt_datetime - timedelta(hours=CANCELLATION_HOURS)
        
        if datetime.now() > min_cancel_time:
            raise HTTPException(
                status_code=400,
                detail=f"Appointments must be cancelled at least {CANCELLATION_HOURS} hours in advance"
            )
    except HTTPException:
        raise
    except:
        pass  # If date parsing fails, allow cancellation
    
    del APPOINTMENTS[appointment_id]
    
    return DeleteResponse(
        success=True,
        message=f"Appointment {appointment_id} cancelled successfully"
    )

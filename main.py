from fastapi import FastAPI, HTTPException
from models import (
    BookingRequest,
    BookingResponse,
    UpdateRequest,
    UpdateResponse,
    DeleteResponse,
    AppointmentDetail,
    AllAppointmentsResponse
)
from data import SCHEDULE, APPOINTMENTS, save_appointments
from config import SERVICE_DURATION, MIN_ADVANCE_HOURS, MAX_ADVANCE_DAYS, CANCELLATION_HOURS
from typing import Optional
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
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date or time format. Use YYYY-MM-DD for date and HH:MM for time")
    
    now = datetime.now()
    
    # Check if date exists in schedule
    if appointment_date not in SCHEDULE:
        raise HTTPException(
            status_code=400,
            detail=f"No appointments available on {appointment_date}. Please check available dates."
        )
    
    # Check if time slot exists in schedule for this date
    available_times = SCHEDULE.get(appointment_date, [])
    if appointment_time not in available_times:
        raise HTTPException(
            status_code=400,
            detail=f"Time {appointment_time} is not available on {appointment_date}. Available times: {', '.join(available_times)}"
        )
    
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
                    detail=f"Time slots {', '.join(sorted(overlap))} are already booked on {appointment_date}"
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
    except Exception:
        # If parsing fails, return as-is
        return time_str

app = FastAPI(
    title="Dental Appointment API",
    description="Simple API - Only 4 endpoints you need",
    version="1.0.0"
)

# ============================================================================
# 4 SIMPLE ENDPOINTS
# ============================================================================

@app.post("/appointments", response_model=BookingResponse, status_code=201)
def create_appointment(req: BookingRequest):
    """
    📅 Book a new dental appointment
    
    Required: service, patient_name, phone, appointment_date, time
    """
    appointment_date = req.appointment_date
    appointment_time = req.time
    
    # Normalize time format
    normalized_time = normalize_time(appointment_time)
    
    # Validate business rules
    validate_booking_time(appointment_date, normalized_time)
    check_patient_existing_appointments(req.phone, req.email, appointment_date, normalized_time)
    check_slot_availability(req.service, appointment_date, normalized_time)
    
    # Generate unique appointment ID
    appointment_id = str(uuid.uuid4())
    
    # Store appointment
    APPOINTMENTS[appointment_id] = {
        "service": req.service,
        "patient_name": req.patient_name,
        "phone": req.phone,
        "email": req.email,
        "appointment_date": appointment_date,
        "time": normalized_time,
        "insurance_provider": req.insurance_provider,
        "notes": req.notes
    }
    
    # Save to JSON file
    save_appointments(APPOINTMENTS)

    return BookingResponse(success=True, appointment_id=appointment_id)


@app.get("/appointments", response_model=AllAppointmentsResponse)
def get_appointments(date: Optional[str] = None, phone: Optional[str] = None):
    """
    📋 Get all appointments (optionally filter by date and/or phone)
    
    Example: /appointments?date=2026-01-20&phone=0791234567
    """
    appointments_list = []
    
    for appt_id, appt in APPOINTMENTS.items():
        if date and appt["appointment_date"] != date:
            continue
        if phone and appt["phone"] != phone:
            continue
            
        appointments_list.append(AppointmentDetail(appointment_id=appt_id, **appt))
    
    appointments_list.sort(key=lambda x: (x.appointment_date, x.time))
    
    return AllAppointmentsResponse(total=len(appointments_list), appointments=appointments_list)


@app.put("/appointments/{appointment_id}", response_model=UpdateResponse)
def update_appointment(appointment_id: str, req: UpdateRequest):
    """
    ✏️ Update an existing appointment
    
    Can update: appointment_date, time, insurance_provider, notes
    """
    if appointment_id not in APPOINTMENTS:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    appointment = APPOINTMENTS[appointment_id]
    req.appointment_id = appointment_id  # Set the ID from path
    
    # Get current or updated values
    new_date = req.appointment_date if req.appointment_date else appointment["appointment_date"]
    new_time = normalize_time(req.time) if req.time else appointment["time"]
    service = appointment["service"]
    
    # If date or time is being changed, validate
    if req.appointment_date or req.time:
        validate_booking_time(new_date, new_time)
        check_patient_existing_appointments(
            appointment["phone"], appointment["email"], new_date, new_time, exclude_id=appointment_id
        )
        check_slot_availability(service, new_date, new_time, exclude_id=appointment_id)
    
    # Update fields
    if req.appointment_date:
        appointment["appointment_date"] = req.appointment_date
    if req.time:
        appointment["time"] = new_time
    if req.insurance_provider is not None:
        appointment["insurance_provider"] = req.insurance_provider
    if req.notes is not None:
        appointment["notes"] = req.notes
    
    save_appointments(APPOINTMENTS)
    
    return UpdateResponse(success=True, message="Appointment updated successfully")


@app.delete("/appointments/{appointment_id}", response_model=DeleteResponse)
def delete_appointment(appointment_id: str):
    """
    🗑️ Cancel an appointment
    
    Must cancel at least 24 hours in advance
    """
    if appointment_id not in APPOINTMENTS:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    appointment = APPOINTMENTS[appointment_id]
    
    # Check cancellation policy
    try:
        appt_datetime = datetime.strptime(
            f"{appointment['appointment_date']} {appointment['time']}", "%Y-%m-%d %H:%M"
        )
        min_cancel_time = appt_datetime - timedelta(hours=CANCELLATION_HOURS)
        
        if datetime.now() > min_cancel_time:
            raise HTTPException(
                status_code=400,
                detail=f"Must cancel at least {CANCELLATION_HOURS} hours in advance"
            )
    except HTTPException:
        raise
    except Exception:
        pass
    
    del APPOINTMENTS[appointment_id]
    save_appointments(APPOINTMENTS)
    
    return DeleteResponse(success=True, message="Appointment cancelled successfully")


@app.get("/available-slots")
def get_available_slots(date: str, service: str = "Default"):
    """
    📅 Get available time slots for a specific date and service
    
    Returns only unbooked slots that can accommodate the service duration
    Example: /available-slots?date=2026-01-20&service=Root Canal
    """
    # Check if date exists in schedule
    if date not in SCHEDULE:
        raise HTTPException(
            status_code=400,
            detail=f"No appointments available on {date}. Please check available dates."
        )
    
    # Get all scheduled slots for the date
    all_slots = SCHEDULE[date]
    
    # Get service duration
    duration = get_service_duration(service)
    slots_needed = duration // 30
    
    # Find all booked slots for this date
    booked_slots = set()
    for appt_id, appt in APPOINTMENTS.items():
        if appt["appointment_date"] == date:
            # Calculate all slots occupied by this appointment
            occupied_slots = calculate_required_slots(appt["service"], appt["time"])
            booked_slots.update(occupied_slots)
    
    # Find available start times that can accommodate the service duration
    available_start_times = []
    for i, start_slot in enumerate(all_slots):
        # Check if we have enough consecutive slots from this start time
        required_slots = []
        current_time = datetime.strptime(start_slot, "%H:%M")
        
        can_book = True
        for j in range(slots_needed):
            slot_time = current_time.strftime("%H:%M")
            
            # Check if this slot exists in schedule
            if slot_time not in all_slots:
                can_book = False
                break
            
            # Check if this slot is already booked
            if slot_time in booked_slots:
                can_book = False
                break
            
            required_slots.append(slot_time)
            current_time += timedelta(minutes=30)
        
        if can_book:
            available_start_times.append(start_slot)
    
    return {
        "date": date,
        "service": service,
        "duration_minutes": duration,
        "slots_needed": slots_needed,
        "total_available": len(available_start_times),
        "available_times": available_start_times
    }

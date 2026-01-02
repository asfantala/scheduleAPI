from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
from config import SERVICE_DURATION, MIN_ADVANCE_HOURS, MAX_ADVANCE_DAYS, CANCELLATION_HOURS, DENTISTS, DENTIST_SCHEDULES
from typing import Optional
import uuid
from dateutil import parser
from datetime import datetime, timedelta
import re

def validate_service(service: str) -> None:
    """Validate that service name is in the allowed list"""
    if service not in SERVICE_DURATION or service == "Default":
        valid_services = [s for s in SERVICE_DURATION.keys() if s != "Default"]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service '{service}'. Valid services: {', '.join(valid_services)}"
        )

def is_dentist_available(dentist: str, date_str: str) -> bool:
    """Check if dentist is working on a specific date"""
    if dentist not in DENTIST_SCHEDULES:
        return False

    schedule = DENTIST_SCHEDULES[dentist]

    # Check if date is in vacation
    if date_str in schedule["vacation_dates"]:
        return False

    # Check if weekday is a working day
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        weekday = date_obj.weekday()
        return weekday in schedule["working_days"]
    except:
        return False

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

def check_slot_availability(service: str, appointment_date: str, start_time: str, dentist: str = None, exclude_id: str = None) -> None:
    """Check if all required time slots are available for the service duration and dentist"""
    required_slots = calculate_required_slots(service, start_time)
    
    # Check if all required slots exist in schedule
    available_slots = SCHEDULE.get(appointment_date, [])
    for slot in required_slots:
        if slot not in available_slots:
            raise HTTPException(
                status_code=400,
                detail=f"Time slot {slot} is not available in the clinic schedule"
            )
    
    # Check if any required slot is already booked for this dentist
    for appt_id, appt in APPOINTMENTS.items():
        if exclude_id and appt_id == exclude_id:
            continue
        
        # Only check appointments for the same dentist
        if dentist and appt.get("dentist") != dentist:
            continue
            
        if appt["appointment_date"] == appointment_date:
            # Calculate slots for existing appointment
            existing_slots = calculate_required_slots(appt["service"], appt["time"])
            
            # Check for overlap
            overlap = set(required_slots) & set(existing_slots)
            if overlap:
                dentist_name = appt.get("dentist", "the clinic")
                raise HTTPException(
                    status_code=409,
                    detail=f"Time slots {', '.join(sorted(overlap))} are already booked for {dentist_name} on {appointment_date}"
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

def find_available_dentist(service: str, appointment_date: str, start_time: str) -> str:
    """Find an available dentist for the requested time slot"""
    for dentist in DENTISTS:
        # Check if dentist is working on this date
        if not is_dentist_available(dentist, appointment_date):
            continue
        
        try:
            check_slot_availability(service, appointment_date, start_time, dentist=dentist)
            return dentist
        except HTTPException:
            continue
    
    # No dentist available
    raise HTTPException(
        status_code=409,
        detail=f"No dentist available for {service} on {appointment_date} at {start_time}. All dentists are either booked or not working on this day."
    )

def search_appointments_by_phone(phone: str) -> list:
    """Search and return all appointment IDs for a phone number"""
    appointment_ids = []
    for appt_id, appt in APPOINTMENTS.items():
        if appt["phone"] == phone:
            appointment_ids.append(appt_id)
    return appointment_ids

def search_appointments_by_phone_and_date(phone: str, date: str) -> list:
    """Search and return all appointment IDs for a phone number and date"""
    appointment_ids = []
    for appt_id, appt in APPOINTMENTS.items():
        if appt["phone"] == phone and appt["appointment_date"] == date:
            appointment_ids.append(appt_id)
    return appointment_ids

app = FastAPI(
    title="Dental Appointment API",
    description="Simple API - Only 4 endpoints you need",
    version="1.0.0"
)

# Add CORS middleware to allow requests from HeyBreez and other sources
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (you can restrict this to specific domains)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)



@app.post("/appointments", response_model=BookingResponse, status_code=201)
def create_appointment(req: BookingRequest):
    """
    Book a new dental appointment

    Required: service, patient_name, phone, appointment_date, time
    Optional: dentist (auto-assigned if not specified)
    """
    appointment_date = req.appointment_date
    appointment_time = req.time

    # Validate service name
    validate_service(req.service)

    # Normalize time format
    normalized_time = normalize_time(appointment_time)

    # Validate business rules
    validate_booking_time(appointment_date, normalized_time)
    check_patient_existing_appointments(req.phone, req.email, appointment_date, normalized_time)
    
    # Handle dentist assignment
    # Treat empty string as None for dentist
    requested_dentist = req.dentist if req.dentist and req.dentist.strip() else None

    if requested_dentist:
        # Validate requested dentist exists
        if requested_dentist not in DENTISTS:
            raise HTTPException(
                status_code=400,
                detail=f"Dentist '{req.dentist}' not found. Available dentists: {', '.join(DENTISTS)}"
            )
        # Check if dentist is working on this date
        if not is_dentist_available(req.dentist, appointment_date):
            raise HTTPException(
                status_code=400,
                detail=f"{req.dentist} is not available on {appointment_date} (not working or on vacation)"
            )
        # Check if requested dentist is available
        check_slot_availability(req.service, appointment_date, normalized_time, dentist=req.dentist)
        assigned_dentist = req.dentist
    else:
        # Auto-assign an available dentist
        assigned_dentist = find_available_dentist(req.service, appointment_date, normalized_time)
    
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
        "dentist": assigned_dentist,
        "insurance_provider": req.insurance_provider,
        "notes": req.notes
    }
    
    # Save to JSON file
    save_appointments(APPOINTMENTS)

    return BookingResponse(success=True, appointment_id=appointment_id)


@app.get("/appointments", response_model=AllAppointmentsResponse)
def get_appointments(date: Optional[str] = None, phone: Optional[str] = None, dentist: Optional[str] = None):

    appointments_list = []
    
    for appt_id, appt in APPOINTMENTS.items():
        if date and appt["appointment_date"] != date:
            continue
        if phone and appt["phone"] != phone:
            continue
        if dentist and appt.get("dentist") != dentist:
            continue
            
        appointments_list.append(AppointmentDetail(appointment_id=appt_id, **appt))
    
    appointments_list.sort(key=lambda x: (x.appointment_date, x.time))
    
    return AllAppointmentsResponse(total=len(appointments_list), appointments=appointments_list)


@app.put("/appointments", response_model=UpdateResponse)
def update_appointment(req: UpdateRequest, phone: str, date: str):
    """
    Update the FIRST appointment on a specific date for a phone number

    Searches for appointments by phone and date, then updates only the earliest appointment on that date.
    Can update: service, patient_name, email, appointment_date, time, dentist, insurance_provider, notes
    Example: PUT /appointments?phone=0791234567&date=2026-01-20
    """
    # Search for appointments by phone and date
    appointment_ids = search_appointments_by_phone_and_date(phone, date)

    if not appointment_ids:
        raise HTTPException(status_code=404, detail=f"No appointments found for phone {phone} on {date}")

    # Find the FIRST appointment on that date (earliest time)
    first_appointment_id = None
    first_appointment_time = None

    for appt_id in appointment_ids:
        appointment = APPOINTMENTS[appt_id]
        appt_time = appointment["time"]

        if first_appointment_time is None or appt_time < first_appointment_time:
            first_appointment_id = appt_id
            first_appointment_time = appt_time

    # Update only the first appointment
    appointment = APPOINTMENTS[first_appointment_id]

    # Validate service if being changed
    if req.service:
        validate_service(req.service)

    # Get current or updated values
    service = req.service if req.service else appointment["service"]
    new_date = req.appointment_date if req.appointment_date else appointment["appointment_date"]
    new_time = normalize_time(req.time) if req.time else appointment["time"]
    new_dentist = req.dentist if req.dentist else appointment.get("dentist")
    new_email = req.email if req.email else appointment["email"]

    # Validate dentist if being changed
    if req.dentist:
        if req.dentist not in DENTISTS:
            raise HTTPException(
                status_code=400,
                detail=f"Dentist '{req.dentist}' not found. Available dentists: {', '.join(DENTISTS)}"
            )
        # Check if dentist is working on the date
        if not is_dentist_available(req.dentist, new_date):
            raise HTTPException(
                status_code=400,
                detail=f"{req.dentist} is not available on {new_date} (not working or on vacation)"
            )

    # If date, time, dentist, or service is being changed, validate
    if req.appointment_date or req.time or req.dentist or req.service:
        validate_booking_time(new_date, new_time)
        check_patient_existing_appointments(
            appointment["phone"], new_email, new_date, new_time, exclude_id=first_appointment_id
        )
        check_slot_availability(service, new_date, new_time, dentist=new_dentist, exclude_id=first_appointment_id)

    # Store old values for the response message
    old_date = appointment["appointment_date"]
    old_time = appointment["time"]

    # Update fields
    if req.service:
        appointment["service"] = req.service
    if req.patient_name:
        appointment["patient_name"] = req.patient_name
    if req.email:
        appointment["email"] = req.email
    if req.appointment_date:
        appointment["appointment_date"] = req.appointment_date
    if req.time:
        appointment["time"] = new_time
    if req.dentist:
        appointment["dentist"] = req.dentist
    if req.insurance_provider is not None:
        appointment["insurance_provider"] = req.insurance_provider
    if req.notes is not None:
        appointment["notes"] = req.notes

    save_appointments(APPOINTMENTS)
    return UpdateResponse(
        success=True,
        message=f"Appointment updated: {old_date} at {old_time} → {appointment['appointment_date']} at {appointment['time']}"
    )


@app.delete("/appointments", response_model=DeleteResponse)
def delete_appointment(phone: str):
    """
    Delete the NEXT upcoming appointment for a phone number

    Searches for all appointments by phone, then deletes only the earliest future appointment.
    Example: DELETE /appointments?phone=0791234567
    """
    # Search for appointments by phone
    appointment_ids = search_appointments_by_phone(phone)

    if not appointment_ids:
        raise HTTPException(status_code=404, detail="No appointments found for this phone number")

    # Find the next upcoming appointment (earliest future appointment)
    now = datetime.now()
    next_appointment_id = None
    next_appointment_datetime = None
    next_appointment_data = None

    for appt_id in appointment_ids:
        appointment = APPOINTMENTS[appt_id]
        try:
            appt_datetime = datetime.strptime(
                f"{appointment['appointment_date']} {appointment['time']}", "%Y-%m-%d %H:%M"
            )

            # Only consider future appointments
            if appt_datetime > now:
                if next_appointment_datetime is None or appt_datetime < next_appointment_datetime:
                    next_appointment_id = appt_id
                    next_appointment_datetime = appt_datetime
                    next_appointment_data = appointment
        except Exception:
            continue

    if not next_appointment_id:
        raise HTTPException(
            status_code=404,
            detail="No upcoming appointments found for this phone number. All appointments are in the past."
        )

    # Check cancellation policy for the next appointment
    min_cancel_time = next_appointment_datetime - timedelta(hours=CANCELLATION_HOURS)
    if now > min_cancel_time:
        raise HTTPException(
            status_code=400,
            detail=f"Appointment on {next_appointment_data['appointment_date']} at {next_appointment_data['time']} must be cancelled at least {CANCELLATION_HOURS} hours in advance"
        )

    # Delete only the next upcoming appointment
    del APPOINTMENTS[next_appointment_id]
    save_appointments(APPOINTMENTS)

    return DeleteResponse(
        success=True,
        message=f"Appointment cancelled: {next_appointment_data['appointment_date']} at {next_appointment_data['time']} with {next_appointment_data['dentist']}"
    )


@app.get("/available-slots")
def get_available_slots(date: str, service: str = "Default", dentist: Optional[str] = None):
    """
    
    Example: /available-slots?date=2026-01-20&service=Root Canal&dentist=Dr. Sarah Ahmed
    """
    # Check if date exists in schedule
    if date not in SCHEDULE:
        raise HTTPException(
            status_code=400,
            detail=f"No appointments available on {date}. Please check available dates."
        )
    
    # Validate dentist if specified
    if dentist:
        if dentist not in DENTISTS:
            raise HTTPException(
                status_code=400,
                detail=f"Dentist '{dentist}' not found. Available dentists: {', '.join(DENTISTS)}"
            )
        # Check if dentist is working on this date
        if not is_dentist_available(dentist, date):
            raise HTTPException(
                status_code=400,
                detail=f"{dentist} is not available on {date} (not working or on vacation)"
            )
    
    # Get all scheduled slots for the date
    all_slots = SCHEDULE[date]
    
    # Get service duration
    duration = get_service_duration(service)
    slots_needed = duration // 30
    
    if dentist:
        # Check availability for specific dentist
        booked_slots = set()
        for appt_id, appt in APPOINTMENTS.items():
            if appt["appointment_date"] == date and appt.get("dentist") == dentist:
                occupied_slots = calculate_required_slots(appt["service"], appt["time"])
                booked_slots.update(occupied_slots)
        
        available_start_times = []
        for start_slot in all_slots:
            required_slots = []
            current_time = datetime.strptime(start_slot, "%H:%M")
            
            can_book = True
            for j in range(slots_needed):
                slot_time = current_time.strftime("%H:%M")
                
                if slot_time not in all_slots or slot_time in booked_slots:
                    can_book = False
                    break
                
                required_slots.append(slot_time)
                current_time += timedelta(minutes=30)
            
            if can_book:
                available_start_times.append(start_slot)
        
        return {
            "date": date,
            "service": service,
            "dentist": dentist,
            "duration_minutes": duration,
            "slots_needed": slots_needed,
            "total_available": len(available_start_times),
            "available_times": available_start_times
        }
    else:
        # Show slots where ANY dentist is available
        available_start_times = []
        for start_slot in all_slots:
            current_time = datetime.strptime(start_slot, "%H:%M")
            
            # Check if at least one dentist is available
            dentist_available = False
            for check_dentist in DENTISTS:
                # Skip if dentist is not working on this date
                if not is_dentist_available(check_dentist, date):
                    continue
                
                try:
                    check_slot_availability(service, date, start_slot, dentist=check_dentist)
                    dentist_available = True
                    break
                except HTTPException:
                    continue
            
            if dentist_available:
                available_start_times.append(start_slot)
        
        return {
            "date": date,
            "service": service,
            "dentist": "Any available",
            "duration_minutes": duration,
            "slots_needed": slots_needed,
            "total_available": len(available_start_times),
            "available_times": available_start_times
        }

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
import uuid
from dateutil import parser
from datetime import datetime
import re

def normalize_time(time_str: str) -> str:
    """Convert various time formats to HH:MM (24-hour format)"""
    time_str = time_str.strip().lower()
    
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

    times = SCHEDULE.get(req.preferred_date, [])

    for t in times:
        slots.append(TimeSlot(date=req.preferred_date, time=t))

    return AvailabilityResponse(
        available=len(slots) > 0,
        slots=slots
    )

@app.post("/book-appointment", response_model=BookingResponse)
def book_appointment(req: BookingRequest):
    # Normalize time format
    normalized_time = normalize_time(req.time)
    
    # Check if the time slot is already booked
    for appt_id, appt in APPOINTMENTS.items():
        if appt["appointment_date"] == req.appointment_date and appt["time"] == normalized_time:
            raise HTTPException(
                status_code=409, 
                detail=f"Time slot {normalized_time} on {req.appointment_date} is already booked"
            )
    
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
    
    if req.appointment_date:
        appointment["appointment_date"] = req.appointment_date
    if req.time:
        appointment["time"] = normalize_time(req.time)
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
    
    del APPOINTMENTS[appointment_id]
    
    return DeleteResponse(
        success=True,
        message=f"Appointment {appointment_id} cancelled successfully"
    )

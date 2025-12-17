from pydantic import BaseModel
from typing import Optional, List

class AvailabilityRequest(BaseModel):
    service: str
    preferred_date: str
    preferred_time: Optional[str] = None

class TimeSlot(BaseModel):
    date: str
    time: str

class AvailabilityResponse(BaseModel):
    available: bool
    slots: List[TimeSlot]

class BookingRequest(BaseModel):
    service: str
    patient_name: str
    phone: str
    email: Optional[str] = "no-email@clinic.com"
    appointment_date: str
    time: str
    insurance_provider: Optional[str] = "No Insurance"
    notes: Optional[str] = "No additional notes"

class BookingResponse(BaseModel):
    success: bool
    appointment_id: str

class UpdateRequest(BaseModel):
    appointment_id: str
    appointment_date: Optional[str] = None
    time: Optional[str] = None
    insurance_provider: Optional[str] = None
    notes: Optional[str] = None

class UpdateResponse(BaseModel):
    success: bool
    message: str

class DeleteResponse(BaseModel):
    success: bool
    message: str

class AppointmentDetail(BaseModel):
    appointment_id: str
    service: str
    patient_name: str
    phone: str
    email: str
    appointment_date: str
    time: str
    insurance_provider: Optional[str] = None
    notes: Optional[str] = None

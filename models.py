from pydantic import BaseModel, field_validator
from typing import Optional, List
import re

class AvailabilityRequest(BaseModel):
    service: str
    preferred_date: str
    preferred_time: str

class TimeSlot(BaseModel):
    date: str
    time: str

class AvailabilityResponse(BaseModel):
    available: bool
    requested_date: str
    requested_time: str
    service: str
    duration_minutes: int
    alternative_slots: List[TimeSlot]
    message: str

# Simple booking request - only required fields
class BookingRequest(BaseModel):
    service: str
    patient_name: str
    phone: str
    appointment_date: str
    time: str
    dentist: Optional[str] = None  # If not specified, auto-assign available dentist
    email: Optional[str] = "no-email@clinic.com"
    insurance_provider: Optional[str] = "No Insurance"
    notes: Optional[str] = ""

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number format"""
        if not v:
            raise ValueError('Phone number is required')
        # Remove spaces and dashes
        cleaned = re.sub(r'[\s\-]', '', v)
        # Check if it's at least 10 digits
        if len(cleaned) < 10 or not cleaned.isdigit():
            raise ValueError('Phone number must be at least 10 digits')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format"""
        if v and v != "no-email@clinic.com":
            # Basic email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
        return v

    @field_validator('patient_name')
    @classmethod
    def validate_name(cls, v):
        """Validate patient name is not empty"""
        if not v or not v.strip():
            raise ValueError('Patient name is required')
        return v.strip()

class BookingResponse(BaseModel):
    success: bool
    appointment_id: str

class UpdateRequest(BaseModel):
    service: Optional[str] = None
    patient_name: Optional[str] = None
    email: Optional[str] = None
    appointment_date: Optional[str] = None
    time: Optional[str] = None
    dentist: Optional[str] = None
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
    dentist: Optional[str] = None
    insurance_provider: Optional[str] = None
    notes: Optional[str] = None

class AllAppointmentsResponse(BaseModel):
    total: int
    appointments: List[AppointmentDetail]

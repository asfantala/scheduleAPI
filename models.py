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

    @field_validator('phone', mode='before')
    @classmethod
    def validate_phone(cls, v):
        """Coerce and validate phone number format (accept ints too)"""
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError('Phone number is required')
        # Coerce non-string inputs (e.g., int) to string
        v_str = str(v)
        # Remove spaces, dashes, parentheses, and plus signs
        cleaned = re.sub(r'[\s\-\(\)\+]', '', v_str)
        # Check if it's at least 9 digits (more lenient)
        if len(cleaned) < 9:
            raise ValueError('Phone number must be at least 9 digits')
        if not cleaned.isdigit():
            raise ValueError('Phone number must contain only digits')
        return cleaned

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format (lenient)"""
        if not v:
            return "no-email@clinic.com"  # Use default if empty
        if v == "no-email@clinic.com":
            return v
        # More lenient email validation
        if '@' not in v or '.' not in v:
            raise ValueError('Invalid email format - must contain @ and .')
        return v

    @field_validator('patient_name')
    @classmethod
    def validate_name(cls, v):
        """Validate patient name is not empty"""
        if not v or not v.strip():
            raise ValueError('Patient name is required')
        # Allow any characters including Arabic, spaces, etc.
        return v.strip()

class BookingResponse(BaseModel):
    success: bool
    appointment_id: str

class UpdateRequest(BaseModel):
    service: Optional[str] = None
    patient_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    appointment_date: Optional[str] = None
    time: Optional[str] = None
    dentist: Optional[str] = None
    insurance_provider: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('phone', mode='before')
    @classmethod
    def validate_update_phone(cls, v):
        if v is None:
            return v
        v_str = str(v)
        cleaned = re.sub(r'[\s\-\(\)\+]', '', v_str)
        if not cleaned:
            return None
        return cleaned

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

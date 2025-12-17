# Dental Clinic Scheduling API

A FastAPI-based RESTful API for managing dental clinic appointments with full CRUD operations and double-booking prevention.

## Features

- ✅ Check appointment availability
- ✅ Book appointments with conflict prevention
- ✅ View appointment details
- ✅ Update existing appointments
- ✅ Cancel appointments
- ✅ Flexible time format support (12hr/24hr)
- ✅ Default values for optional fields

## Tech Stack

- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation
- **python-dateutil** - Flexible time parsing

## Installation

```bash
# Clone the repository
git clone https://github.com/asfantala/scheduleAPI.git
cd scheduleAPI

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload
```

## API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### 1. Check Availability

**POST** `/check-availability`

Check available time slots for a specific date.

**Request Body:**
```json
{
  "service": "Dental Cleaning",
  "preferred_date": "2026-01-20",
  "preferred_time": "afternoon"
}
```

**Response:**
```json
{
  "available": true,
  "slots": [
    {
      "date": "2026-01-20",
      "time": "09:00"
    },
    {
      "date": "2026-01-20",
      "time": "11:00"
    },
    {
      "date": "2026-01-20",
      "time": "14:00"
    },
    {
      "date": "2026-01-20",
      "time": "15:00"
    }
  ]
}
```

### 2. Book Appointment

**POST** `/book-appointment`

Create a new appointment. Prevents double-booking automatically.

**Request Body:**
```json
{
  "service": "Dental Cleaning",
  "patient_name": "John Doe",
  "phone": "15550199",
  "email": "john@example.com",
  "appointment_date": "2026-01-20",
  "time": "2:00 PM",
  "insurance_provider": "BlueCross",
  "notes": "First-time patient"
}
```

**Response:**
```json
{
  "success": true,
  "appointment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Flexible Time Formats:**
- `"14:00"` (24-hour)
- `"2:00 PM"` (12-hour with space)
- `"2pm"` (12-hour no space)
- `"2:00pm"` (12-hour no space)

### 3. Get Appointment Details

**GET** `/appointment/{appointment_id}`

Retrieve details of a specific appointment.

**Response:**
```json
{
  "appointment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "service": "Dental Cleaning",
  "patient_name": "John Doe",
  "phone": "15550199",
  "email": "john@example.com",
  "appointment_date": "2026-01-20",
  "time": "14:00",
  "insurance_provider": "BlueCross",
  "notes": "First-time patient"
}
```

### 4. Update Appointment

**PUT** `/update-appointment`

Modify an existing appointment.

**Request Body:**
```json
{
  "appointment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "appointment_date": "2026-01-21",
  "time": "10:00 AM",
  "notes": "Rescheduled due to conflict"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Appointment a1b2c3d4-e5f6-7890-abcd-ef1234567890 updated successfully"
}
```

### 5. Cancel Appointment

**DELETE** `/cancel-appointment/{appointment_id}`

Cancel and remove an appointment.

**Response:**
```json
{
  "success": true,
  "message": "Appointment a1b2c3d4-e5f6-7890-abcd-ef1234567890 cancelled successfully"
}
```

## Sample Data

The API includes pre-configured data:

### Available Time Slots
- **December 2025**: Dec 17, 18, 22, 23
- **January 2026**: Multiple dates throughout the month

### Sample Appointments
Three pre-loaded appointments for testing:

| ID | Patient | Service | Date | Time |
|---|---|---|---|---|
| `sample-appt-001` | Sarah Johnson | Dental Cleaning | 2026-01-20 | 09:00 |
| `sample-appt-002` | Ahmed Ali | Root Canal | 2026-01-20 | 14:00 |
| `sample-appt-003` | Layla Hassan | Teeth Whitening | 2026-01-21 | 10:30 |

You can retrieve these using the GET endpoint:
```bash
curl -X 'GET' 'http://localhost:8000/appointment/sample-appt-001'
```

See `data.py` for complete details.

## cURL Examples

### Check Availability
```bash
curl -X 'POST' \
  'http://localhost:8000/check-availability' \
  -H 'Content-Type: application/json' \
  -d '{
    "service": "Dental Cleaning",
    "preferred_date": "2026-01-20"
  }'
```

### Book Appointment
```bash
curl -X 'POST' \
  'http://localhost:8000/book-appointment' \
  -H 'Content-Type: application/json' \
  -d '{
    "service": "Dental Cleaning",
    "patient_name": "John Doe",
    "phone": "15550199",
    "email": "john@example.com",
    "appointment_date": "2026-01-20",
    "time": "2:00 PM",
    "insurance_provider": "BlueCross",
    "notes": "First-time patient"
  }'
```

### Get Appointment
```bash
curl -X 'GET' \
  'http://localhost:8000/appointment/{appointment_id}'
```

### Update Appointment
```bash
curl -X 'PUT' \
  'http://localhost:8000/update-appointment' \
  -H 'Content-Type: application/json' \
  -d '{
    "appointment_id": "your-appointment-id",
    "time": "3:00 PM"
  }'
```

### Cancel Appointment
```bash
curl -X 'DELETE' \
  'http://localhost:8000/cancel-appointment/{appointment_id}'
```

## Error Handling

### 409 Conflict - Double Booking
```json
{
  "detail": "Time slot 14:00 on 2026-01-20 is already booked"
}
```

### 404 Not Found - Invalid Appointment ID
```json
{
  "detail": "Appointment not found"
}
```

## Default Values

Optional fields have default values:
- `email`: "no-email@clinic.com"
- `insurance_provider`: "No Insurance"
- `notes`: "No additional notes"

## Deployment

This API can be deployed on:
- **Render** (recommended)
- **Railway**
- **Fly.io**
- **Heroku**
- **AWS EC2/Lightsail**
- **DigitalOcean**
- **Google Cloud Run**

**Note**: Cannot be deployed on Netlify (requires persistent server).

## Project Structure

```
scheduleAPI/
├── main.py              # FastAPI application & endpoints
├── models.py            # Pydantic schemas
├── data.py              # Mock schedule & storage
├── requirements.txt     # Python dependencies
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## License

MIT License

## Author

Tala - [@asfantala](https://github.com/asfantala)

---

**API Status**: ✅ Running on http://localhost:8000

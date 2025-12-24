# Dental Clinic Scheduling API

A production-ready FastAPI-based RESTful API for managing dental clinic appointments with realistic business logic, calendar-based scheduling, and comprehensive validation.

## 🌟 Features

### Core Functionality
- ✅ **Calendar-based availability checking** - Real-time slot validation
- ✅ **Smart appointment booking** - Service duration-aware scheduling
- ✅ **View all appointments** - Admin dashboard support
- ✅ **Update appointments** - Reschedule with conflict detection
- ✅ **Cancel appointments** - 24-hour cancellation policy
- ✅ **Conflict prevention** - No double-booking, duplicate patient detection

### Advanced Features
- 🌍 **Arabic language support** - Time format handling (٢ مساءً, ٩ صباحا)
- ⏰ **Flexible time formats** - 12hr/24hr (2:00 PM, 14:00, 2pm)
- 📅 **Service duration handling** - Automatic multi-slot blocking
- 🔒 **Business rules validation** - Advance booking limits, working hours
- 🎯 **Smart alternatives** - Suggests available slots when requested time is taken

## 🏗️ Tech Stack

- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation and settings management
- **python-dateutil** - Flexible date/time parsing
- **Railway** - Cloud deployment platform

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/asfantala/scheduleAPI.git
cd scheduleAPI

# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn main:app --reload
```

Server runs at: **http://localhost:8000**

## 📚 API Documentation

Interactive documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 API Endpoints

### 1. Check Availability - `GET /check-availability`

Check if a specific date and time is available for a service.

**Query Parameters:**
- `service` - Service type (e.g., "Dental Cleaning", "Root Canal")
- `preferred_date` - Date in YYYY-MM-DD format
- `preferred_time` - Time in any format (14:00, 2:00 PM, 2pm, ٢ مساءً)

**Example:**
```bash
GET /check-availability?service=Root%20Canal&preferred_date=2026-01-20&preferred_time=2:00%20PM
```

**Response (Available):**
```json
{
  "available": true,
  "requested_date": "2026-01-20",
  "requested_time": "14:00",
  "service": "Root Canal",
  "duration_minutes": 90,
  "alternative_slots": [],
  "message": "Time slot 14:00 on 2026-01-20 is available for Root Canal (90 minutes)"
}
```

---

### 2. Book Appointment - `POST /book-appointment`

Create a new appointment with validation.

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

---

### 3. Get All Appointments - `GET /appointments`

Retrieve all booked appointments (admin endpoint).

**Query Parameters:**
- `date` (optional) - Filter by date (YYYY-MM-DD)

**Example:**
```bash
GET /appointments?date=2026-01-20
```

---

### 4. Get Appointment - `GET /appointment/{appointment_id}`

Get specific appointment details.

---

### 5. Update Appointment - `PUT /update-appointment`

Modify an existing appointment.

**Request Body:**
```json
{
  "appointment_id": "a1b2c3d4-...",
  "appointment_date": "2026-01-21",
  "time": "10:00 AM",
  "notes": "Rescheduled"
}
```

---

### 6. Cancel Appointment - `DELETE /cancel-appointment/{appointment_id}`

Cancel an appointment (24-hour notice required).

---

## ⚙️ Configuration

### Service Duration (config.py)
```python
SERVICE_DURATION = {
    "Dental Cleaning": 30,      # 1 slot (30 min)
    "Root Canal": 90,            # 3 slots (90 min)
    "Teeth Whitening": 60,       # 2 slots (60 min)
    "Filling": 45,
    "Extraction": 45,
    "Consultation": 30,
    "Checkup": 30
}
```

### Business Rules
- **Clinic hours**: 9:00 AM - 6:00 PM
- **Appointment slots**: 30-minute intervals
- **Lunch break**: 12:00 PM - 1:00 PM (no bookings)
- **Minimum advance**: 2 hours
- **Maximum advance**: 90 days
- **Cancellation policy**: 24 hours notice

---

## 📅 Sample Data

10 mock appointments included for testing across January 2026:

| Date | Time | Patient | Service |
|------|------|---------|---------|
| Jan 20 | 09:00 | Sarah Johnson | Dental Cleaning |
| Jan 20 | 14:00 | Ahmed Ali | Root Canal |
| Jan 21 | 10:00 | Layla Hassan | Teeth Whitening |
| Jan 22 | 09:30 | Rania Samir | Checkup |
| ... | ... | ... | ... |

---

## 🚀 Deployment

**Live API**: https://web-production-b2126.up.railway.app

### Deploy to Railway
1. Push code to GitHub
2. Connect repository to Railway
3. Railway auto-deploys using Procfile
4. Access API at generated URL

---

## 🧪 Testing

**Check availability:**
```bash
curl "http://localhost:8000/check-availability?service=Dental%20Cleaning&preferred_date=2026-01-20&preferred_time=09:00"
```

**Book appointment:**
```bash
curl -X POST http://localhost:8000/book-appointment \
  -H "Content-Type: application/json" \
  -d '{"service":"Dental Cleaning","patient_name":"John","phone":"123","email":"j@ex.com","appointment_date":"2026-01-20","time":"15:00"}'
```

**Get all appointments:**
```bash
curl http://localhost:8000/appointments
```

---

## 🏗️ Project Structure

```
scheduleAPI/
├── main.py              # FastAPI app & endpoints
├── models.py            # Pydantic schemas
├── data.py              # Schedule & appointments
├── config.py            # Service durations & rules
├── requirements.txt     # Dependencies
├── Procfile            # Railway config
└── README.md           # Documentation
```

---

## 🔒 Business Logic

### Calendar-Based Scheduling
- Validates date/time exists in clinic schedule
- Checks patient duplicate bookings
- Calculates required consecutive slots
- Prevents overlapping appointments

### Service Duration Example
**Root Canal (90 min)**:
- Books at 14:00 → Blocks 14:00, 14:30, 15:00
- Next available: 15:30

### Smart Alternatives
- If requested slot unavailable, suggests up to 5 alternatives
- Considers service duration for all suggestions

---

## 🌍 Arabic Support

Handles various Arabic formats:
- Arabic numerals: ٠-٩ → 0-9
- Time indicators: صباحا/مساءً → am/pm
- **Example**: `٢:٣٠ مساءً` → `14:30`

---

## ❌ Error Handling

- **400**: Invalid format, booking rules violated
- **404**: Appointment not found
- **409**: Slot already booked, patient duplicate

---

## 🎯 Realistic Features

✅ Single dental room (no simultaneous bookings)  
✅ Service duration-aware  
✅ Business hours enforcement  
✅ Lunch break handling  
✅ Advance booking rules  
✅ Cancellation policy  
✅ Duplicate prevention  

---

## 📝 License

MIT License

## 👤 Author

**Tala** - [@asfantala](https://github.com/asfantala)

## 🔗 Links

- **Repository**: https://github.com/asfantala/scheduleAPI
- **Live API**: https://web-production-b2126.up.railway.app
- **Docs**: https://web-production-b2126.up.railway.app/docs

---

**Status**: ✅ Production-Ready | 🚀 Deployed on Railway

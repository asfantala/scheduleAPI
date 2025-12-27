# 🦷 Simple Dental Appointment API

Super simple - Only 4 endpoints! All appointments auto-saved to JSON.

## 🎯 The 4 Endpoints

### 1️⃣ CREATE - Book Appointment
```
POST /appointments
```
Book a new dental appointment with just 5 required fields.

### 2️⃣ READ - Get Appointments  
```
GET /appointments
GET /appointments?date=2026-01-20
```
Get all appointments, optionally filter by date.

### 3️⃣ UPDATE - Modify Appointment
```
PUT /appointments/{appointment_id}
```
Update appointment details (date, time, notes, etc).

### 4️⃣ DELETE - Cancel Appointment
```
DELETE /appointments/{appointment_id}
```
Cancel an appointment (24hr advance notice required).

---

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload
```

Server runs at: **http://localhost:8000**  
Docs at: **http://localhost:8000/docs**

---

## 📝 Example Usage

### Book an Appointment
```bash
curl -X POST http://localhost:8000/appointments \
  -H "Content-Type: application/json" \
  -d '{
    "service": "Dental Cleaning",
    "patient_name": "John Doe",
    "phone": "0791234567",
    "appointment_date": "2026-01-20",
    "time": "09:00"
  }'
```

### Get All Appointments
```bash
curl http://localhost:8000/appointments
```

### Get Appointments by Date
```bash
curl http://localhost:8000/appointments?date=2026-01-20
```

### Update Appointment
```bash
curl -X PUT http://localhost:8000/appointments/{id} \
  -H "Content-Type: application/json" \
  -d '{"time": "10:00", "notes": "Rescheduled"}'
```

### Cancel Appointment
```bash
curl -X DELETE http://localhost:8000/appointments/{id}
```

---

## ✨ Features

✅ **Only 4 simple endpoints**  
✅ **Auto-saves to JSON file** (`appointments.json`)  
✅ **Full CRUD operations**  
✅ **Validates business rules** (24hr advance booking, etc)  
✅ **Prevents double-booking**  
✅ **Flexible time formats** (9:00, 2:00 PM, 14:00)  
✅ **Clean & simple code**  

---

## 📋 Required Fields

- `service` - Dental service type  
- `patient_name` - Patient's name  
- `phone` - Phone number (07XXXXXXXX)  
- `appointment_date` - Date (YYYY-MM-DD)  
- `time` - Time (HH:MM or 12hr format)  

Optional: `email`, `insurance_provider`, `notes`

---

### 3. Get All Appointments - `GET /appointments`

Retrieve all booked appointments (admin endpoint).

**Query Parameters:**
- `date` (optional) - Filter by date (YYYY-MM-DD)

**Example:**
## 🚀 That's It!

Your API now has:
- ✅ Only 4 clean endpoints
- ✅ Auto-saves to JSON file
- ✅ Full CRUD functionality
- ✅ Simple and easy to use

**Interactive Docs**: http://localhost:8000/docs 🎉

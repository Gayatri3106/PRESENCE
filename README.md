# Presence — Full Student Attendance Website

Presence is a full-stack classroom attendance website built around the SaveState visual frontend style and the existing Presence face-recognition backend.

## Main workflow

### Faculty
1. Faculty logs in using an existing teacher account. There is no teacher registration page.
2. Faculty details shown in the dashboard include mail ID, subject, period start and period end.
3. Faculty selects the class and creates an attendance room.
4. A unique room code is generated.
5. The room is valid for **2 minutes** and the Flask backend enforces the expiry.
6. A QR code is displayed automatically.
7. The QR token changes every **30 seconds**.
8. Faculty can close the room and download the Excel attendance report.

### Student
1. A student registers once with name, email, roll number and a live face capture.
2. The backend creates a **128-dimensional dlib face embedding** and stores it in Supabase.
3. The student logs in using roll number + email.
4. Student enters the faculty room code.
5. Student scans the **current faculty QR** with the camera.
6. Student opens the live front camera and captures the face.
7. Backend generates a new 128-D embedding and compares it to the stored embedding using Euclidean distance.
8. Attendance is marked only if the room, QR token, student identity and face verification all pass.

## Project structure

```text
Presence/
├── Frontend/        # Next.js + React + Tailwind, SaveState-style UI
│   ├── app/
│   │   ├── page.js
│   │   ├── login/
│   │   ├── signup/
│   │   ├── dashboard/
│   │   ├── admin/login/
│   │   ├── admin/dashboard/
│   │   ├── lib/api.js
│   │   └── globals.css
│   ├── .env.example
│   └── package.json
├── Backend/         # Flask + dlib + Supabase
│   ├── app.py
│   ├── supabase_client.py
│   ├── face_pipeline.py
│   ├── room_code.py
│   ├── config.py
│   ├── schema_migration.sql
│   ├── requirements.txt
│   └── models/
└── README.md
```

## 1. Supabase

Run `Backend/schema_migration.sql` in the Supabase SQL editor.

The existing database must contain the student, faculty, class, attendance session and attendance record tables expected by the backend. Every student used in Excel absent/present reports should have its `class_id` populated.

Create `Backend/.env` from `.env.example` and set:

```env
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_KEY=YOUR_ANON_KEY
SUPABASE_SERVICE_KEY=YOUR_SERVICE_ROLE_KEY
FLASK_SECRET_KEY=USE_A_LONG_RANDOM_SECRET
FLASK_DEBUG=false
FACE_MATCH_THRESHOLD=0.45
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Never commit the service-role key.

## 2. Backend — Windows CMD

```cmd
cd Presence\Backend
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
notepad .env
python app.py
```

Backend health check:

```text
http://127.0.0.1:5000/api/health
```

## 3. Frontend — Windows CMD

Open a second terminal:

```cmd
cd Presence\Frontend
copy .env.example .env.local
notepad .env.local
npm install
npm run dev
```

Set:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:5000
```

Open:

```text
http://localhost:3000
```

## Face recognition

The backend uses the supplied dlib models:

- `shape_predictor_68_face_landmarks.dat`
- `dlib_face_recognition_resnet_model_v1.dat`

The current configured face threshold is 0.45. This value should be experimentally calibrated before claiming a production accuracy figure.

## Important camera requirement

Camera access works on `localhost` during local development. For a deployed site, serve the frontend over HTTPS.

The student QR scanner uses the browser `BarcodeDetector` API. A recent Chrome/Edge browser is recommended. The QR token itself is signed by the Flask backend and is accepted only for the current 30-second token bucket.

## Security behavior

Attendance cannot be created by only knowing a roll number or room code. The backend checks:

`Active Session AND Valid Room Code AND Current QR Token AND Student Record AND Matching Face`

A failed face match does not create an attendance record.

## Excel report

Faculty can download `/api/session/<session_id>/export`. The generated workbook includes student status, attendance time and session metadata. The expiry scheduler also closes expired rooms automatically.

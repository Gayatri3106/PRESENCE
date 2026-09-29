"""Supabase data-access layer for Presence."""
import logging
from datetime import datetime, timezone
from supabase import create_client, Client
from config import config

logger = logging.getLogger(__name__)
_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be configured.")
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
    return _client


def first(resp):
    return resp.data[0] if resp.data else None

# Students

def get_student_by_email(email):
    return first(get_client().table("students").select("*").eq("email", email).execute())


def get_student_by_id(student_id):
    return first(get_client().table("students").select("*").eq("id", student_id).execute())


def get_student_by_roll_no(roll_no):
    return first(get_client().table("students").select("*").eq("roll_no", roll_no).execute())


def create_student(name, email, roll_no):
    return first(get_client().table("students").insert({"name": name, "email": email, "roll_no": roll_no}).execute()) or (_ for _ in ()).throw(ValueError("Unable to create student record."))


def update_student_identity(student_id, name, email, roll_no):
    get_client().table("students").update({"name": name, "email": email, "roll_no": roll_no}).eq("id", student_id).execute()


def update_student_embedding(student_id, embedding):
    resp = get_client().table("students").update({"face_embedding": embedding}).eq("id", student_id).execute()
    if not resp.data:
        raise ValueError("Student embedding could not be saved.")


def get_students_by_class(class_id):
    resp = get_client().table("students").select("id,name,email,roll_no,class_id").eq("class_id", class_id).execute()
    return resp.data or []

# Faculty

def get_faculty_by_id(faculty_id):
    return first(get_client().table("faculty").select("*").eq("id", faculty_id).execute())


def get_faculty_by_email(email):
    return first(get_client().table("faculty").select("*").eq("email", email).execute())


def get_classes_for_faculty(faculty_id):
    resp = get_client().table("classes").select("*").eq("faculty_id", faculty_id).execute()
    return resp.data or []

# Sessions

def create_session(class_id, faculty_id, subject, period_start, period_end, room_code, expires_at):
    payload = {
        "class_id": class_id,
        "faculty_id": faculty_id,
        "subject": subject,
        "period_start": period_start,
        "period_end": period_end,
        "room_code": room_code,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at.isoformat(),
        "status": "active",
    }
    resp = get_client().table("attendance_sessions").insert(payload).execute()
    return first(resp) or (_ for _ in ()).throw(ValueError("Unable to create attendance session."))


def get_session_by_id(session_id):
    return first(get_client().table("attendance_sessions").select("*").eq("id", session_id).execute())


def get_active_session(session_id):
    return first(get_client().table("attendance_sessions").select("*").eq("id", session_id).eq("status", "active").execute())


def get_active_session_for_class(class_id):
    return first(get_client().table("attendance_sessions").select("*").eq("class_id", class_id).eq("status", "active").execute())


def get_expired_active_sessions():
    resp = get_client().table("attendance_sessions").select("*").eq("status", "active").lt("expires_at", datetime.now(timezone.utc).isoformat()).execute()
    return resp.data or []


def close_session(session_id):
    get_client().table("attendance_sessions").update({"status": "closed"}).eq("id", session_id).execute()


def validate_room_code(room_code):
    session = first(get_client().table("attendance_sessions").select("*").eq("room_code", room_code).eq("status", "active").execute())
    if not session:
        return None
    expires = datetime.fromisoformat(str(session["expires_at"]).replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) >= expires:
        close_session(session["id"])
        return None
    return session

# Attendance

def create_attendance_record(session_id, student_id, match_distance, status, method="qr+face"):
    resp = get_client().table("attendance_records").insert({
        "session_id": session_id,
        "student_id": student_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "match_distance": match_distance,
        "status": status,
        "method": method,
    }).execute()
    return first(resp) or (_ for _ in ()).throw(ValueError("Unable to create attendance record."))


def student_already_checked_in(session_id, student_id):
    resp = get_client().table("attendance_records").select("id").eq("session_id", session_id).eq("student_id", student_id).execute()
    return bool(resp.data)


def get_records_for_session(session_id):
    resp = get_client().table("attendance_records").select("*, students(name,roll_no,email)").eq("session_id", session_id).order("timestamp").execute()
    return resp.data or []


def get_attendance_for_student(student_id):
    resp = get_client().table("attendance_records").select("*, attendance_sessions(class_id,subject,period_start,period_end)").eq("student_id", student_id).order("timestamp", desc=True).execute()
    return resp.data or []


def get_class_attendance_stats(class_id):
    students = get_students_by_class(class_id)
    sessions = get_client().table("attendance_sessions").select("id").eq("class_id", class_id).execute().data or []
    total = len(sessions)
    if not students:
        return []
    ids = [s["id"] for s in sessions]
    result = []
    for student in students:
        present = 0
        if ids:
            rows = get_client().table("attendance_records").select("id").eq("student_id", student["id"]).in_("session_id", ids).eq("status", "present").execute().data or []
            present = len(rows)
        result.append({"student_id": student["id"], "name": student.get("name"), "roll_no": student.get("roll_no"), "present": present, "total_sessions": total, "percentage": round(present * 100 / total, 1) if total else 0})
    return result

-- Presence attendance-session migration
-- Run this in Supabase SQL Editor before using the new teacher/session workflow.

alter table public.attendance_sessions
  add column if not exists faculty_id uuid references public.faculty(id),
  add column if not exists subject text,
  add column if not exists period_start text,
  add column if not exists period_end text;

create index if not exists attendance_sessions_active_class_idx
  on public.attendance_sessions(class_id, status);

create index if not exists attendance_sessions_room_code_idx
  on public.attendance_sessions(room_code);

create index if not exists attendance_records_session_idx
  on public.attendance_records(session_id);

create index if not exists attendance_records_student_idx
  on public.attendance_records(student_id);

-- Prevent the same student from being marked twice in one session.
create unique index if not exists attendance_records_session_student_uidx
  on public.attendance_records(session_id, student_id);

-- Recommended identity constraints.
create unique index if not exists students_roll_no_uidx
  on public.students(roll_no);

create unique index if not exists students_email_uidx
  on public.students(email);

-- Make sure face_embedding can hold the 128 floating-point values.
-- If this column already exists as jsonb, leave it unchanged.
-- If your current column is text, migrate it separately after checking existing data.

-- IMPORTANT FOR ABSENT REPORTS:
-- Every student who belongs to a class must have students.class_id set to that class.
-- The Excel generator uses students in the selected class as the complete attendance list.

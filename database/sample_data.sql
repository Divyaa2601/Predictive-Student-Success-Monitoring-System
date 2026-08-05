-- =========================================================
-- PREDICTIVE STUDENT SUCCESS MONITORING SYSTEM
-- SAMPLE DATA
-- =========================================================

USE student_success_db;


-- =========================================================
-- 1. SAMPLE USERS
-- =========================================================
-- Passwords are temporary placeholders for database testing.
-- Proper hashed passwords will be handled by Flask later.

INSERT INTO users (username, password_hash, role)
VALUES
('faculty01', 'temporary_password', 'faculty'),
('student01', 'temporary_password', 'student'),
('student02', 'temporary_password', 'student'),
('student03', 'temporary_password', 'student');


-- =========================================================
-- 2. SAMPLE FACULTY
-- =========================================================

INSERT INTO faculty (
    user_id,
    faculty_name,
    email,
    department
)
VALUES (
    (SELECT user_id FROM users WHERE username = 'faculty01'),
    'Dr. Priya Kumar',
    'priya.faculty@example.com',
    'Artificial Intelligence and Machine Learning'
);


-- =========================================================
-- 3. SAMPLE STUDENTS
-- =========================================================

INSERT INTO students (
    user_id,
    register_number,
    student_name,
    email,
    department,
    semester
)
VALUES

(
    (SELECT user_id FROM users WHERE username = 'student01'),
    'AIML001',
    'Arun Kumar',
    'arun.student@example.com',
    'Artificial Intelligence and Machine Learning',
    5
),

(
    (SELECT user_id FROM users WHERE username = 'student02'),
    'AIML002',
    'Meena Ravi',
    'meena.student@example.com',
    'Artificial Intelligence and Machine Learning',
    5
),

(
    (SELECT user_id FROM users WHERE username = 'student03'),
    'AIML003',
    'Rahul S',
    'rahul.student@example.com',
    'Artificial Intelligence and Machine Learning',
    5
);


-- =========================================================
-- 4. ACADEMIC RECORD — STUDENT 1
-- Strong academic performance
-- =========================================================

INSERT INTO academic_records (
    student_id,
    semester,
    previous_gpa,
    attendance_pct,
    internal_1,
    internal_2,
    assignment_avg,
    assignment_completion_pct,
    quiz_avg,
    study_hours_weekly,
    class_participation,
    late_submissions
)
VALUES (
    (SELECT student_id
     FROM students
     WHERE register_number = 'AIML001'),

    5,
    8.40,
    91.00,
    82.00,
    85.00,
    86.00,
    95.00,
    80.00,
    15.00,
    8.00,
    0
);


-- =========================================================
-- 5. ACADEMIC RECORD — STUDENT 2
-- Moderate academic performance
-- =========================================================

INSERT INTO academic_records (
    student_id,
    semester,
    previous_gpa,
    attendance_pct,
    internal_1,
    internal_2,
    assignment_avg,
    assignment_completion_pct,
    quiz_avg,
    study_hours_weekly,
    class_participation,
    late_submissions
)
VALUES (
    (SELECT student_id
     FROM students
     WHERE register_number = 'AIML002'),

    5,
    6.50,
    73.00,
    58.00,
    53.00,
    60.00,
    68.00,
    52.00,
    10.00,
    5.00,
    3
);


-- =========================================================
-- 6. ACADEMIC RECORD — STUDENT 3
-- Weak academic performance
-- =========================================================

INSERT INTO academic_records (
    student_id,
    semester,
    previous_gpa,
    attendance_pct,
    internal_1,
    internal_2,
    assignment_avg,
    assignment_completion_pct,
    quiz_avg,
    study_hours_weekly,
    class_participation,
    late_submissions
)
VALUES (
    (SELECT student_id
     FROM students
     WHERE register_number = 'AIML003'),

    5,
    5.20,
    65.00,
    36.00,
    37.00,
    55.00,
    60.00,
    28.00,
    7.00,
    3.00,
    5
);


-- =========================================================
-- VERIFY SAMPLE DATA
-- =========================================================

SELECT * FROM users;

SELECT * FROM faculty;

SELECT * FROM students;

SELECT * FROM academic_records;
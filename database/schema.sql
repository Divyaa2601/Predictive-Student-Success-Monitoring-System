-- =========================================================
-- PREDICTIVE STUDENT SUCCESS MONITORING SYSTEM
-- DATABASE SCHEMA
-- =========================================================

CREATE DATABASE IF NOT EXISTS student_success_db;

USE student_success_db;


-- =========================================================
-- 1. USERS
-- Stores login information for faculty and students
-- =========================================================

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,

    role ENUM(
        'faculty',
        'student'
    ) NOT NULL,

    student_id INT NULL,

    password_hash VARCHAR(255) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_users_student
        FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- =========================================================
-- 2. STUDENTS
-- Basic student profile information
-- =========================================================

CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    register_number VARCHAR(50) NOT NULL UNIQUE,
    student_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE,
    department VARCHAR(100),
    semester INT NOT NULL,

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);


-- =========================================================
-- 3. FACULTY
-- Faculty profile information
-- =========================================================

CREATE TABLE faculty (
    faculty_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    faculty_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE,
    department VARCHAR(100),

    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);


-- =========================================================
-- 4. ACADEMIC RECORDS
-- Stores the ML input features for each student
-- =========================================================

CREATE TABLE academic_records (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,

    semester INT NOT NULL,

    previous_gpa DECIMAL(4,2),

    attendance_pct DECIMAL(5,2),

    internal_1 DECIMAL(5,2),
    internal_2 DECIMAL(5,2),

    assignment_avg DECIMAL(5,2),
    assignment_completion_pct DECIMAL(5,2),

    quiz_avg DECIMAL(5,2),

    study_hours_weekly DECIMAL(5,2),

    class_participation DECIMAL(5,2),

    late_submissions INT DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE
);


-- =========================================================
-- 5. PREDICTIONS
-- Stores model predictions and probabilities
-- =========================================================

CREATE TABLE predictions (
    prediction_id INT AUTO_INCREMENT PRIMARY KEY,

    student_id INT NOT NULL,
    record_id INT NOT NULL,

    risk_level ENUM(
        'Low',
        'Medium',
        'High'
    ) NOT NULL,

    high_probability DECIMAL(5,2),
    medium_probability DECIMAL(5,2),
    low_probability DECIMAL(5,2),

    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,

    FOREIGN KEY (record_id)
        REFERENCES academic_records(record_id)
        ON DELETE CASCADE
);


-- =========================================================
-- 6. RISK FACTORS
-- Stores SHAP explanation results
-- =========================================================

CREATE TABLE risk_factors (
    risk_factor_id INT AUTO_INCREMENT PRIMARY KEY,

    prediction_id INT NOT NULL,

    feature_name VARCHAR(100) NOT NULL,

    feature_value DECIMAL(10,2),

    shap_impact DECIMAL(10,6),

    factor_rank INT,

    FOREIGN KEY (prediction_id)
        REFERENCES predictions(prediction_id)
        ON DELETE CASCADE
);


-- =========================================================
-- 7. INTERVENTIONS
-- Stores personalized recommendations
-- =========================================================

CREATE TABLE interventions (
    intervention_id INT AUTO_INCREMENT PRIMARY KEY,

    prediction_id INT NOT NULL,

    feature_name VARCHAR(100),

    intervention_title VARCHAR(200),

    recommendation TEXT NOT NULL,

    priority ENUM(
        'Routine',
        'Moderate',
        'Immediate'
    ) NOT NULL,

    status ENUM(
        'Pending',
        'In Progress',
        'Completed'
    ) DEFAULT 'Pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (prediction_id)
        REFERENCES predictions(prediction_id)
        ON DELETE CASCADE
);


-- =========================================================
-- 8. PROGRESS TRACKING
-- Tracks intervention follow-up
-- =========================================================

CREATE TABLE progress_tracking (
    progress_id INT AUTO_INCREMENT PRIMARY KEY,

    student_id INT NOT NULL,
    intervention_id INT,

    progress_note TEXT,

    status ENUM(
        'Pending',
        'In Progress',
        'Completed'
    ) DEFAULT 'Pending',

    updated_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,

    FOREIGN KEY (intervention_id)
        REFERENCES interventions(intervention_id)
        ON DELETE SET NULL
);
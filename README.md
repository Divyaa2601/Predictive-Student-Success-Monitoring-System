# Predictive Student Success Monitoring System

A machine-learning-based web application for predicting student academic risk, providing personalized interventions, and monitoring student progress.

## Table of Contents

- [Overview](#overview)
- [Objectives](#objectives)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Dataset](#dataset)
- [Machine Learning Model](#machine-learning-model)
- [Database Design](#database-design)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
- [Application Workflow](#application-workflow)
- [Testing and Validation](#testing-and-validation)
- [Limitations](#limitations)
- [Future Enhancements](#future-enhancements)
- [Conclusion](#conclusion)

## Overview

The Predictive Student Success Monitoring System is designed to identify students who may be at academic risk and support timely educational interventions.

The application combines machine learning, a Flask web interface, and a MySQL database to classify academic risk, display prediction probabilities, generate personalized recommendations, and track intervention progress.

It provides separate interfaces for students and faculty, with role-based authentication and student-specific data access.

## Objectives

- Predict academic risk using student performance indicators.
- Classify students into Low, Medium, and High risk categories.
- Display risk probabilities and historical predictions.
- Provide personalized interventions based on identified risk factors.
- Enable faculty to monitor students within their assigned department.
- Record progress notes and track intervention statuses.
- Maintain role-based access to student and faculty functionality.

## Features

### Student Module

- Secure login and logout.
- Student-specific academic dashboard.
- Academic risk prediction and probability display.
- Prediction history.
- Personalized interventions and recommendations.
- Progress notes and intervention-status tracking.

### Faculty Module

- Faculty authentication.
- Department-filtered student dashboard.
- Student academic and prediction information.
- Intervention and progress monitoring.
- Role-based access control.

### Machine Learning Module

- Academic risk classification.
- Missing-value preprocessing.
- Feature preparation and scaling.
- Risk probability output.
- Reuse of saved model and preprocessing artifacts.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Web framework | Flask |
| Database | MySQL |
| Frontend | HTML, CSS, Jinja2 |
| Machine learning | scikit-learn |
| Data processing | pandas, NumPy |
| Authentication | Flask-Login |
| Password hashing | Werkzeug |
| Development environment | Visual Studio Code |

## System Architecture

The application is organized into four logical layers:

1. **Presentation layer:** HTML templates and CSS provide the user interface.
2. **Application layer:** Flask manages authentication, application routes, database operations, and dashboard logic.
3. **Machine learning layer:** The saved model and preprocessing components generate academic risk predictions.
4. **Database layer:** MySQL stores users, student profiles, academic records, predictions, interventions, and progress updates.

## Dataset

The project uses a synthetic academic dataset containing 2,000 student records for model development and demonstration.

The dataset includes academic and engagement-related attributes such as:

- Previous GPA
- Internal assessment marks
- Assignment average
- Quiz average
- Attendance percentage
- Weekly study hours
- Classroom participation
- Risk-level labels

The dataset also contains a derived feature representing changes between internal assessments.

Selected missing numerical values are handled through the project's preprocessing workflow.

### Dataset Limitations

The dataset is synthetic and does not represent verified academic outcomes from a real institution. Predictions should be interpreted as decision-support information, not definitive judgments about a student's future performance.

Performance on synthetic data may not generalize to real-world student populations.

## Machine Learning Model

The application classifies student academic risk into three categories:

- **Low Risk**
- **Medium Risk**
- **High Risk**

The inference workflow prepares input features, applies the saved preprocessing components, and produces a predicted risk category and associated probabilities.

The saved artifacts are maintained in the `models/` directory:

- `student_risk_model.pkl`
- `imputer.pkl`
- `scaler.pkl`
- `feature_names.pkl`

The existing artifacts are loaded for prediction. Retraining is not required for ordinary application startup, provided the required files and compatible dependencies are available.

## Database Design

The application uses the MySQL database `student_success_db`.

| Table | Purpose |
|---|---|
| `users` | Usernames, password hashes, roles, and account links |
| `students` | Student profile information |
| `faculty` | Faculty information and department association |
| `academic_records` | Academic performance information |
| `predictions` | Risk classifications, probabilities, and timestamps |
| `interventions` | Recommendations, priorities, and intervention statuses |
| `progress_tracking` | Progress notes, statuses, and update timestamps |
| `risk_factors` | Risk-related information used by the application |

Database identifiers link students to their academic records, predictions, interventions, and progress-tracking entries.

The database schema SQL file is available in the `database/` directory.

## Project Structure

```text
Predictive-Student-Success-Monitoring-System/
├── app/
│   ├── app.py
│   └── templates/
├── data/
│   └── student_success_dataset.csv
├── database/
│   └── [database schema SQL file]
├── ml/
│   └── predictor.py
├── models/
│   ├── student_risk_model.pkl
│   ├── imputer.pkl
│   ├── scaler.pkl
│   └── feature_names.pkl
├── notebooks/
├── venv/
├── requirements.txt
└── README.md
```

This is a simplified overview. Update the structure to match the actual repository before submitting.

## Installation and Setup

### Prerequisites

- Python 3.11 or a compatible Python version.
- MySQL Server.
- MySQL Workbench or another MySQL client.
- Git.
- The project source code and saved model artifacts.

### 1. Clone the repository

```bash
git clone https://github.com/Divyaa2601/Predictive-Student-Success-Monitoring-System.git
cd Predictive-Student-Success-Monitoring-System
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If a compatible virtual environment already exists, activate it instead of recreating it.

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure the database

1. Start MySQL Server.
2. Open MySQL Workbench.
3. Create or select the database `student_success_db`.
4. Execute the project's database schema SQL file from the `database/` directory.
5. Configure the database connection settings used by the Flask application.
6. Ensure the configured MySQL account has the required permissions.

If the database is already configured, verify the connection rather than resetting the existing database.

**Security:** Do not commit database passwords, private configuration files, or real student information to a public repository.

### 5. Verify the model artifacts

Confirm that all required model and preprocessing files exist in the `models/` directory.

The installed scikit-learn version must be compatible with the version used to save the model artifacts.

### 6. Start the Flask application

```powershell
cd app
python app.py
```

Open the local address displayed in the terminal. The application normally runs at:

`http://127.0.0.1:5000`

Keep the terminal open while using the application.

## Application Workflow

1. An authorized student or faculty member logs in.
2. The application redirects the user to the appropriate dashboard.
3. Students access their own academic information, predictions, interventions, and progress records.
4. Faculty access the students assigned to their department.
5. Risk predictions display the predicted category and probability values.
6. Previous predictions can be reviewed through prediction history.
7. Intervention statuses and progress notes can be updated and verified.

## Testing and Validation

The following functional tests have been completed successfully during project testing:

- Faculty login and logout.
- Student login and logout.
- Faculty dashboard displaying 53 students.
- Student-specific data isolation.
- Risk prediction and probability display.
- Prediction history.
- Intervention-status persistence after refresh.
- Progress-note display and persistence.
- Progress-status persistence after refresh.
- No major terminal errors during the tested workflows.

These results describe functional testing of the application. They do not constitute independent validation of model accuracy or production readiness.

## Limitations

- The demonstration dataset is synthetic.
- Prediction quality depends on the input data and the suitability of the trained model.
- Risk categories are estimates and should not replace faculty judgment.
- The application is intended for academic demonstration and further evaluation.

## Future Enhancements

- Evaluate the model with appropriately authorized real-world academic data.
- Improve model evaluation and probability calibration.
- Add notifications for students who may need support.
- Introduce progress visualizations and analytical reports.
- Strengthen deployment security and operational monitoring.
- Evaluate usability with students and faculty.

## Conclusion

The Predictive Student Success Monitoring System demonstrates the integration of machine learning, web development, and database management for academic risk prediction and intervention tracking.

By connecting risk classification with personalized recommendations and progress monitoring, the system provides a foundation for proactive academic support.

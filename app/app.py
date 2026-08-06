import os
import sys

from flask import (
    Flask,
    jsonify,
    request,
    render_template,
    redirect,
    url_for,
    flash
)

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import check_password_hash

import mysql.connector
from dotenv import load_dotenv


# =========================================================
# PROJECT PATH CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


from ml.predictor import predict_student_risk
from ml.intervention_engine import generate_interventions


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

ENV_PATH = os.path.join(
    BASE_DIR,
    ".env"
)

load_dotenv(ENV_PATH)


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "development-secret-key"
)


# =========================================================
# FLASK LOGIN CONFIGURATION
# =========================================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

login_manager.login_message = (
    "Please login to access this page."
)

login_manager.login_message_category = "warning"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(
            os.getenv(
                "DB_PORT",
                3306
            )
        ),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


# =========================================================
# USER MODEL
# =========================================================

class User(UserMixin):

    def __init__(
        self,
        user_id,
        username,
        role,
        student_id=None
    ):

        self.id = str(user_id)

        self.username = username

        self.role = role

        self.student_id = student_id


# =========================================================
# FLASK LOGIN USER LOADER
# =========================================================

@login_manager.user_loader
def load_user(user_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                user_id,
                username,
                role,
                student_id
            FROM users
            WHERE user_id = %s;
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if user is None:
            return None

        return User(
            user_id=user["user_id"],
            username=user["username"],
            role=user["role"],
            student_id=user["student_id"]
        )

    finally:

        if cursor is not None:
            cursor.close()

        if (
            connection is not None
            and connection.is_connected()
        ):
            connection.close()

# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    # -----------------------------------------------------
    # Already logged in
    # -----------------------------------------------------

    if current_user.is_authenticated:

        if current_user.role == "faculty":
            return redirect(
                url_for("faculty_dashboard")
            )

        elif current_user.role == "student":
            return redirect(
                url_for("student_dashboard")
            )

        logout_user()

        flash(
            "Invalid user role.",
            "error"
        )

        return redirect(
            url_for("login")
        )


    # -----------------------------------------------------
    # Handle login form
    # -----------------------------------------------------

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        # -------------------------------------------------
        # Validate input
        # -------------------------------------------------

        if not username or not password:

            flash(
                "Username and password are required.",
                "error"
            )

            return render_template(
                "login.html"
            )


        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT
                    user_id,
                    username,
                    password_hash,
                    role,
                    student_id
                FROM users
                WHERE username = %s;
                """,
                (username,)
            )

            user_record = cursor.fetchone()


            # -------------------------------------------------
            # Verify username and password
            # -------------------------------------------------

            if (
                user_record is None
                or not check_password_hash(
                    user_record["password_hash"],
                    password
                )
            ):

                flash(
                    "Invalid username or password.",
                    "error"
                )

                return render_template(
                    "login.html"
                )


            # -------------------------------------------------
            # Create authenticated user
            # -------------------------------------------------

            user = User(
                user_id=user_record["user_id"],
                username=user_record["username"],
                role=user_record["role"],
                student_id=user_record["student_id"]
            )

            login_user(user)


            # -------------------------------------------------
            # Role-based redirect
            # -------------------------------------------------

            if user.role == "faculty":

                return redirect(
                    url_for(
                        "faculty_dashboard"
                    )
                )


            elif user.role == "student":

                if user.student_id is None:

                    logout_user()

                    flash(
                        "Student account is not linked "
                        "to a student record.",
                        "error"
                    )

                    return redirect(
                        url_for("login")
                    )


                return redirect(
                    url_for(
                        "student_dashboard"
                    )
                )


            # -------------------------------------------------
            # Invalid role
            # -------------------------------------------------

            logout_user()

            flash(
                "Invalid user role.",
                "error"
            )

            return redirect(
                url_for("login")
            )


        except Exception as error:

            print(
                "Login error:",
                error
            )

            flash(
                "Unable to login. Please try again.",
                "error"
            )

            return render_template(
                "login.html"
            ), 500


        finally:

            if cursor is not None:
                cursor.close()

            if (
                connection is not None
                and connection.is_connected()
            ):
                connection.close()


    # -----------------------------------------------------
    # GET /login
    # -----------------------------------------------------

    return render_template(
        "login.html"
    )
# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("login")
    )


# =========================================================
# FACULTY DASHBOARD
# =========================================================

@app.route("/faculty/dashboard")
@login_required
def faculty_dashboard():

    # -----------------------------------------------------
    # Role protection
    # -----------------------------------------------------

    if current_user.role != "faculty":

        flash(
            "You are not authorized to access "
            "the faculty dashboard.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )


    connection = None
    cursor = None

    try:

        # -------------------------------------------------
        # Database connection
        # -------------------------------------------------

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # Get all students with latest academic record
        # and latest saved prediction
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                s.student_id,
                s.register_number,
                s.student_name,
                s.email,
                s.department,
                s.semester,

                ar.previous_gpa,
                ar.attendance_pct,
                ar.internal_1,
                ar.internal_2,
                ar.assignment_avg,
                ar.quiz_avg,

                p.prediction_id,
                p.risk_level,
                p.high_probability,
                p.medium_probability,
                p.low_probability,
                p.predicted_at

            FROM students s

            LEFT JOIN academic_records ar
                ON ar.record_id = (
                    SELECT ar2.record_id
                    FROM academic_records ar2
                    WHERE ar2.student_id = s.student_id
                    ORDER BY
                        ar2.created_at DESC,
                        ar2.record_id DESC
                    LIMIT 1
                )

            LEFT JOIN predictions p
                ON p.prediction_id = (
                    SELECT p2.prediction_id
                    FROM predictions p2
                    WHERE p2.student_id = s.student_id
                    ORDER BY
                        p2.predicted_at DESC,
                        p2.prediction_id DESC
                    LIMIT 1
                )

            ORDER BY s.student_id;
            """
        )

        student_rows = cursor.fetchall()

        students = []


        # -------------------------------------------------
        # Convert database rows into Python dictionaries
        # -------------------------------------------------

        for row in student_rows:

            student = {

                "student_id":
                    row["student_id"],

                "register_number":
                    row["register_number"],

                "student_name":
                    row["student_name"],

                "email":
                    row["email"],

                "department":
                    row["department"],

                "semester":
                    row["semester"],


                # -----------------------------------------
                # Academic information
                # -----------------------------------------

                "previous_gpa":
                    (
                        float(row["previous_gpa"])
                        if row["previous_gpa"] is not None
                        else None
                    ),

                "attendance_pct":
                    (
                        float(row["attendance_pct"])
                        if row["attendance_pct"] is not None
                        else None
                    ),

                "internal_1":
                    (
                        float(row["internal_1"])
                        if row["internal_1"] is not None
                        else None
                    ),

                "internal_2":
                    (
                        float(row["internal_2"])
                        if row["internal_2"] is not None
                        else None
                    ),

                "assignment_avg":
                    (
                        float(row["assignment_avg"])
                        if row["assignment_avg"] is not None
                        else None
                    ),

                "quiz_avg":
                    (
                        float(row["quiz_avg"])
                        if row["quiz_avg"] is not None
                        else None
                    ),


                # -----------------------------------------
                # Prediction information
                # -----------------------------------------

                "prediction_id":
                    row["prediction_id"],

                "risk_level":
                    row["risk_level"],

                "probabilities": {

                    "High":
                        (
                            float(row["high_probability"])
                            if row["high_probability"] is not None
                            else None
                        ),

                    "Medium":
                        (
                            float(row["medium_probability"])
                            if row["medium_probability"] is not None
                            else None
                        ),

                    "Low":
                        (
                            float(row["low_probability"])
                            if row["low_probability"] is not None
                            else None
                        )
                },

                "predicted_at":
                    (
                        row["predicted_at"].isoformat()
                        if row["predicted_at"] is not None
                        else None
                    )
            }

            students.append(student)


        # -------------------------------------------------
        # Dashboard statistics
        # -------------------------------------------------

        total_students = len(students)


        high_risk_count = sum(
            1
            for student in students
            if student["risk_level"] == "High"
        )


        medium_risk_count = sum(
            1
            for student in students
            if student["risk_level"] == "Medium"
        )


        low_risk_count = sum(
            1
            for student in students
            if student["risk_level"] == "Low"
        )


        not_analyzed_count = sum(
            1
            for student in students
            if student["risk_level"] is None
        )


        # -------------------------------------------------
        # Create dashboard summary
        # -------------------------------------------------

        summary = {

            "total_students":
                total_students,

            "high_risk":
                high_risk_count,

            "medium_risk":
                medium_risk_count,

            "low_risk":
                low_risk_count,

            "not_analyzed":
                not_analyzed_count
        }


        # -------------------------------------------------
        # Render Faculty Dashboard
        # -------------------------------------------------

        return render_template(
            "faculty_dashboard.html",
            faculty=current_user,
            summary=summary,
            students=students
        )


    # -----------------------------------------------------
    # Error handling
    # -----------------------------------------------------

    except Exception as error:

        print(
            "Faculty dashboard error:",
            error
        )

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


    # -----------------------------------------------------
    # Close database connection
    # -----------------------------------------------------

    finally:

        if cursor is not None:
            cursor.close()

        if (
            connection is not None
            and connection.is_connected()
        ):
            connection.close()

# =========================================================
# STUDENT ANALYSIS / VIEW DETAILS
# =========================================================

@app.route("/faculty/student/<int:student_id>/analysis")
@login_required
def student_analysis(student_id):

    # -----------------------------------------------------
    # Faculty-only access
    # -----------------------------------------------------

    if current_user.role != "faculty":

        flash(
            "You are not authorized to access this page.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # =================================================
        # 1. GET STUDENT INFORMATION
        # =================================================

        cursor.execute(
            """
            SELECT
                student_id,
                register_number,
                student_name,
                email,
                department,
                semester
            FROM students
            WHERE student_id = %s;
            """,
            (student_id,)
        )

        student = cursor.fetchone()


        if student is None:

            flash(
                "Student not found.",
                "error"
            )

            return redirect(
                url_for("faculty_dashboard")
            )


        # =================================================
        # 2. GET LATEST ACADEMIC RECORD
        # =================================================

        cursor.execute(
            """
            SELECT *
            FROM academic_records
            WHERE student_id = %s
            ORDER BY
                created_at DESC,
                record_id DESC
            LIMIT 1;
            """,
            (student_id,)
        )

        academic_record = cursor.fetchone()


        # =================================================
        # 3. GET LATEST SAVED PREDICTION
        # =================================================

        cursor.execute(
            """
            SELECT *
            FROM predictions
            WHERE student_id = %s
            ORDER BY
                predicted_at DESC,
                prediction_id DESC
            LIMIT 1;
            """,
            (student_id,)
        )

        prediction = cursor.fetchone()


        # -------------------------------------------------
        # Student has not been analyzed yet
        # -------------------------------------------------

        if prediction is None:

            flash(
                "This student has not been analyzed yet.",
                "error"
            )

            return redirect(
                url_for("faculty_dashboard")
            )


        prediction_id = prediction["prediction_id"]


        # =================================================
        # 4. GET SAVED RISK FACTORS
        # =================================================

        cursor.execute(
            """
            SELECT
                risk_factor_id,
                feature_name,
                feature_value,
                shap_impact,
                factor_rank
            FROM risk_factors
            WHERE prediction_id = %s
            ORDER BY
                factor_rank ASC,
                shap_impact DESC;
            """,
            (prediction_id,)
        )

        factor_rows = cursor.fetchall()


        # =================================================
        # 5. GET SAVED INTERVENTIONS
        # =================================================

        cursor.execute(
            """
            SELECT
                intervention_id,
                feature_name,
                intervention_title,
                recommendation,
                priority,
                status,
                created_at
            FROM interventions
            WHERE prediction_id = %s
            ORDER BY intervention_id ASC;
            """,
            (prediction_id,)
        )

        intervention_rows = cursor.fetchall()


        # =================================================
        # 6. CONVERT DECIMAL VALUES
        # =================================================

        if academic_record is not None:

            numeric_academic_fields = [
                "previous_gpa",
                "attendance_pct",
                "internal_1",
                "internal_2",
                "assignment_avg",
                "assignment_completion_pct",
                "quiz_avg",
                "study_hours_weekly",
                "class_participation"
            ]

            for field in numeric_academic_fields:

                if academic_record.get(field) is not None:

                    academic_record[field] = float(
                        academic_record[field]
                    )


        # -------------------------------------------------
        # Prediction probabilities
        # -------------------------------------------------

        probabilities = {

            "High":
                (
                    float(prediction["high_probability"])
                    if prediction["high_probability"] is not None
                    else 0.0
                ),

            "Medium":
                (
                    float(prediction["medium_probability"])
                    if prediction["medium_probability"] is not None
                    else 0.0
                ),

            "Low":
                (
                    float(prediction["low_probability"])
                    if prediction["low_probability"] is not None
                    else 0.0
                )
        }


        # -------------------------------------------------
        # Risk factors
        # -------------------------------------------------

        risk_factors = []

        for factor in factor_rows:

            risk_factors.append({

                "risk_factor_id":
                    factor["risk_factor_id"],

                "feature_name":
                    factor["feature_name"],

                "feature_value":
                    (
                        float(factor["feature_value"])
                        if factor["feature_value"] is not None
                        else None
                    ),

                "shap_impact":
                    (
                        float(factor["shap_impact"])
                        if factor["shap_impact"] is not None
                        else None
                    ),

                "factor_rank":
                    factor["factor_rank"]
            })


        # -------------------------------------------------
        # Interventions
        # -------------------------------------------------

        interventions = []

        for intervention in intervention_rows:

            interventions.append({

                "intervention_id":
                    intervention["intervention_id"],

                "feature_name":
                    intervention["feature_name"],

                "title":
                    intervention["intervention_title"],

                "recommendation":
                    intervention["recommendation"],

                "priority":
                    intervention["priority"],

                "status":
                    intervention["status"],

                "created_at":
                    (
                        intervention["created_at"].isoformat()
                        if intervention["created_at"] is not None
                        else None
                    )
            })


        # =================================================
        # 7. CREATE RISK MESSAGE
        # =================================================

        risk_level = prediction["risk_level"]


        if risk_level == "High":

            risk_message = (
                "The student requires immediate academic "
                "attention. The identified risk factors "
                "should be addressed through a structured "
                "improvement plan and regular faculty "
                "monitoring."
            )

            priority = "Immediate"


        elif risk_level == "Medium":

            risk_message = (
                "The student shows signs of academic "
                "vulnerability. Early corrective actions "
                "are recommended to prevent further decline."
            )

            priority = "Moderate"


        else:

            risk_message = (
                "The student is currently performing "
                "satisfactorily. The focus should be on "
                "maintaining consistent academic performance."
            )

            priority = "Routine"


        # =================================================
        # 8. RENDER STUDENT ANALYSIS PAGE
        # =================================================

        return render_template(
            "student_analysis.html",
            student=student,
            academic=academic_record,
            prediction=prediction,
            probabilities=probabilities,
            risk_factors=risk_factors,
            interventions=interventions,
            risk_message=risk_message,
            priority=priority
        )


    # =====================================================
    # ERROR HANDLING
    # =====================================================

    except Exception as error:

        print(
            "Student analysis error:",
            error
        )

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


    # =====================================================
    # CLOSE DATABASE
    # =====================================================

    finally:

        if cursor is not None:
            cursor.close()

        if (
            connection is not None
            and connection.is_connected()
        ):
            connection.close()

# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/student/dashboard")
@login_required
def student_dashboard():

    if current_user.role != "student":

        flash(
            "You are not authorized to access "
            "the student dashboard.",
            "error"
        )

        return redirect(
            url_for("faculty_dashboard")
        )

    return jsonify({
        "status": "success",
        "message": "Student dashboard access granted.",
        "username": current_user.username,
        "role": current_user.role,
        "student_id": current_user.student_id
    })

# =========================================================
# ACADEMIC RECORD HELPER
# =========================================================

def get_latest_academic_record(
    cursor,
    student_id
):

    """
    Fetch the latest academic record and prepare
    the feature dictionary required by the ML model.
    """

    cursor.execute(
        """
        SELECT
            record_id,
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
        FROM academic_records
        WHERE student_id = %s
        ORDER BY created_at DESC
        LIMIT 1;
        """,
        (student_id,)
    )

    record = cursor.fetchone()

    if record is None:

        return None, None

    student_data = {

        "semester":
            int(record["semester"]),

        "previous_gpa":
            float(record["previous_gpa"]),

        "attendance_pct":
            float(record["attendance_pct"]),

        "internal_1":
            float(record["internal_1"]),

        "internal_2":
            float(record["internal_2"]),

        "assignment_avg":
            float(record["assignment_avg"]),

        "assignment_completion_pct":
            float(
                record[
                    "assignment_completion_pct"
                ]
            ),

        "quiz_avg":
            float(record["quiz_avg"]),

        "study_hours_weekly":
            float(
                record[
                    "study_hours_weekly"
                ]
            ),

        "class_participation":
            float(
                record[
                    "class_participation"
                ]
            ),

        "late_submissions":
            int(
                record[
                    "late_submissions"
                ]
            )
    }

    return record, student_data


# =========================================================
# HOME ROUTE
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "message":
            "Predictive Student Success Monitoring System API",

        "status":
            "running"
    })


# =========================================================
# DATABASE TEST ROUTE
# =========================================================

@app.route("/api/test-db")
def test_database():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            "SELECT DATABASE() AS database_name"
        )

        result = cursor.fetchone()

        return jsonify({
            "status":
                "success",

            "message":
                "Database connected successfully",

            "database":
                result["database_name"]
        })

    except mysql.connector.Error as error:

        return jsonify({
            "status":
                "error",

            "message":
                str(error)
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if (
            connection is not None
            and connection.is_connected()
        ):
            connection.close()


# =========================================================
# GET STUDENTS
# =========================================================

@app.route("/api/students")
def get_students():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                student_id,
                register_number,
                student_name,
                email,
                department,
                semester
            FROM students
            ORDER BY student_id;
            """
        )

        students = cursor.fetchall()

        return jsonify({
            "status":
                "success",

            "count":
                len(students),

            "students":
                students
        })

    except mysql.connector.Error as error:

        return jsonify({
            "status":
                "error",

            "message":
                str(error)
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if (
            connection is not None
            and connection.is_connected()
        ):
            connection.close()


# =========================================================
# PREDICT STUDENT RISK
# =========================================================

@app.route(
    "/api/predict/<int:student_id>"
)
def predict_student(student_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # Get latest academic record + ML input
        # -------------------------------------------------

        record, student_data = (
            get_latest_academic_record(
                cursor,
                student_id
            )
        )

        if record is None:

            return jsonify({
                "status":
                    "error",

                "message":
                    "Academic record not found for this student."
            }), 404


        # -------------------------------------------------
        # ML Prediction
        # -------------------------------------------------

        prediction = predict_student_risk(
            student_data
        )


        # -------------------------------------------------
        # SHAP + Intervention Engine
        # -------------------------------------------------

        intervention_result = (
            generate_interventions(
                student_data
            )
        )


        # -------------------------------------------------
        # Student information
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                register_number,
                student_name
            FROM students
            WHERE student_id = %s;
            """,
            (student_id,)
        )

        student = cursor.fetchone()

        if student is None:

            return jsonify({
                "status":
                    "error",

                "message":
                    "Student not found."
            }), 404


        # -------------------------------------------------
        # Response
        # -------------------------------------------------

        return jsonify({

            "status":
                "success",

            "student": {

                "student_id":
                    student_id,

                "register_number":
                    student[
                        "register_number"
                    ],

                "student_name":
                    student[
                        "student_name"
                    ]
            },

            "prediction":
                prediction,

            "priority":
                intervention_result[
                    "priority"
                ],

            "risk_message":
                intervention_result[
                    "risk_message"
                ],

            "interventions":
                intervention_result[
                    "interventions"
                ]
        })

    except Exception as error:

        return jsonify({
            "status":
                "error",

            "message":
                str(error)
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if (
            connection is not None
            and connection.is_connected()
        ):
            connection.close()


# =========================================================
# ANALYZE AND SAVE STUDENT PREDICTION
# =========================================================


@app.route(
    "/api/predict/<int:student_id>/save",
    methods=["POST"]
)
def save_student_prediction(student_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # Get latest academic record + ML input
        # -------------------------------------------------

        record, student_data = (
            get_latest_academic_record(
                cursor,
                student_id
            )
        )

        if record is None:

            return jsonify({
                "status":
                    "error",

                "message":
                    "Academic record not found for this student."
            }), 404


        # -------------------------------------------------
        # Prediction + interventions
        # -------------------------------------------------

        analysis = generate_interventions(
            student_data
        )

        risk_level = analysis[
            "risk_level"
        ]

        probabilities = analysis[
            "probabilities"
        ]


        # -------------------------------------------------
        # Insert prediction
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO predictions (
                student_id,
                record_id,
                risk_level,
                high_probability,
                medium_probability,
                low_probability
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            );
            """,
            (
                student_id,
                record["record_id"],
                risk_level,
                probabilities.get(
                    "High",
                    0
                ),
                probabilities.get(
                    "Medium",
                    0
                ),
                probabilities.get(
                    "Low",
                    0
                )
            )
        )

        prediction_id = (
            cursor.lastrowid
        )


        # -------------------------------------------------
        # Insert SHAP risk factors
        # -------------------------------------------------

        for rank, factor in enumerate(
            analysis["interventions"],
            start=1
        ):

            cursor.execute(
                """
                INSERT INTO risk_factors (
                    prediction_id,
                    feature_name,
                    feature_value,
                    shap_impact,
                    factor_rank
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                );
                """,
                (
                    prediction_id,
                    factor["feature"],
                    factor["value"],
                    factor["shap_impact"],
                    rank
                )
            )


        # -------------------------------------------------
        # Insert interventions
        # -------------------------------------------------

        for intervention in analysis[
            "interventions"
        ]:

            cursor.execute(
                """
                INSERT INTO interventions (
                    prediction_id,
                    feature_name,
                    intervention_title,
                    recommendation,
                    priority
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                );
                """,
                (
                    prediction_id,
                    intervention[
                        "feature"
                    ],
                    intervention[
                        "title"
                    ],
                    intervention[
                        "recommendation"
                    ],
                    analysis[
                        "priority"
                    ]
                )
            )


        # -------------------------------------------------
        # Commit transaction
        # -------------------------------------------------

        connection.commit()


        return jsonify({

            "status":
                "success",

            "message":
                "Prediction and interventions saved successfully.",

            "prediction_id":
                prediction_id,

            "student_id":
                student_id,

            "risk_level":
                risk_level,

            "probabilities":
                probabilities,

            "priority":
                analysis[
                    "priority"
                ],

            "factors_saved":
                len(
                    analysis[
                        "interventions"
                    ]
                ),

            "interventions_saved":
                len(
                    analysis[
                        "interventions"
                    ]
                )
        })

    except Exception as error:

        if connection is not None:
            connection.rollback()

        return jsonify({
            "status":
                "error",

            "message":
                str(error)
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if (
            connection is not None
            and connection.is_connected()
        ):
            connection.close()

# =========================================================
# ANALYZE STUDENT FROM FACULTY DASHBOARD
# =========================================================

@app.route(
    "/faculty/student/<int:student_id>/analyze",
    methods=["POST"]
)
@login_required
def analyze_student(student_id):

    # -----------------------------------------------------
    # Faculty-only access
    # -----------------------------------------------------

    if current_user.role != "faculty":

        flash(
            "You are not authorized to analyze students.",
            "error"
        )

        return redirect(
            url_for("student_dashboard")
        )


    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # Check whether student exists
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                student_id,
                student_name
            FROM students
            WHERE student_id = %s;
            """,
            (student_id,)
        )

        student = cursor.fetchone()


        if student is None:

            flash(
                "Student not found.",
                "error"
            )

            return redirect(
                url_for("faculty_dashboard")
            )


        # -------------------------------------------------
        # Get latest academic record + ML input
        # -------------------------------------------------

        record, student_data = (
            get_latest_academic_record(
                cursor,
                student_id
            )
        )


        if record is None:

            flash(
                "Academic record not found for this student.",
                "error"
            )

            return redirect(
                url_for("faculty_dashboard")
            )


        # -------------------------------------------------
        # Generate prediction + SHAP + interventions
        # -------------------------------------------------

        analysis = generate_interventions(
            student_data
        )


        risk_level = analysis[
            "risk_level"
        ]


        probabilities = analysis[
            "probabilities"
        ]


        # -------------------------------------------------
        # Save prediction
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO predictions (
                student_id,
                record_id,
                risk_level,
                high_probability,
                medium_probability,
                low_probability
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            );
            """,
            (
                student_id,
                record["record_id"],
                risk_level,
                probabilities.get(
                    "High",
                    0
                ),
                probabilities.get(
                    "Medium",
                    0
                ),
                probabilities.get(
                    "Low",
                    0
                )
            )
        )


        prediction_id = cursor.lastrowid


        # -------------------------------------------------
        # Save SHAP risk factors
        # -------------------------------------------------

        for rank, factor in enumerate(
            analysis["interventions"],
            start=1
        ):

            cursor.execute(
                """
                INSERT INTO risk_factors (
                    prediction_id,
                    feature_name,
                    feature_value,
                    shap_impact,
                    factor_rank
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                );
                """,
                (
                    prediction_id,
                    factor["feature"],
                    factor["value"],
                    factor["shap_impact"],
                    rank
                )
            )


        # -------------------------------------------------
        # Save interventions
        # -------------------------------------------------

        for intervention in analysis[
            "interventions"
        ]:

            cursor.execute(
                """
                INSERT INTO interventions (
                    prediction_id,
                    feature_name,
                    intervention_title,
                    recommendation,
                    priority
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                );
                """,
                (
                    prediction_id,
                    intervention[
                        "feature"
                    ],
                    intervention[
                        "title"
                    ],
                    intervention[
                        "recommendation"
                    ],
                    analysis[
                        "priority"
                    ]
                )
            )


        # -------------------------------------------------
        # Commit everything
        # -------------------------------------------------

        connection.commit()


        flash(
            f"{student['student_name']} analyzed successfully. "
            f"Predicted risk level: {risk_level}.",
            "success"
        )


        # -------------------------------------------------
        # Go directly to analysis page
        # -------------------------------------------------

        return redirect(
            url_for(
                "student_analysis",
                student_id=student_id
            )
        )


    # -----------------------------------------------------
    # Error handling
    # -----------------------------------------------------

    except Exception as error:

        if connection is not None:

            try:
                connection.rollback()
            except Exception:
                pass


        print(
            "Analyze student error:",
            error
        )


        flash(
            "Unable to analyze the student. "
            "Please try again.",
            "error"
        )


        return redirect(
            url_for("faculty_dashboard")
        )


    # -----------------------------------------------------
    # Close database connection
    # -----------------------------------------------------

    finally:

        if cursor is not None:
            cursor.close()


        if (
            connection is not None
            and connection.is_connected()
        ):
            connection.close()

# =========================================================
# STUDENT PREDICTION HISTORY
# =========================================================

@app.route(
    "/api/students/<int:student_id>/prediction-history",
    methods=["GET"]
)
def get_prediction_history(student_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # Check student exists
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                student_id,
                register_number,
                student_name
            FROM students
            WHERE student_id = %s;
            """,
            (student_id,)
        )

        student = cursor.fetchone()

        if student is None:

            return jsonify({
                "status":
                    "error",

                "message":
                    "Student not found."
            }), 404


        # -------------------------------------------------
        # Get prediction history
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                p.prediction_id,
                p.record_id,
                a.semester,
                p.risk_level,
                p.high_probability,
                p.medium_probability,
                p.low_probability,
                p.predicted_at
            FROM predictions p
            JOIN academic_records a
                ON p.record_id = a.record_id
            WHERE p.student_id = %s
            ORDER BY p.predicted_at ASC;
            """,
            (student_id,)
        )

        predictions = cursor.fetchall()

        history = []


        # -------------------------------------------------
        # JSON-friendly result
        # -------------------------------------------------

        for prediction in predictions:

            history.append({

                "prediction_id":
                    prediction[
                        "prediction_id"
                    ],

                "record_id":
                    prediction[
                        "record_id"
                    ],

                "semester":
                    prediction[
                        "semester"
                    ],

                "risk_level":
                    prediction[
                        "risk_level"
                    ],

                "probabilities": {

                    "High":
                        float(
                            prediction[
                                "high_probability"
                            ]
                        ),

                    "Medium":
                        float(
                            prediction[
                                "medium_probability"
                            ]
                        ),

                    "Low":
                        float(
                            prediction[
                                "low_probability"
                            ]
                        )
                },

                "predicted_at":
                    prediction[
                        "predicted_at"
                    ].isoformat()
            })


        return jsonify({

            "status":
                "success",

            "student": {

                "student_id":
                    student[
                        "student_id"
                    ],

                "register_number":
                    student[
                        "register_number"
                    ],

                "student_name":
                    student[
                        "student_name"
                    ]
            },

            "prediction_count":
                len(history),

            "history":
                history
        })

    except Exception as error:

        return jsonify({
            "status":
                "error",

            "message":
                str(error)
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if (
            connection is not None
            and connection.is_connected()
        ):
            connection.close()


# =========================================================
# UPDATE INTERVENTION PROGRESS
# =========================================================

@app.route(
    "/api/interventions/<int:intervention_id>/progress",
    methods=["POST"]
)
def update_intervention_progress(
    intervention_id
):

    connection = None
    cursor = None

    try:

        # -------------------------------------------------
        # Read JSON
        # -------------------------------------------------

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "status":
                    "error",

                "message":
                    "Request body is required."
            }), 400


        new_status = data.get(
            "status"
        )

        progress_note = data.get(
            "progress_note",
            ""
        ).strip()


        # -------------------------------------------------
        # Validate status
        # -------------------------------------------------

        allowed_statuses = [
            "Pending",
            "In Progress",
            "Completed"
        ]

        if new_status not in allowed_statuses:

            return jsonify({
                "status":
                    "error",

                "message":
                    "Status must be Pending, "
                    "In Progress or Completed."
            }), 400


        # -------------------------------------------------
        # Database
        # -------------------------------------------------

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # Find intervention
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                i.intervention_id,
                i.prediction_id,
                i.intervention_title,
                i.status AS current_status,
                p.student_id
            FROM interventions i
            JOIN predictions p
                ON i.prediction_id =
                   p.prediction_id
            WHERE i.intervention_id = %s;
            """,
            (intervention_id,)
        )

        intervention = (
            cursor.fetchone()
        )

        if intervention is None:

            return jsonify({
                "status":
                    "error",

                "message":
                    "Intervention not found."
            }), 404


        student_id = intervention[
            "student_id"
        ]


        # -------------------------------------------------
        # Update current status
        # -------------------------------------------------

        cursor.execute(
            """
            UPDATE interventions
            SET status = %s
            WHERE intervention_id = %s;
            """,
            (
                new_status,
                intervention_id
            )
        )


        # -------------------------------------------------
        # Add progress history
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO progress_tracking (
                student_id,
                intervention_id,
                progress_note,
                status
            )
            VALUES (
                %s,
                %s,
                %s,
                %s
            );
            """,
            (
                student_id,
                intervention_id,
                progress_note,
                new_status
            )
        )

        progress_id = (
            cursor.lastrowid
        )

        connection.commit()


        return jsonify({

            "status":
                "success",

            "message":
                "Intervention progress updated successfully.",

            "progress_id":
                progress_id,

            "student_id":
                student_id,

            "intervention_id":
                intervention_id,

            "intervention_title":
                intervention[
                    "intervention_title"
                ],

            "previous_status":
                intervention[
                    "current_status"
                ],

            "current_status":
                new_status,

            "progress_note":
                progress_note
        })

    except Exception as error:

        if connection is not None:
            connection.rollback()

        return jsonify({
            "status":
                "error",

            "message":
                str(error)
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if (
            connection is not None
            and connection.is_connected()
        ):
            connection.close()


# =========================================================
# GET STUDENT INTERVENTION PROGRESS
# =========================================================

@app.route(
    "/api/students/<int:student_id>/progress",
    methods=["GET"]
)
def get_student_progress(student_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # Check student exists
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                student_id,
                register_number,
                student_name
            FROM students
            WHERE student_id = %s;
            """,
            (student_id,)
        )

        student = cursor.fetchone()

        if student is None:

            return jsonify({
                "status":
                    "error",

                "message":
                    "Student not found."
            }), 404


        # -------------------------------------------------
        # Get interventions
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                i.intervention_id,
                i.prediction_id,
                i.feature_name,
                i.intervention_title,
                i.recommendation,
                i.priority,
                i.status
            FROM interventions i
            JOIN predictions p
                ON i.prediction_id =
                   p.prediction_id
            WHERE p.student_id = %s
            ORDER BY i.intervention_id;
            """,
            (student_id,)
        )

        intervention_rows = (
            cursor.fetchall()
        )

        interventions = []


        # -------------------------------------------------
        # Progress history
        # -------------------------------------------------

        for intervention in intervention_rows:

            cursor.execute(
                """
                SELECT
                    progress_id,
                    progress_note,
                    status,
                    updated_at
                FROM progress_tracking
                WHERE intervention_id = %s
                ORDER BY updated_at ASC;
                """,
                (
                    intervention[
                        "intervention_id"
                    ],
                )
            )

            progress_rows = (
                cursor.fetchall()
            )

            progress_history = []

            for progress in progress_rows:

                progress_history.append({

                    "progress_id":
                        progress[
                            "progress_id"
                        ],

                    "progress_note":
                        progress[
                            "progress_note"
                        ],

                    "status":
                        progress[
                            "status"
                        ],

                    "updated_at":
                        progress[
                            "updated_at"
                        ].isoformat()
                })


            interventions.append({

                "intervention_id":
                    intervention[
                        "intervention_id"
                    ],

                "prediction_id":
                    intervention[
                        "prediction_id"
                    ],

                "feature":
                    intervention[
                        "feature_name"
                    ],

                "title":
                    intervention[
                        "intervention_title"
                    ],

                "recommendation":
                    intervention[
                        "recommendation"
                    ],

                "priority":
                    intervention[
                        "priority"
                    ],

                "current_status":
                    intervention[
                        "status"
                    ],

                "progress_history":
                    progress_history
            })


        return jsonify({

            "status":
                "success",

            "student": {

                "student_id":
                    student[
                        "student_id"
                    ],

                "register_number":
                    student[
                        "register_number"
                    ],

                "student_name":
                    student[
                        "student_name"
                    ]
            },

            "intervention_count":
                len(interventions),

            "interventions":
                interventions
        })

    except Exception as error:

        return jsonify({
            "status":
                "error",

            "message":
                str(error)
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if (
            connection is not None
            and connection.is_connected()
        ):
            connection.close()


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
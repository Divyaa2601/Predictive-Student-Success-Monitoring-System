import os
import sys

from flask import Flask, jsonify, request
import mysql.connector
from dotenv import load_dotenv


# =========================================================
# PROJECT PATH CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Allows Flask to import modules from project root later
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.predictor import predict_student_risk
from ml.intervention_engine import generate_interventions

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    """
    Create and return a MySQL database connection.
    """

    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

    return connection


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
            "status": "success",
            "message": "Database connected successfully",
            "database": result["database_name"]
        })

    except mysql.connector.Error as error:

        return jsonify({
            "status": "error",
            "message": str(error)
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

        query = """
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

        cursor.execute(query)

        students = cursor.fetchall()

        return jsonify({
            "status": "success",
            "count": len(students),
            "students": students
        })

    except mysql.connector.Error as error:

        return jsonify({
            "status": "error",
            "message": str(error)
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

@app.route("/api/predict/<int:student_id>")
def predict_student(student_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # -------------------------------------------------
        # Get latest academic record
        # -------------------------------------------------

        query = """
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
        """

        cursor.execute(
            query,
            (student_id,)
        )

        record = cursor.fetchone()

        if record is None:

            return jsonify({
                "status": "error",
                "message":
                    "Academic record not found for this student."
            }), 404


        # -------------------------------------------------
        # Convert MySQL Decimal values to float
        # -------------------------------------------------

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
                    record["study_hours_weekly"]
                ),

            "class_participation":
                float(
                    record["class_participation"]
                ),

            "late_submissions":
                int(record["late_submissions"])
        }


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
        # Get student information
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


        # -------------------------------------------------
        # API Response
        # -------------------------------------------------

        return jsonify({

            "status":
                "success",

            "student": {
                "student_id":
                    student_id,

                "register_number":
                    student["register_number"],

                "student_name":
                    student["student_name"]
            },

            "prediction":
                prediction,

            "priority":
                intervention_result["priority"],

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
            "status": "error",
            "message": str(error)
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
        # 1. Get latest academic record
        # -------------------------------------------------

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

            return jsonify({
                "status": "error",
                "message":
                    "Academic record not found for this student."
            }), 404


        # -------------------------------------------------
        # 2. Prepare ML input
        # -------------------------------------------------

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
                    record["assignment_completion_pct"]
                ),

            "quiz_avg":
                float(record["quiz_avg"]),

            "study_hours_weekly":
                float(record["study_hours_weekly"]),

            "class_participation":
                float(record["class_participation"]),

            "late_submissions":
                int(record["late_submissions"])
        }


        # -------------------------------------------------
        # 3. Generate prediction + interventions
        # -------------------------------------------------

        analysis = generate_interventions(
            student_data
        )

        risk_level = analysis["risk_level"]

        probabilities = analysis["probabilities"]


        # -------------------------------------------------
        # 4. Insert prediction
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
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (
                student_id,
                record["record_id"],
                risk_level,
                probabilities.get("High", 0),
                probabilities.get("Medium", 0),
                probabilities.get("Low", 0)
            )
        )

        prediction_id = cursor.lastrowid


        # -------------------------------------------------
        # 5. Insert SHAP risk factors
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
                VALUES (%s, %s, %s, %s, %s);
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
        # 6. Insert interventions
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
                VALUES (%s, %s, %s, %s, %s);
                """,
                (
                    prediction_id,
                    intervention["feature"],
                    intervention["title"],
                    intervention["recommendation"],
                    analysis["priority"]
                )
            )


        # -------------------------------------------------
        # 7. Commit transaction
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
                analysis["priority"],

            "factors_saved":
                len(analysis["interventions"]),

            "interventions_saved":
                len(analysis["interventions"])
        })


    except Exception as error:

        if connection is not None:
            connection.rollback()

        return jsonify({
            "status": "error",
            "message": str(error)
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
        # 1. Check whether student exists
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
                "status": "error",
                "message": "Student not found."
            }), 404


        # -------------------------------------------------
        # 2. Get prediction history
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


        # -------------------------------------------------
        # 3. Make values JSON-friendly
        # -------------------------------------------------

        history = []

        for prediction in predictions:

            history.append({

                "prediction_id":
                    prediction["prediction_id"],

                "record_id":
                    prediction["record_id"],

                "semester":
                    prediction["semester"],

                "risk_level":
                    prediction["risk_level"],

                "probabilities": {

                    "High": float(
                        prediction["high_probability"]
                    ),

                    "Medium": float(
                        prediction["medium_probability"]
                    ),

                    "Low": float(
                        prediction["low_probability"]
                    )
                },

                "predicted_at":
                    prediction[
                        "predicted_at"
                    ].isoformat()
            })


        # -------------------------------------------------
        # 4. Return response
        # -------------------------------------------------

        return jsonify({

            "status": "success",

            "student": {
                "student_id":
                    student["student_id"],

                "register_number":
                    student["register_number"],

                "student_name":
                    student["student_name"]
            },

            "prediction_count":
                len(history),

            "history":
                history
        })


    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
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
def update_intervention_progress(intervention_id):

    connection = None
    cursor = None

    try:

        # -------------------------------------------------
        # 1. Read JSON request
        # -------------------------------------------------

        data = request.get_json(silent=True)

        if not data:

            return jsonify({
                "status": "error",
                "message": "Request body is required."
            }), 400


        new_status = data.get("status")

        progress_note = data.get(
            "progress_note",
            ""
        ).strip()


        # -------------------------------------------------
        # 2. Validate status
        # -------------------------------------------------

        allowed_statuses = [
            "Pending",
            "In Progress",
            "Completed"
        ]

        if new_status not in allowed_statuses:

            return jsonify({
                "status": "error",
                "message":
                    "Status must be Pending, "
                    "In Progress or Completed."
            }), 400


        # -------------------------------------------------
        # 3. Connect to database
        # -------------------------------------------------

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # 4. Find intervention + student
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
                ON i.prediction_id = p.prediction_id
            WHERE i.intervention_id = %s;
            """,
            (intervention_id,)
        )

        intervention = cursor.fetchone()


        if intervention is None:

            return jsonify({
                "status": "error",
                "message": "Intervention not found."
            }), 404


        student_id = intervention["student_id"]


        # -------------------------------------------------
        # 5. Update intervention status
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
        # 6. Create progress history record
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO progress_tracking (
                student_id,
                intervention_id,
                progress_note,
                status
            )
            VALUES (%s, %s, %s, %s);
            """,
            (
                student_id,
                intervention_id,
                progress_note,
                new_status
            )
        )

        progress_id = cursor.lastrowid


        # -------------------------------------------------
        # 7. Save transaction
        # -------------------------------------------------

        connection.commit()


        return jsonify({

            "status": "success",

            "message":
                "Intervention progress updated successfully.",

            "progress_id":
                progress_id,

            "student_id":
                student_id,

            "intervention_id":
                intervention_id,

            "intervention_title":
                intervention["intervention_title"],

            "previous_status":
                intervention["current_status"],

            "current_status":
                new_status,

            "progress_note":
                progress_note
        })


    except Exception as error:

        if connection is not None:
            connection.rollback()

        return jsonify({
            "status": "error",
            "message": str(error)
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
        # 1. Check student exists
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
                "status": "error",
                "message": "Student not found."
            }), 404


        # -------------------------------------------------
        # 2. Get interventions
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
                ON i.prediction_id = p.prediction_id
            WHERE p.student_id = %s
            ORDER BY i.intervention_id;
            """,
            (student_id,)
        )

        intervention_rows = cursor.fetchall()

        interventions = []


        # -------------------------------------------------
        # 3. Get progress history for each intervention
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
                    intervention["intervention_id"],
                )
            )

            progress_rows = cursor.fetchall()

            progress_history = []

            for progress in progress_rows:

                progress_history.append({
                    "progress_id":
                        progress["progress_id"],

                    "progress_note":
                        progress["progress_note"],

                    "status":
                        progress["status"],

                    "updated_at":
                        progress["updated_at"].isoformat()
                })


            interventions.append({

                "intervention_id":
                    intervention["intervention_id"],

                "prediction_id":
                    intervention["prediction_id"],

                "feature":
                    intervention["feature_name"],

                "title":
                    intervention["intervention_title"],

                "recommendation":
                    intervention["recommendation"],

                "priority":
                    intervention["priority"],

                "current_status":
                    intervention["status"],

                "progress_history":
                    progress_history
            })


        # -------------------------------------------------
        # 4. Return result
        # -------------------------------------------------

        return jsonify({

            "status": "success",

            "student": {
                "student_id":
                    student["student_id"],

                "register_number":
                    student["register_number"],

                "student_name":
                    student["student_name"]
            },

            "intervention_count":
                len(interventions),

            "interventions":
                interventions
        })


    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
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
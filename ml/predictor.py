import os
import joblib
import pandas as pd


# =========================================================
# PATH CONFIGURATION
# =========================================================

# Project root directory
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODEL_DIR = os.path.join(BASE_DIR, "models")

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "student_risk_model.pkl"
)

IMPUTER_PATH = os.path.join(
    MODEL_DIR,
    "imputer.pkl"
)

SCALER_PATH = os.path.join(
    MODEL_DIR,
    "scaler.pkl"
)

FEATURES_PATH = os.path.join(
    MODEL_DIR,
    "feature_names.pkl"
)


# =========================================================
# LOAD MODEL ARTIFACTS
# =========================================================

model = joblib.load(MODEL_PATH)

imputer = joblib.load(IMPUTER_PATH)

scaler = joblib.load(SCALER_PATH)

features = joblib.load(FEATURES_PATH)


# =========================================================
# INPUT FEATURES
# =========================================================

# internal_change is calculated automatically,
# so the user does not need to provide it.

required_input_features = [
    feature
    for feature in features
    if feature != "internal_change"
]


# =========================================================
# STUDENT RISK PREDICTION FUNCTION
# =========================================================

def predict_student_risk(student_data):
    """
    Predict the academic risk level of a student.

    The function performs:
    1. Input validation
    2. Feature engineering
    3. Missing-value imputation
    4. Feature scaling
    5. Risk prediction
    6. Probability calculation

    Parameters
    ----------
    student_data : dict
        Dictionary containing student academic
        and engagement information.

    Returns
    -------
    dict
        Predicted risk level and probabilities
        for High, Medium and Low risk classes.
    """

    # -----------------------------------------------------
    # Validate input type
    # -----------------------------------------------------

    if not isinstance(student_data, dict):
        raise TypeError(
            "student_data must be provided as a dictionary."
        )


    # -----------------------------------------------------
    # Check required features
    # -----------------------------------------------------

    missing_features = [
        feature
        for feature in required_input_features
        if feature not in student_data
    ]

    if missing_features:
        raise ValueError(
            "Missing required features: "
            + ", ".join(missing_features)
        )


    # -----------------------------------------------------
    # Copy input
    # -----------------------------------------------------

    student_data = student_data.copy()


    # -----------------------------------------------------
    # Feature Engineering
    # -----------------------------------------------------

    student_data["internal_change"] = (
        student_data["internal_2"]
        - student_data["internal_1"]
    )


    # -----------------------------------------------------
    # Convert input into DataFrame
    # -----------------------------------------------------

    student_df = pd.DataFrame(
        [student_data]
    )


    # -----------------------------------------------------
    # Maintain training feature order
    # -----------------------------------------------------

    student_df = student_df[features]


    # -----------------------------------------------------
    # Missing Value Imputation
    # -----------------------------------------------------

    student_imputed = imputer.transform(
        student_df
    )

    student_imputed = pd.DataFrame(
        student_imputed,
        columns=features
    )


    # -----------------------------------------------------
    # Feature Scaling
    # -----------------------------------------------------

    student_scaled = scaler.transform(
        student_imputed
    )

    student_scaled = pd.DataFrame(
        student_scaled,
        columns=features
    )


    # -----------------------------------------------------
    # Risk Prediction
    # -----------------------------------------------------

    prediction = model.predict(
        student_scaled
    )[0]


    # -----------------------------------------------------
    # Prediction Probabilities
    # -----------------------------------------------------

    probabilities = model.predict_proba(
        student_scaled
    )[0]

    probability_dict = {
        str(class_name): round(
            float(probability) * 100,
            2
        )
        for class_name, probability
        in zip(
            model.classes_,
            probabilities
        )
    }


    # -----------------------------------------------------
    # Return Prediction Result
    # -----------------------------------------------------

    return {
        "risk_level": str(prediction),
        "probabilities": probability_dict
    }


# =========================================================
# TEST PREDICTOR
# =========================================================

if __name__ == "__main__":

    print("=" * 50)
    print("PREDICTIVE STUDENT SUCCESS MONITORING SYSTEM")
    print("=" * 50)

    print("\nTesting student risk predictor...")


    # -----------------------------------------------------
    # Sample Student
    # -----------------------------------------------------

    sample_student = {

        "semester": 5,

        "previous_gpa": 5.2,

        "attendance_pct": 65,

        "internal_1": 36,

        "internal_2": 37,

        "assignment_avg": 55,

        "assignment_completion_pct": 60,

        "quiz_avg": 28,

        "study_hours_weekly": 7,

        "class_participation": 3,

        "late_submissions": 5
    }


    # -----------------------------------------------------
    # Generate Prediction
    # -----------------------------------------------------

    result = predict_student_risk(
        sample_student
    )


    # -----------------------------------------------------
    # Display Result
    # -----------------------------------------------------

    print("\nSTUDENT RISK PREDICTION")
    print("-" * 50)

    print(
        "Predicted Risk Level:",
        result["risk_level"]
    )

    print("\nRisk Probabilities:")

    for risk, probability in result[
        "probabilities"
    ].items():

        print(
            f"{risk}: {probability}%"
        )


    print("\nPrediction completed successfully.")
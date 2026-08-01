import os
import joblib
import shap
import pandas as pd
import numpy as np


# =========================================================
# PATH CONFIGURATION
# =========================================================

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
# READABLE FEATURE NAMES
# =========================================================

FEATURE_DISPLAY_NAMES = {
    "semester": "Semester",
    "previous_gpa": "Previous GPA",
    "attendance_pct": "Attendance",
    "internal_1": "Internal Assessment 1",
    "internal_2": "Internal Assessment 2",
    "assignment_avg": "Assignment Average",
    "assignment_completion_pct": "Assignment Completion",
    "quiz_avg": "Quiz Average",
    "study_hours_weekly": "Weekly Study Hours",
    "class_participation": "Class Participation",
    "late_submissions": "Late Submissions",
    "internal_change": "Internal Performance Change"
}


# =========================================================
# CREATE SHAP EXPLAINER
# =========================================================

# For a linear model, SHAP can use the model's learned
# coefficients directly. A zero vector in scaled feature
# space represents approximately the training mean because
# StandardScaler was used during preprocessing.

background = np.zeros(
    (1, len(features))
)

background_df = pd.DataFrame(
    background,
    columns=features
)

explainer = shap.LinearExplainer(
    model,
    background_df
)


# =========================================================
# PREPARE STUDENT DATA
# =========================================================

def prepare_student_data(student_data):

    student_data = student_data.copy()

    required_features = [
        feature
        for feature in features
        if feature != "internal_change"
    ]

    missing_features = [
        feature
        for feature in required_features
        if feature not in student_data
    ]

    if missing_features:
        raise ValueError(
            "Missing required features: "
            + ", ".join(missing_features)
        )

    # Feature engineering
    student_data["internal_change"] = (
        student_data["internal_2"]
        - student_data["internal_1"]
    )

    # Convert to DataFrame
    student_df = pd.DataFrame(
        [student_data]
    )

    student_df = student_df[features]

    # Imputation
    student_imputed = imputer.transform(
        student_df
    )

    student_imputed = pd.DataFrame(
        student_imputed,
        columns=features
    )

    # Scaling
    student_scaled = scaler.transform(
        student_imputed
    )

    student_scaled = pd.DataFrame(
        student_scaled,
        columns=features
    )

    return (
        student_df,
        student_scaled
    )


# =========================================================
# EXPLAIN STUDENT PREDICTION
# =========================================================

def explain_student_prediction(
    student_data,
    top_n=5
):

    student_original, student_scaled = (
        prepare_student_data(student_data)
    )

    # ---------------------------------------------
    # Predict risk level
    # ---------------------------------------------

    predicted_risk = model.predict(
        student_scaled
    )[0]

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


    # ---------------------------------------------
    # Generate SHAP values
    # ---------------------------------------------

    shap_values = explainer(
        student_scaled
    )


    # ---------------------------------------------
    # Find predicted class index
    # ---------------------------------------------

    class_index = list(
        model.classes_
    ).index(predicted_risk)


    # ---------------------------------------------
    # Extract SHAP values for predicted class
    # ---------------------------------------------

    student_shap_values = (
        shap_values.values[
            0,
            :,
            class_index
        ]
    )


    # ---------------------------------------------
    # Build explanation table
    # ---------------------------------------------

    explanation = pd.DataFrame({
        "feature": features,
        "value": student_original.iloc[0].values,
        "shap_value": student_shap_values
    })

    explanation["absolute_impact"] = (
        explanation["shap_value"].abs()
    )

    explanation["display_name"] = (
        explanation["feature"].map(
            FEATURE_DISPLAY_NAMES
        )
    )


    # ---------------------------------------------
    # Factors pushing toward predicted risk
    # ---------------------------------------------

    contributing_factors = explanation[
        explanation["shap_value"] > 0
    ].copy()

    contributing_factors = (
        contributing_factors
        .sort_values(
            "shap_value",
            ascending=False
        )
        .head(top_n)
    )


    # ---------------------------------------------
    # Convert results into JSON-friendly format
    # ---------------------------------------------

    factors = []

    for _, row in contributing_factors.iterrows():

        factors.append({
            "feature": row["feature"],
            "display_name": row["display_name"],
            "value": round(
                float(row["value"]),
                2
            ),
            "impact": round(
                float(row["shap_value"]),
                4
            )
        })


    # ---------------------------------------------
    # Return explanation
    # ---------------------------------------------

    return {
        "risk_level": str(predicted_risk),
        "probabilities": probability_dict,
        "top_factors": factors
    }


# =========================================================
# TEST EXPLAINABILITY MODULE
# =========================================================

if __name__ == "__main__":

    print("=" * 55)
    print("STUDENT RISK EXPLAINABILITY TEST")
    print("=" * 55)

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

    result = explain_student_prediction(
        sample_student
    )

    print(
        "\nPredicted Risk:",
        result["risk_level"]
    )

    print("\nProbabilities:")

    for risk, probability in result[
        "probabilities"
    ].items():

        print(
            f"{risk}: {probability}%"
        )

    print("\nTop Contributing Factors:")

    for index, factor in enumerate(
        result["top_factors"],
        start=1
    ):

        print(
            f"{index}. "
            f"{factor['display_name']} "
            f"(Value: {factor['value']}, "
            f"SHAP Impact: {factor['impact']})"
        )

    print(
        "\nExplanation generated successfully."
    )
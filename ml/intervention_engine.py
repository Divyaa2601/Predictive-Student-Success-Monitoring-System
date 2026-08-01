from explainability import explain_student_prediction


# =========================================================
# INTERVENTION RULES
# =========================================================

INTERVENTION_RULES = {

    "attendance_pct": {
        "title": "Improve Attendance",
        "recommendation":
            "Attend classes regularly and maintain at least 75% attendance. "
            "Prioritize classes in subjects where academic performance is weak."
    },

    "internal_1": {
        "title": "Improve Internal Assessment Performance",
        "recommendation":
            "Review weak topics from Internal Assessment 1 and practice "
            "important questions before the next internal examination."
    },

    "internal_2": {
        "title": "Focus on Recent Internal Performance",
        "recommendation":
            "Focus on topics where performance was weak in Internal Assessment 2. "
            "Seek faculty guidance and revise difficult concepts."
    },

    "internal_change": {
        "title": "Address Performance Decline",
        "recommendation":
            "Review the topics responsible for the decline between internal "
            "assessments and create a focused recovery plan."
    },

    "quiz_avg": {
        "title": "Improve Quiz Performance",
        "recommendation":
            "Practice topic-wise quizzes regularly and review incorrect answers "
            "to strengthen conceptual understanding."
    },

    "assignment_avg": {
        "title": "Improve Assignment Performance",
        "recommendation":
            "Review assignment feedback, correct previous mistakes and complete "
            "future assignments with greater focus on weak concepts."
    },

    "assignment_completion_pct": {
        "title": "Complete Pending Assignments",
        "recommendation":
            "Complete pending assignments on priority and maintain a regular "
            "assignment submission schedule."
    },

    "previous_gpa": {
        "title": "Strengthen Academic Foundation",
        "recommendation":
            "Identify subjects contributing to the lower GPA and allocate "
            "additional weekly study time to foundational concepts."
    },

    "study_hours_weekly": {
        "title": "Increase Study Time",
        "recommendation":
            "Follow a structured weekly study schedule with dedicated revision "
            "and practice sessions."
    },

    "class_participation": {
        "title": "Increase Classroom Participation",
        "recommendation":
            "Participate more actively in classroom discussions, ask questions "
            "and clarify difficult concepts with faculty."
    },

    "late_submissions": {
        "title": "Reduce Late Submissions",
        "recommendation":
            "Use a weekly deadline tracker and complete academic tasks before "
            "their submission dates."
    }
}


# =========================================================
# RISK-LEVEL GUIDANCE
# =========================================================

RISK_GUIDANCE = {

    "High": {
        "priority": "Immediate",
        "message":
            "The student requires immediate academic attention. "
            "The identified risk factors should be addressed through a "
            "structured improvement plan and regular faculty monitoring."
    },

    "Medium": {
        "priority": "Moderate",
        "message":
            "The student shows signs of academic vulnerability. "
            "Early corrective actions are recommended to prevent further decline."
    },

    "Low": {
        "priority": "Routine",
        "message":
            "The student is currently performing satisfactorily. "
            "The focus should be on maintaining consistent academic performance."
    }
}


# =========================================================
# GENERATE PERSONALIZED INTERVENTIONS
# =========================================================

def generate_interventions(student_data, top_n=5):

    """
    Generate personalized academic interventions based on
    the student's predicted risk and SHAP explanation.
    """

    explanation = explain_student_prediction(
        student_data,
        top_n=top_n
    )

    risk_level = explanation["risk_level"]

    top_factors = explanation["top_factors"]

    interventions = []


    # -----------------------------------------------------
    # Map SHAP factors to intervention rules
    # -----------------------------------------------------

    for factor in top_factors:

        feature = factor["feature"]

        if feature in INTERVENTION_RULES:

            rule = INTERVENTION_RULES[feature]

            interventions.append({

                "feature": feature,

                "factor":
                    factor["display_name"],

                "value":
                    factor["value"],

                "shap_impact":
                    factor["impact"],

                "title":
                    rule["title"],

                "recommendation":
                    rule["recommendation"]
            })


    # -----------------------------------------------------
    # Risk-level guidance
    # -----------------------------------------------------

    guidance = RISK_GUIDANCE.get(
        risk_level,
        {
            "priority": "Unknown",
            "message":
                "Risk guidance is currently unavailable."
        }
    )


    # -----------------------------------------------------
    # Return intervention result
    # -----------------------------------------------------

    return {

        "risk_level":
            risk_level,

        "probabilities":
            explanation["probabilities"],

        "priority":
            guidance["priority"],

        "risk_message":
            guidance["message"],

        "interventions":
            interventions
    }


# =========================================================
# TEST INTERVENTION ENGINE
# =========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("AI INTERVENTION ENGINE TEST")
    print("=" * 60)


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


    result = generate_interventions(
        sample_student
    )


    # -----------------------------------------------------
    # Display Risk Information
    # -----------------------------------------------------

    print(
        "\nPredicted Risk Level:",
        result["risk_level"]
    )

    print(
        "Intervention Priority:",
        result["priority"]
    )


    print("\nRisk Probabilities:")

    for risk, probability in result[
        "probabilities"
    ].items():

        print(
            f"{risk}: {probability}%"
        )


    # -----------------------------------------------------
    # Display Guidance
    # -----------------------------------------------------

    print("\nAcademic Guidance:")

    print(
        result["risk_message"]
    )


    # -----------------------------------------------------
    # Display Personalized Interventions
    # -----------------------------------------------------

    print(
        "\nPersonalized Recommendations"
    )

    print("-" * 60)


    if not result["interventions"]:

        print(
            "No specific intervention is currently required."
        )


    for index, intervention in enumerate(
        result["interventions"],
        start=1
    ):

        print(
            f"\n{index}. "
            f"{intervention['title']}"
        )

        print(
            f"   Contributing Factor: "
            f"{intervention['factor']}"
        )

        print(
            f"   Student Value: "
            f"{intervention['value']}"
        )

        print(
            f"   SHAP Impact: "
            f"{intervention['shap_impact']}"
        )

        print(
            f"   Recommendation: "
            f"{intervention['recommendation']}"
        )


    print(
        "\nIntervention analysis completed successfully."
    )
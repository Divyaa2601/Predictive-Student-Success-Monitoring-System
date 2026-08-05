from ml.explainability import explain_student_prediction


# =========================================================
# CORRECTIVE / PREVENTIVE INTERVENTIONS
# Used mainly for Medium and High risk students
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
            "Review assignment feedback, correct previous mistakes and focus "
            "on improving performance in future assignments."
    },

    "assignment_completion_pct": {
        "title": "Complete Assignments Consistently",
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
        "title": "Improve Study Routine",
        "recommendation":
            "Follow a structured weekly study schedule with dedicated revision "
            "and practice sessions."
    },

    "class_participation": {
        "title": "Increase Classroom Participation",
        "recommendation":
            "Participate actively in classroom discussions, ask questions and "
            "clarify difficult concepts with faculty."
    },

    "late_submissions": {
        "title": "Reduce Late Submissions",
        "recommendation":
            "Use a weekly deadline tracker and complete academic tasks before "
            "their submission dates."
    }
}


# =========================================================
# MAINTENANCE RECOMMENDATIONS
# Used for Low risk students
# =========================================================

MAINTENANCE_RULES = {

    "attendance_pct": {
        "title": "Maintain Good Attendance",
        "recommendation":
            "Continue maintaining regular attendance and consistent classroom "
            "engagement."
    },

    "internal_1": {
        "title": "Maintain Internal Assessment Performance",
        "recommendation":
            "Continue the current preparation strategy and maintain consistent "
            "performance in future internal assessments."
    },

    "internal_2": {
        "title": "Maintain Recent Academic Performance",
        "recommendation":
            "Continue the effective preparation approach demonstrated in the "
            "recent internal assessment."
    },

    "internal_change": {
        "title": "Maintain Performance Progress",
        "recommendation":
            "Continue monitoring internal assessment performance and maintain "
            "consistent academic progress."
    },

    "quiz_avg": {
        "title": "Maintain Strong Quiz Performance",
        "recommendation":
            "Continue regular topic-wise practice and revision to maintain "
            "strong quiz performance."
    },

    "assignment_avg": {
        "title": "Maintain Assignment Quality",
        "recommendation":
            "Continue completing assignments carefully and applying faculty "
            "feedback to maintain strong performance."
    },

    "assignment_completion_pct": {
        "title": "Maintain Assignment Completion",
        "recommendation":
            "Continue completing and submitting assignments consistently "
            "within the given deadlines."
    },

    "previous_gpa": {
        "title": "Maintain Academic Consistency",
        "recommendation":
            "Continue the study habits that have supported good academic "
            "performance and maintain consistency across subjects."
    },

    "study_hours_weekly": {
        "title": "Maintain Effective Study Routine",
        "recommendation":
            "Continue following a balanced and consistent weekly study schedule."
    },

    "class_participation": {
        "title": "Maintain Classroom Engagement",
        "recommendation":
            "Continue participating actively in classroom activities and "
            "academic discussions."
    },

    "late_submissions": {
        "title": "Maintain Timely Submissions",
        "recommendation":
            "Continue managing deadlines effectively and submitting academic "
            "work on time."
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

    explanation = explain_student_prediction(
        student_data,
        top_n=top_n
    )

    risk_level = explanation["risk_level"]
    top_factors = explanation["top_factors"]

    interventions = []


    # -----------------------------------------------------
    # Select recommendation type based on risk
    # -----------------------------------------------------

    if risk_level == "Low":
        selected_rules = MAINTENANCE_RULES
        intervention_type = "Maintenance"
    else:
        selected_rules = INTERVENTION_RULES
        intervention_type = "Corrective"


    # -----------------------------------------------------
    # Generate recommendations from SHAP factors
    # -----------------------------------------------------

    for factor in top_factors:

        feature = factor["feature"]

        if feature in selected_rules:

            rule = selected_rules[feature]

            interventions.append({
                "feature": feature,
                "factor": factor["display_name"],
                "value": factor["value"],
                "shap_impact": factor["impact"],
                "type": intervention_type,
                "title": rule["title"],
                "recommendation": rule["recommendation"]
            })


    # -----------------------------------------------------
    # Risk guidance
    # -----------------------------------------------------

    guidance = RISK_GUIDANCE.get(
        risk_level,
        {
            "priority": "Unknown",
            "message": "Risk guidance is currently unavailable."
        }
    )


    return {
        "risk_level": risk_level,
        "probabilities": explanation["probabilities"],
        "priority": guidance["priority"],
        "risk_message": guidance["message"],
        "interventions": interventions
    }


# =========================================================
# TEST
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

    result = generate_interventions(sample_student)

    print("\nPredicted Risk Level:", result["risk_level"])
    print("Intervention Priority:", result["priority"])

    print("\nRisk Probabilities:")

    for risk, probability in result["probabilities"].items():
        print(f"{risk}: {probability}%")

    print("\nAcademic Guidance:")
    print(result["risk_message"])

    print("\nPersonalized Recommendations")
    print("-" * 60)

    for index, intervention in enumerate(
        result["interventions"],
        start=1
    ):

        print(f"\n{index}. {intervention['title']}")
        print(f"   Type: {intervention['type']}")
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
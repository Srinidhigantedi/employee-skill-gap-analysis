
"""Recommend courses using skill gaps and learning eligibility rules."""

from pathlib import Path
import pandas as pd
import argparse

DATA_DIR = Path("data") / "starter"
OUTPUT_DIR = Path("outputs")
REFERENCE_DATE = pd.Timestamp("2026-10-28")


def recommend_courses(data_dir=DATA_DIR, output_dir=OUTPUT_DIR):
    gaps = pd.read_csv(output_dir / "skill_gap_analysis.csv")
    courses = pd.read_csv(data_dir / "course.csv")
    course_skills = pd.read_csv(data_dir / "course_skill.csv")
    prerequisites = pd.read_csv(data_dir / "prerequisite.csv")
    enrollments = pd.read_csv(data_dir / "enrollment.csv")
    completions = pd.read_csv(data_dir / "completion.csv")

    # Only recommend courses for assessed skill gaps.
    required_gaps = gaps.loc[
        gaps["gap_status"] == "gap_identified"
    ].copy()

    if required_gaps.empty:
        print("No assessed skill gaps found.")
        return pd.DataFrame()

    # Identify courses each employee has passed.
    completion_details = completions.merge(
        enrollments[["enrollment_id", "employee_id", "course_id"]],
        on="enrollment_id",
        how="inner",
        validate="many_to_one",
    )

    passed = completion_details.loc[
        completion_details["result"].astype(str).str.lower() == "passed"
    ]

    passed_pairs = set(
        zip(passed["employee_id"], passed["course_id"])
    )

    # Identify courses employees are currently taking.
    active_statuses = {"enrolled", "in_progress"}

    active_enrollments = enrollments.loc[
        enrollments["status"].astype(str).str.lower().isin(active_statuses)
    ]

    active_pairs = set(
        zip(active_enrollments["employee_id"],
            active_enrollments["course_id"])
    )

    # Connect skill gaps to courses teaching those skills.
    recommendations = required_gaps.merge(
        course_skills,
        on="skill_id",
        how="inner",
    ).merge(
        courses,
        on="course_id",
        how="inner",
        validate="many_to_one",
    )

    # Keep active courses available on the fixed reference date.
    recommendations["available_from"] = pd.to_datetime(
        recommendations["available_from"], errors="coerce"
    )
    recommendations["available_to"] = pd.to_datetime(
        recommendations["available_to"], errors="coerce"
    )

    valid_status = recommendations["status"].astype(str).str.lower().isin(
        {"active", "available"}
    )
    valid_dates = (
        recommendations["available_from"].le(REFERENCE_DATE)
        & recommendations["available_to"].ge(REFERENCE_DATE)
    )

    recommendations = recommendations.loc[
        valid_status & valid_dates
    ].copy()

    # Remove courses already passed or currently being taken.
    recommendations = recommendations.loc[
        ~recommendations.apply(
            lambda row: (
                (row["employee_id"], row["course_id"]) in passed_pairs
                or (row["employee_id"], row["course_id"]) in active_pairs
            ),
            axis=1,
        )
    ].copy()

    # Check that every required prerequisite has been passed.
    required_prerequisites = prerequisites.loc[
        prerequisites["required"].astype(str).str.lower().isin(
            {"true", "1", "yes"}
        )
    ]

    prerequisite_map = (
        required_prerequisites.groupby("course_id")[
            "prerequisite_course_id"
        ]
        .apply(list)
        .to_dict()
    )

    def prerequisites_satisfied(row):
        needed = prerequisite_map.get(row["course_id"], [])
        passed_courses = {
            course_id
            for employee_id, course_id in passed_pairs
            if employee_id == row["employee_id"]
        }
        return all(course_id in passed_courses for course_id in needed)

    recommendations = recommendations.loc[
        recommendations.apply(prerequisites_satisfied, axis=1)
    ].copy()

    # Rank courses by largest gap, learning gain, then lower cost.
    recommendations = recommendations.sort_values(
        by=[
            "employee_id",
            "gap",
            "expected_proficiency_gain",
            "cost",
        ],
        ascending=[True, False, False, True],
    )

    # If one course addresses multiple gaps, keep its best-ranked match.
    recommendations = recommendations.drop_duplicates(
        subset=["employee_id", "course_id"],
        keep="first",
    ).copy()

    recommendations["recommendation_rank"] = (
        recommendations.groupby("employee_id").cumcount() + 1
    )

    recommendations["recommendation_reason"] = (
        "Addresses "
        + recommendations["skill_name"].astype(str)
        + " gap of "
        + recommendations["gap"].astype(str)
        + " proficiency level(s)"
    )

    columns = [
        "employee_id",
        "department",
        "role_name",
        "skill_id",
        "skill_name",
        "proficiency",
        "target_proficiency",
        "gap",
        "course_id",
        "course_name",
        "expected_proficiency_gain",
        "duration_hours",
        "cost",
        "recommendation_rank",
        "recommendation_reason",
    ]

    recommendations = recommendations[columns]

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "course_recommendations.csv"
    recommendations.to_csv(output_file, index=False)

    print("\nELIGIBLE COURSE RECOMMENDATIONS")
    print("=" * 50)
    print(f"Employees with assessed skill gaps: "
          f"{required_gaps['employee_id'].nunique()}")
    print(f"Eligible recommendations: {len(recommendations)}")
    print(f"Employees receiving recommendations: "
          f"{recommendations['employee_id'].nunique()}")
    print(f"Unique employee-course pairs: "
          f"{recommendations[['employee_id', 'course_id']].drop_duplicates().shape[0]}")
    print(f"Results saved to: {output_file}")

    if not recommendations.empty:
        print("\nTop recommendations:")
        print(recommendations.head(10).to_string(index=False))
    else:
        print("No eligible courses found after applying the rules.")

    return recommendations


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scale", choices=["starter", "full"], default="starter"
    )
    args = parser.parse_args()

    data_dir = Path("data") / args.scale
    output_dir = Path("outputs") / args.scale

    recommend_courses(data_dir=data_dir, output_dir=output_dir)


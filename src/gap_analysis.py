

"""Analyze employee skill gaps against role requirements."""

from pathlib import Path
import argparse

import pandas as pd


DATA_DIR = Path("data") / "starter"
OUTPUT_DIR = Path("outputs")

# Project rule: reassessment is required after 180 days.
REFERENCE_DATE = pd.Timestamp("2026-10-28")
REASSESSMENT_DAYS = 180


def calculate_skill_gaps(data_dir=DATA_DIR, output_dir=OUTPUT_DIR):
    employees = pd.read_csv(data_dir / "employee.csv")
    roles = pd.read_csv(data_dir / "role.csv")
    skills = pd.read_csv(data_dir / "skill.csv")
    targets = pd.read_csv(data_dir / "role_skill_target.csv")
    assessments = pd.read_csv(data_dir / "employee_skill.csv")

    # Connect employees to their role requirements.
    employee_targets = employees[
        ["employee_id", "role_id", "department"]
    ].merge(
        roles[["role_id", "role_name"]],
        on="role_id",
        validate="many_to_one",
    ).merge(
        targets,
        on="role_id",
        validate="many_to_many",
    )

    # Attach assessments where available.
    results = employee_targets.merge(
        assessments[
            ["employee_id", "skill_id", "proficiency", "assessed_on"]
        ],
        on=["employee_id", "skill_id"],
        how="left",
        validate="one_to_one",
    )

    results["assessed_on"] = pd.to_datetime(
        results["assessed_on"], errors="coerce"
    )

    # Classify assessment freshness.
    results["assessment_status"] = "assessed"

    results.loc[
        results["proficiency"].isna(),
        "assessment_status",
    ] = "not_assessed"

    assessment_age = (
        REFERENCE_DATE - results["assessed_on"]
    ).dt.days

    stale_assessment = (
        results["proficiency"].notna()
        & (
            results["assessed_on"].isna()
            | (assessment_age > REASSESSMENT_DAYS)
        )
    )

    results.loc[
        stale_assessment,
        "assessment_status",
    ] = "reassessment_required"

    # Calculate confirmed gaps only from current assessments.
    results["gap"] = (
        results["target_proficiency"] - results["proficiency"]
    ).clip(lower=0)

    results.loc[
        results["assessment_status"] != "assessed",
        "gap",
    ] = pd.NA

    # Add readable skill names.
    results = results.merge(
        skills[["skill_id", "skill_name"]],
        on="skill_id",
        validate="many_to_one",
    )

    results["gap_status"] = "not_assessed"

    results.loc[
        results["assessment_status"] == "reassessment_required",
        "gap_status",
    ] = "reassessment_required"

    results.loc[
        results["gap"].eq(0),
        "gap_status",
    ] = "no_gap"

    results.loc[
        results["gap"].gt(0),
        "gap_status",
    ] = "gap_identified"

    results["gap"] = results["gap"].astype("Int64")

    # Save detailed results.
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "skill_gap_analysis.csv"
    results.to_csv(output_file, index=False)

    # Print a summary.
    print("\nSKILL GAP ANALYSIS")
    print("=" * 50)
    print(f"Employees analyzed: {employees['employee_id'].nunique()}")
    print(f"Employee requirement rows: {len(results)}")
    print(
        f"Current assessments: "
        f"{results['assessment_status'].eq('assessed').sum()}"
    )
    print(
        f"Not assessed: "
        f"{results['assessment_status'].eq('not_assessed').sum()}"
    )
    print(
        f"Reassessment required: "
        f"{results['assessment_status'].eq('reassessment_required').sum()}"
    )
    print(f"Identified skill gaps: {results['gap_status'].eq('gap_identified').sum()}")
    print(f"No-gap rows: {results['gap_status'].eq('no_gap').sum()}")
    print(f"Results saved to: {output_file}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scale", choices=["starter", "full"], default="starter"
    )
    args = parser.parse_args()

    data_dir = Path("data") / args.scale
    output_dir = Path("outputs") / args.scale

    calculate_skill_gaps(data_dir=data_dir, output_dir=output_dir)

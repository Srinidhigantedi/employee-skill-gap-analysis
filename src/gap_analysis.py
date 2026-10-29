
"""Analyze employee skill gaps against role requirements."""

from pathlib import Path
import argparse

import pandas as pd


DATA_DIR = Path("data") / "starter"
OUTPUT_DIR = Path("outputs")


def calculate_skill_gaps(data_dir=DATA_DIR, output_dir=OUTPUT_DIR):
    employees = pd.read_csv(data_dir / "employee.csv")
    roles = pd.read_csv(data_dir / "role.csv")
    skills = pd.read_csv(data_dir / "skill.csv")
    targets = pd.read_csv(data_dir / "role_skill_target.csv")
    assessments = pd.read_csv(data_dir / "employee_skill.csv")

    # Connect each employee to their role's required skills.
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

    # Attach the current assessment, if one exists.
    results = employee_targets.merge(
        assessments[
            ["employee_id", "skill_id", "proficiency", "assessed_on"]
        ],
        on=["employee_id", "skill_id"],
        how="left",
        validate="one_to_one",
    )

    # Missing assessments are unknown, not proof of zero proficiency.
    results["assessment_status"] = results["proficiency"].apply(
        lambda value: "assessed" if pd.notna(value) else "not_assessed"
    )

    # Calculate gaps only where a valid assessment exists.
    results["gap"] = (
        results["target_proficiency"] - results["proficiency"]
    ).clip(lower=0)

    results.loc[
        results["proficiency"].isna(), "gap"
    ] = pd.NA

    # Add readable skill names.
    results = results.merge(
        skills[["skill_id", "skill_name"]],
        on="skill_id",
        validate="many_to_one",
    )

    results["gap_status"] = "not_assessed"
    results.loc[
        results["gap"].eq(0), "gap_status"
    ] = "no_gap"
    results.loc[
        results["gap"].gt(0), "gap_status"
    ] = "gap_identified"

    results["gap"] = results["gap"].astype("Int64")

    # Save detailed results.
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "skill_gap_analysis.csv"
    results.to_csv(output_file, index=False)

    print("\nSKILL GAP ANALYSIS")
    print("=" * 50)
    print(f"Employees analyzed: {employees['employee_id'].nunique()}")
    print(f"Role-skill requirements: {len(targets)}")
    print(f"Employee requirement rows: {len(results)}")
    print(f"Rows with assessments: {results['proficiency'].notna().sum()}")
    print(f"Rows not assessed: {results['proficiency'].isna().sum()}")
    print(f"Identified gaps: {results['gap_status'].eq('gap_identified').sum()}")
    print(f"No-gap rows: {results['gap_status'].eq('no_gap').sum()}")
    print(f"Results saved to: {output_file}")

    print("\nExample results:")
    columns = [
        "employee_id", "role_name", "skill_name",
        "proficiency", "target_proficiency", "gap_status", "gap",
    ]
    print(
        results.loc[
            results["assessment_status"] == "assessed", columns
        ].head(10).to_string(index=False)
    )

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

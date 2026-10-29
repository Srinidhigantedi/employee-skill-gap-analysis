
"""Validate the starter or full synthetic dataset."""

import argparse
from pathlib import Path

import pandas as pd


def validate_data(scale="starter"):
    folder = Path("data") / scale

    required_files = [
        "employee", "role", "skill", "role_skill_target",
        "employee_skill", "course", "course_skill",
        "prerequisite", "enrollment", "completion", "budget",
    ]

    tables = {
        name: pd.read_csv(folder / f"{name}.csv")
        for name in required_files
    }

    errors = []
    checks = 0

    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(message)

    # 1. Primary-key uniqueness
    primary_keys = {
        "employee": "employee_id",
        "role": "role_id",
        "skill": "skill_id",
        "course": "course_id",
        "enrollment": "enrollment_id",
        "completion": "completion_id",
        "budget": "budget_id",
    }

    for table_name, column in primary_keys.items():
        df = tables[table_name]
        check(
            df[column].notna().all()
            and df[column].is_unique,
            f"{table_name}: missing or duplicate {column}",
        )

    # 2. Foreign-key integrity
    foreign_keys = [
        ("employee", "role_id", "role", "role_id"),
        ("role_skill_target", "role_id", "role", "role_id"),
        ("role_skill_target", "skill_id", "skill", "skill_id"),
        ("employee_skill", "employee_id", "employee", "employee_id"),
        ("employee_skill", "skill_id", "skill", "skill_id"),
        ("course_skill", "course_id", "course", "course_id"),
        ("course_skill", "skill_id", "skill", "skill_id"),
        ("prerequisite", "course_id", "course", "course_id"),
        (
            "prerequisite", "prerequisite_course_id",
            "course", "course_id",
        ),
        ("enrollment", "employee_id", "employee", "employee_id"),
        ("enrollment", "course_id", "course", "course_id"),
        (
            "completion", "enrollment_id",
            "enrollment", "enrollment_id",
        ),
    ]

    for child, column, parent, parent_column in foreign_keys:
        actual = set(tables[child][column].dropna())
        valid = set(tables[parent][parent_column].dropna())
        check(
            actual.issubset(valid),
            f"{child}.{column}: invalid foreign-key references",
        )

    # 3. Employee department must match the referenced role
    employee_roles = tables["employee"].merge(
        tables["role"][["role_id", "department"]],
        on="role_id",
        how="left",
        suffixes=("_employee", "_role"),
        validate="many_to_one",
    )

    check(
        (
            employee_roles["department_employee"]
            == employee_roles["department_role"]
        ).all(),
        "Employee department differs from role department",
    )

    # 4. Bridge-table uniqueness
    for table_name, columns in [
        ("role_skill_target", ["role_id", "skill_id"]),
        ("employee_skill", ["employee_id", "skill_id"]),
        ("course_skill", ["course_id", "skill_id"]),
        (
            "prerequisite",
            ["course_id", "prerequisite_course_id"],
        ),
    ]:
        check(
            not tables[table_name].duplicated(columns).any(),
            f"{table_name}: duplicate relationship",
        )

    # 5. Proficiency and gap validation
    employee_skills = tables["employee_skill"]
    targets = tables["role_skill_target"]
    employees = tables["employee"][["employee_id", "role_id"]]

    assessed = employee_skills.merge(
        employees, on="employee_id", validate="many_to_one"
    ).merge(
        targets,
        on=["role_id", "skill_id"],
        how="left",
        validate="many_to_one",
    )

    check(
        employee_skills["proficiency"].between(0, 5).all(),
        "Employee proficiency must be between 0 and 5",
    )

    check(
        assessed["target_proficiency"].notna().all(),
        "An employee assessment has no matching role skill target",
    )

    expected_gap = (
        assessed["target_proficiency"] - assessed["proficiency"]
    ).clip(lower=0)

    check(
        assessed["gap"].eq(expected_gap).all(),
        "Derived skill gaps do not match the proficiency rules",
    )

    check(
        targets["target_proficiency"].between(0, 5).all(),
        "Role target proficiency must be between 0 and 5",
    )

    # 6. Course values
    courses = tables["course"]

    check(
        (courses["duration_hours"] > 0).all(),
        "Course duration must be positive",
    )
    check(
        (courses["cost"] >= 0).all(),
        "Course cost cannot be negative",
    )
    check(
        (courses["capacity"] > 0).all(),
        "Course capacity must be positive",
    )

    # 7. Prerequisite and completion consistency
    prerequisites = tables["prerequisite"]

    check(
        (
            prerequisites["course_id"]
            != prerequisites["prerequisite_course_id"]
        ).all(),
        "A course cannot be its own prerequisite",
    )

    completions = tables["completion"]
    enrollments = tables["enrollment"]

    completed_ids = set(
        enrollments.loc[
            enrollments["status"] == "completed", "enrollment_id"
        ]
    )

    check(
        set(completions["enrollment_id"]).issubset(completed_ids),
        "Completion references an enrollment not marked completed",
    )

    check(
        not completions["enrollment_id"].duplicated().any(),
        "Duplicate completion event detected",
    )

    # 8. Enrollment IDs must follow the naming convention
    expected_ids = (
        "ENR-" + enrollments["employee_id"]
        + "-" + enrollments["course_id"]
    )

    check(
        enrollments["enrollment_id"].eq(expected_ids).all(),
        "Enrollment IDs do not follow the required convention",
    )

    # 9. Report
    print(f"\nDataset: {scale}")
    print(f"Checks executed: {checks}")
    print(f"Errors found: {len(errors)}")

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        raise SystemExit(1)

    print("All current validation checks passed!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scale", choices=["starter", "full"], default="starter"
    )
    args = parser.parse_args()

    validate_data(args.scale)

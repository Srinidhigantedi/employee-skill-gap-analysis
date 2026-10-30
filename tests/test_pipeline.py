
"""Automated tests for the learning recommendation pipeline."""

from pathlib import Path
import pandas as pd

DATA = Path("data/starter")
OUTPUT = Path("outputs")


def load_csv(folder, filename):
    return pd.read_csv(folder / filename)


def test_generated_data_has_unique_primary_keys():
    primary_keys = {
        "employee.csv": "employee_id",
        "role.csv": "role_id",
        "skill.csv": "skill_id",
        "course.csv": "course_id",
        "enrollment.csv": "enrollment_id",
        "completion.csv": "completion_id",
    }

    for filename, key in primary_keys.items():
        frame = load_csv(DATA, filename)
        assert frame[key].notna().all(), f"Missing {key} in {filename}"
        assert frame[key].is_unique, f"Duplicate {key} in {filename}"


def test_recommendations_have_no_duplicate_employee_course_pairs():
    recommendations = load_csv(OUTPUT, "course_recommendations.csv")

    assert not recommendations.duplicated(
        ["employee_id", "course_id"]
    ).any()


def test_allocations_do_not_exceed_course_capacity():
    allocations = load_csv(OUTPUT, "learning_plan_allocations.csv")
    courses = load_csv(DATA, "course.csv")
    enrollments = load_csv(DATA, "enrollment.csv")

    active = enrollments[
        enrollments["status"].str.lower().isin(
            ["enrolled", "in_progress"]
        )
    ]

    existing_counts = active.groupby("course_id").size()
    new_counts = allocations.groupby("course_id").size()

    total_counts = existing_counts.add(new_counts, fill_value=0)

    capacity = courses.set_index("course_id")["capacity"]
    total_counts = total_counts.reindex(capacity.index, fill_value=0)

    assert (total_counts <= capacity).all()


def test_allocations_respect_department_budgets():
    allocations = load_csv(OUTPUT, "learning_plan_allocations.csv")
    budgets = load_csv(DATA, "budget.csv")
    enrollments = load_csv(DATA, "enrollment.csv")
    employees = load_csv(DATA, "employee.csv")
    courses = load_csv(DATA, "course.csv")

    active = enrollments[
        enrollments["status"].str.lower().isin(
            ["enrolled", "in_progress"]
        )
    ]

    active_spend = active.merge(
        employees[["employee_id", "department"]],
        on="employee_id",
        validate="many_to_one",
    ).merge(
        courses[["course_id", "cost"]],
        on="course_id",
        validate="many_to_one",
    )

    existing_spend = active_spend.groupby("department")["cost"].sum()
    new_spend = allocations.groupby("department")["cost"].sum()

    budget = (
        budgets[budgets["fiscal_year"] == 2026]
        .set_index("department")["allocated_amount"]
    )

    total_spend = (
        existing_spend.add(new_spend, fill_value=0)
        .reindex(budget.index, fill_value=0)
    )

    assert (total_spend <= budget + 0.01).all()


def test_allocations_exclude_passed_and_active_courses():
    allocations = load_csv(OUTPUT, "learning_plan_allocations.csv")
    enrollments = load_csv(DATA, "enrollment.csv")
    completions = load_csv(DATA, "completion.csv")

    completion_details = completions.merge(
        enrollments[["enrollment_id", "employee_id", "course_id"]],
        on="enrollment_id",
        validate="many_to_one",
    )

    passed = completion_details[
        completion_details["result"].str.lower() == "passed"
    ]

    passed_pairs = set(zip(passed["employee_id"], passed["course_id"]))

    active = enrollments[
        enrollments["status"].str.lower().isin(
            ["enrolled", "in_progress"]
        )
    ]
    active_pairs = set(zip(active["employee_id"], active["course_id"]))

    allocated_pairs = set(
        zip(allocations["employee_id"], allocations["course_id"])
    )

    assert allocated_pairs.isdisjoint(passed_pairs)
    assert allocated_pairs.isdisjoint(active_pairs)


def test_allocations_satisfy_required_prerequisites():
    allocations = load_csv(OUTPUT, "learning_plan_allocations.csv")
    prerequisites = load_csv(DATA, "prerequisite.csv")
    enrollments = load_csv(DATA, "enrollment.csv")
    completions = load_csv(DATA, "completion.csv")

    required = prerequisites[
        prerequisites["required"].astype(str).str.lower().isin(
            ["true", "1", "yes"]
        )
    ]

    completion_details = completions.merge(
        enrollments[["enrollment_id", "employee_id", "course_id"]],
        on="enrollment_id",
        validate="many_to_one",
    )

    passed = completion_details[
        completion_details["result"].str.lower() == "passed"
    ]

    passed_by_employee = {}
    for employee_id, course_id in zip(
        passed["employee_id"], passed["course_id"]
    ):
        passed_by_employee.setdefault(employee_id, set()).add(course_id)

    required_by_course = (
        required.groupby("course_id")["prerequisite_course_id"]
        .apply(set)
        .to_dict()
    )

    for row in allocations.itertuples(index=False):
        needed = required_by_course.get(row.course_id, set())
        already_passed = passed_by_employee.get(row.employee_id, set())
        assert needed.issubset(already_passed), (
            f"{row.employee_id} lacks a prerequisite for {row.course_id}"
        )

def test_stale_assessment_requires_reassessment(tmp_path):
    import pandas as pd
    from src.gap_analysis import calculate_skill_gaps

    data_dir = tmp_path / "data"
    output_dir = tmp_path / "outputs"
    data_dir.mkdir()

    # One employee has three required skills.
    pd.DataFrame([
        {
            "employee_id": "EMP-000001",
            "role_id": "ROLE-001",
            "department": "Engineering",
        }
    ]).to_csv(data_dir / "employee.csv", index=False)

    pd.DataFrame([
        {"role_id": "ROLE-001", "role_name": "Test Engineer"}
    ]).to_csv(data_dir / "role.csv", index=False)

    pd.DataFrame([
        {"skill_id": "SKL-001", "skill_name": "Python"},
        {"skill_id": "SKL-002", "skill_name": "SQL"},
        {"skill_id": "SKL-003", "skill_name": "Git"},
    ]).to_csv(data_dir / "skill.csv", index=False)

    pd.DataFrame([
        {
            "role_id": "ROLE-001",
            "skill_id": skill_id,
            "target_proficiency": 4,
        }
        for skill_id in ["SKL-001", "SKL-002", "SKL-003"]
    ]).to_csv(data_dir / "role_skill_target.csv", index=False)

    pd.DataFrame([
        {
            "employee_id": "EMP-000001",
            "skill_id": "SKL-001",
            "proficiency": 2,
            "assessed_on": "2025-01-01",
        },
        {
            "employee_id": "EMP-000001",
            "skill_id": "SKL-002",
            "proficiency": 2,
            "assessed_on": "2026-10-01",
        },
    ]).to_csv(data_dir / "employee_skill.csv", index=False)

    results = calculate_skill_gaps(
        data_dir=data_dir,
        output_dir=output_dir,
    )

    statuses = results.set_index("skill_id")["assessment_status"]
    gaps = results.set_index("skill_id")["gap"]
    gap_statuses = results.set_index("skill_id")["gap_status"]

    assert statuses["SKL-001"] == "reassessment_required"
    assert pd.isna(gaps["SKL-001"])
    assert gap_statuses["SKL-001"] == "reassessment_required"

    assert statuses["SKL-002"] == "assessed"
    assert gaps["SKL-002"] == 2
    assert gap_statuses["SKL-002"] == "gap_identified"

    assert statuses["SKL-003"] == "not_assessed"
    assert pd.isna(gaps["SKL-003"])
    assert gap_statuses["SKL-003"] == "not_assessed"

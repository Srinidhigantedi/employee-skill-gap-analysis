
"""Validate learning allocations against budget and course capacity."""

from pathlib import Path
import pandas as pd

DATA_DIR = Path("data") / "starter"
OUTPUT_DIR = Path("outputs")


def validate_allocation():
    allocations = pd.read_csv(
        OUTPUT_DIR / "learning_plan_allocations.csv"
    )
    decisions = pd.read_csv(
        OUTPUT_DIR / "learning_allocation_decisions.csv"
    )
    courses = pd.read_csv(DATA_DIR / "course.csv")
    employees = pd.read_csv(DATA_DIR / "employee.csv")
    enrollments = pd.read_csv(DATA_DIR / "enrollment.csv")
    budgets = pd.read_csv(DATA_DIR / "budget.csv")

    errors = []

    # 1. Every allocated employee-course pair must be unique.
    if allocations.duplicated(["employee_id", "course_id"]).any():
        errors.append("Duplicate employee-course allocations found.")

    # 2. Allocated courses must exist and costs must be positive.
    checked = allocations.merge(
        courses[["course_id", "capacity"]],
        on="course_id",
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    if not checked["_merge"].eq("both").all():
        errors.append("Allocation references an unknown course.")

    if (allocations["cost"] <= 0).any():
        errors.append("Non-positive course cost found.")

    # 3. Every allocated decision must match the allocation output.
    allocated_decisions = decisions.loc[
        decisions["allocation_status"] == "allocated",
        ["employee_id", "course_id"],
    ].drop_duplicates()

    allocation_pairs = allocations[
        ["employee_id", "course_id"]
    ].drop_duplicates()

    comparison = allocated_decisions.merge(
        allocation_pairs,
        on=["employee_id", "course_id"],
        how="outer",
        indicator=True,
    )

    if not comparison["_merge"].eq("both").all():
        errors.append("Allocation output and decision report disagree.")

    # 4. Existing active enrollments plus new allocations
    # must not exceed any course's capacity.
    active_statuses = {"enrolled", "in_progress"}
    active = enrollments.loc[
        enrollments["status"].astype(str).str.lower().isin(active_statuses)
    ]

    existing_seats = active.groupby("course_id").size()
    new_seats = allocations.groupby("course_id").size()

    seat_usage = (
        existing_seats.add(new_seats, fill_value=0)
        .rename("seats_used")
        .reset_index()
        .merge(
            courses[["course_id", "capacity"]],
            on="course_id",
            how="left",
            validate="one_to_one",
        )
    )

    over_capacity = seat_usage[
        seat_usage["seats_used"] > seat_usage["capacity"]
    ]

    if not over_capacity.empty:
        errors.append(
            f"{len(over_capacity)} courses exceed their capacity."
        )

    # 5. Existing active commitments plus new allocations
    # must stay within each department's 2026 budget.
    active_costs = active.merge(
        employees[["employee_id", "department"]],
        on="employee_id",
        how="left",
        validate="many_to_one",
    ).merge(
        courses[["course_id", "cost"]],
        on="course_id",
        how="left",
        validate="many_to_one",
        suffixes=("_enrollment", "_course"),
    )

    existing_spend = active_costs.groupby("department")[
        "cost"
    ].sum()

    new_spend = allocations.groupby("department")["cost"].sum()

    budget_usage = (
        budgets.loc[budgets["fiscal_year"] == 2026]
        .set_index("department")["allocated_amount"]
        .to_frame("budget")
    )

    budget_usage["existing_spend"] = existing_spend
    budget_usage["new_allocation_spend"] = new_spend
    budget_usage = budget_usage.fillna(0)
    budget_usage["total_spend"] = (
        budget_usage["existing_spend"]
        + budget_usage["new_allocation_spend"]
    )

    over_budget = budget_usage[
        budget_usage["total_spend"] > budget_usage["budget"] + 0.01
    ]

    if not over_budget.empty:
        errors.append(
            f"{len(over_budget)} departments exceed their budget."
        )

    # 6. Every allocated recommendation must have allocated status.
    if not decisions["allocation_status"].isin(
        ["allocated", "not_allocated"]
    ).all():
        errors.append("Unknown allocation status found.")

    print("\nALLOCATION VALIDATION")
    print("=" * 45)
    print(f"Allocated rows checked: {len(allocations)}")
    print(f"Courses checked for capacity: {len(seat_usage)}")
    print(f"Departments checked for budget: {len(budget_usage)}")

    if errors:
        print("\nVALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("\nAll allocation validation checks passed!")

    print("\nBudget usage:")
    print(
        budget_usage[
            ["budget", "total_spend"]
        ].to_string()
    )


if __name__ == "__main__":
    validate_allocation()

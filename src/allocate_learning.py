
"""Allocate recommended courses within capacity and department budgets."""

from pathlib import Path
import pandas as pd
import argparse

DATA_DIR = Path("data") / "starter"
OUTPUT_DIR = Path("outputs")
ACTIVE_STATUSES = {"enrolled", "in_progress"}


def allocate_learning(data_dir=DATA_DIR, output_dir=OUTPUT_DIR):
    candidates = pd.read_csv(output_dir / "course_recommendations.csv")
    courses = pd.read_csv(data_dir / "course.csv")
    employees = pd.read_csv(data_dir / "employee.csv")
    enrollments = pd.read_csv(data_dir / "enrollment.csv")
    budgets = pd.read_csv(data_dir / "budget.csv")

    # Use only the 2026 budget records.
    budgets = budgets.loc[budgets["fiscal_year"] == 2026].copy()

    if budgets["department"].duplicated().any():
        raise ValueError("Multiple 2026 budget records found for a department.")

    budget_remaining = budgets.set_index("department")[
        "allocated_amount"
    ].to_dict()

    # Existing active enrollments consume seats and budget.
    active = enrollments.loc[
        enrollments["status"].astype(str).str.lower().isin(ACTIVE_STATUSES)
    ].merge(
        employees[["employee_id", "department"]],
        on="employee_id",
        how="left",
        validate="many_to_one",
    ).merge(
        courses[["course_id", "cost", "capacity"]],
        on="course_id",
        how="left",
        validate="many_to_one",
    )

    seats_used = active.groupby("course_id").size().to_dict()

    committed = active.groupby("department")["cost"].sum().to_dict()

    for department, amount in committed.items():
        if department in budget_remaining:
            budget_remaining[department] -= amount

    # Report budgets after existing active enrollment commitments.
    budget_start = budgets.set_index("department")[
        "allocated_amount"
    ].to_dict()

    # Sort deterministically: largest gap, best learning gain, lower cost.
    candidates = candidates.merge(
        courses[["course_id", "capacity"]],
        on="course_id",
        how="left",
        validate="many_to_one",
    )

    candidates = candidates.sort_values(
        by=[
            "gap",
            "expected_proficiency_gain",
            "cost",
            "employee_id",
            "course_id",
        ],
        ascending=[False, False, True, True, True],
    ).reset_index(drop=True)

    allocated_rows = []
    decision_rows = []

    for _, row in candidates.iterrows():
        employee_id = row["employee_id"]
        department = row["department"]
        course_id = row["course_id"]
        cost = float(row["cost"])
        capacity = int(row["capacity"])
        used = int(seats_used.get(course_id, 0))

        reason = None

        if department not in budget_remaining:
            reason = "no_2026_department_budget"
        elif used >= capacity:
            reason = "course_capacity_reached"
        elif budget_remaining[department] < cost:
            reason = "department_budget_insufficient"

        record = row.drop(labels=["capacity"]).to_dict()

        if reason is None:
            # Allocate one seat and reserve the course cost.
            seats_used[course_id] = used + 1
            budget_remaining[department] -= cost

            record["allocation_status"] = "allocated"
            record["allocation_reason"] = (
                "Capacity available and department budget sufficient"
            )
            allocated_rows.append(record)
        else:
            record["allocation_status"] = "not_allocated"
            record["allocation_reason"] = reason

        decision_rows.append(record)

    decisions = pd.DataFrame(decision_rows)
    allocated = pd.DataFrame(allocated_rows)

    output_dir.mkdir(parents=True, exist_ok=True)

    decisions.to_csv(
        output_dir / "learning_allocation_decisions.csv",
        index=False,
    )
    allocated.to_csv(
        output_dir / "learning_plan_allocations.csv",
        index=False,
    )

    # Summarize allocated costs by department.
    allocation_spend = (
        allocated.groupby("department")["cost"].sum().to_dict()
        if not allocated.empty
        else {}
    )

    summary_rows = []
    for department, original_budget in budget_start.items():
        existing_commitment = float(committed.get(department, 0))
        newly_allocated = float(allocation_spend.get(department, 0))

        summary_rows.append({
            "department": department,
            "fiscal_year": 2026,
            "currency": budgets.loc[
                budgets["department"] == department, "currency"
            ].iloc[0],
            "allocated_budget": float(original_budget),
            "existing_active_enrollment_cost": existing_commitment,
            "new_recommendation_allocation": newly_allocated,
            "remaining_budget": float(
                budget_remaining.get(department, original_budget)
            ),
        })

    budget_summary = pd.DataFrame(summary_rows)
    budget_summary.to_csv(
        output_dir / "budget_summary.csv",
        index=False,
    )

    print("\nLEARNING ALLOCATION SUMMARY")
    print("=" * 50)
    print(f"Candidate recommendations: {len(candidates)}")
    print(f"Allocated recommendations: {len(allocated)}")
    print(f"Not allocated: {len(decisions) - len(allocated)}")
    print("Allocation decisions: outputs/learning_allocation_decisions.csv")
    print("Learning plan: outputs/learning_plan_allocations.csv")
    print("Budget summary: outputs/budget_summary.csv")

    print("\nBudget summary:")
    print(budget_summary.to_string(index=False))

    print("\nAllocation reasons:")
    if not decisions.empty:
        print(
            decisions["allocation_reason"]
            .value_counts()
            .to_string()
        )

    return allocated, decisions, budget_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scale", choices=["starter", "full"], default="starter"
    )
    args = parser.parse_args()

    data_dir = Path("data") / args.scale
    output_dir = Path("outputs") / args.scale

    allocate_learning(data_dir=data_dir, output_dir=output_dir)

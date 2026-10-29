
"""Generate reproducible synthetic data for the YottaFlex project."""

import argparse
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_SEED = 20261022
OUTPUT_DIR = Path("data")


def make_id(prefix, number, width=6):
    return f"{prefix}-{number:0{width}d}"


def generate_data(scale="starter", seed=DEFAULT_SEED):
    # Small dataset for development; full dataset matches the assessment.
    sizes = {
        "starter": {
            "employees": 100,
            "skills": 50,
            "courses": 100,
            "enrollments": 200,
        },
        "full": {
            "employees": 5000,
            "skills": 500,
            "courses": 1000,
            "enrollments": 10000,
        },
    }

    if scale not in sizes:
        raise ValueError("Scale must be 'starter' or 'full'.")

    n = sizes[scale]
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    departments = ["Engineering", "Data", "IT", "HR", "Operations"]
    today = pd.Timestamp("2026-10-28")

    # 1. MASTER DATA: Roles
    role_names = [
        "Python Developer",
        "Data Analyst",
        "Software Engineer",
        "IT Support Engineer",
        "HR Analyst",
        "Business Analyst",
        "Cloud Engineer",
        "QA Engineer",
        "Database Administrator",
        "Project Coordinator",
    ]

    roles = pd.DataFrame([
        {
            "role_id": make_id("ROL", i),
            "role_name": name,
            "department": departments[(i - 1) % len(departments)],
            "status": "active",
        }
        for i, name in enumerate(role_names, start=1)
    ])

    # 2. MASTER DATA: Skills
    skill_names = [
        "Python", "SQL", "Java", "JavaScript", "HTML",
        "CSS", "React", "Flask", "Django", "Git",
        "Problem Solving", "Communication", "Excel",
        "Data Analysis", "Machine Learning", "Statistics",
        "Cloud Computing", "AWS", "Azure", "Linux",
        "Docker", "Kubernetes", "REST APIs", "Testing",
        "OOP", "Data Structures", "Cybersecurity",
        "Networking", "Project Management", "Leadership",
    ]

    skill_rows = []
    for i in range(1, n["skills"] + 1):
        name = (
            skill_names[i - 1]
            if i <= len(skill_names)
            else f"Specialized Skill {i:04d}"
        )
        skill_rows.append({
            "skill_id": make_id("SKL", i),
            "skill_name": name,
            "category": (
                "Technical" if i % 4 != 0 else "Professional"
            ),
            "status": "active",
        })

    skills = pd.DataFrame(skill_rows)
    skill_ids = skills["skill_id"].tolist()

    # 3. MASTER DATA: Employees
    employee_rows = []
    for i in range(1, n["employees"] + 1):
        role_index = rng.randrange(len(roles))
        employee_rows.append({
            "employee_id": make_id("EMP", i),
            "role_id": roles.iloc[role_index]["role_id"],
            "department": roles.iloc[role_index]["department"],
            "joining_date": (
                today - pd.Timedelta(days=rng.randint(30, 2500))
            ).date().isoformat(),
            "status": "active",
        })

    employees = pd.DataFrame(employee_rows)

    # 4. ROLE SKILL TARGETS
    target_rows = []
    for role in roles.itertuples(index=False):
        selected = rng.sample(skill_ids, k=min(12, len(skill_ids)))
        for skill_id in selected:
            target_rows.append({
                "role_id": role.role_id,
                "skill_id": skill_id,
                "target_proficiency": rng.randint(3, 5),
                "effective_from": "2026-01-01",
                "effective_to": "",
            })

    role_targets = pd.DataFrame(target_rows)

    # 5. EMPLOYEE SKILL ASSESSMENTS
    employee_skill_rows = []
    for employee in employees.itertuples(index=False):
        role_skill_ids = role_targets.loc[
            role_targets["role_id"] == employee.role_id,
            "skill_id",
        ].tolist()

        assessed = rng.sample(
            role_skill_ids,
            k=max(1, min(len(role_skill_ids), 8)),
        )

        for skill_id in assessed:
            target = int(role_targets.loc[
                (role_targets["role_id"] == employee.role_id)
                & (role_targets["skill_id"] == skill_id),
                "target_proficiency",
            ].iloc[0])

            current = rng.randint(1, 5)
            employee_skill_rows.append({
                "employee_id": employee.employee_id,
                "skill_id": skill_id,
                "proficiency": current,
                "assessed_on": "2026-10-01",
                "assessment_status": "assessed",
                "gap": max(0, target - current),
            })

    employee_skills = pd.DataFrame(employee_skill_rows)

    # 6. COURSES
    course_rows = []
    for i in range(1, n["courses"] + 1):
        course_rows.append({
            "course_id": make_id("CRS", i),
            "course_name": f"Learning Course {i:04d}",
            "duration_hours": rng.choice([2, 4, 8, 12, 16, 24, 40]),
            "cost": round(rng.uniform(500, 15000), 2),
            "capacity": rng.randint(10, 100),
            "available_from": "2026-01-01",
            "available_to": "2027-12-31",
            "status": "active",
        })

    courses = pd.DataFrame(course_rows)
    course_ids = courses["course_id"].tolist()

    # 7. COURSE-SKILL BRIDGE TABLE
    course_skill_rows = []
    for course in courses.itertuples(index=False):
        taught_skills = rng.sample(
            skill_ids, k=min(rng.randint(1, 3), len(skill_ids))
        )
        for skill_id in taught_skills:
            course_skill_rows.append({
                "course_id": course.course_id,
                "skill_id": skill_id,
                "expected_proficiency_gain": rng.choice([1, 2]),
            })

    course_skills = pd.DataFrame(course_skill_rows)

    # 8. PREREQUISITES
    # Every prerequisite points to an earlier course, preventing cycles.
    prerequisite_rows = []
    for i in range(1, len(course_ids)):
        if rng.random() < 0.15:
            prerequisite_rows.append({
                "course_id": course_ids[i],
                "prerequisite_course_id": course_ids[
                    rng.randrange(i)
                ],
                "required": True,
            })

    prerequisites = pd.DataFrame(
        prerequisite_rows,
        columns=[
            "course_id", "prerequisite_course_id", "required"
        ],
    )

    # 9. DEPARTMENT BUDGETS
    budgets = pd.DataFrame([
        {
            "budget_id": f"BUD-{department}-2026",
            "department": department,
            "fiscal_year": 2026,
            "allocated_amount": 10000000.00,
            "currency": "INR",
        }
        for department in departments
    ])

    # 10. ENROLLMENTS
    # Sample unique employee-course pairs.
    possible_pairs = [
        (employee_id, course_id)
        for employee_id in employees["employee_id"]
        for course_id in course_ids
    ]

    if n["enrollments"] > len(possible_pairs):
        raise ValueError("Not enough unique employee-course pairs.")

    selected_pairs = rng.sample(possible_pairs, n["enrollments"])
    enrollment_rows = []

    for employee_id, course_id in selected_pairs:
        status = rng.choices(
            ["enrolled", "in_progress", "completed", "cancelled"],
            weights=[25, 25, 40, 10],
            k=1,
        )[0]

        enrollment_rows.append({
            "enrollment_id": f"ENR-{employee_id}-{course_id}",
            "employee_id": employee_id,
            "course_id": course_id,
            "enrollment_date": "2026-09-01",
            "status": status,
        })

    enrollments = pd.DataFrame(enrollment_rows)

    # 11. COMPLETION EVENTS
    completion_rows = []
    completed_enrollments = enrollments[
        enrollments["status"] == "completed"
    ]

    for i, enrollment in enumerate(
        completed_enrollments.itertuples(index=False), start=1
    ):
        completion_rows.append({
            "completion_id": f"CMP-2026-{i:06d}",
            "enrollment_id": enrollment.enrollment_id,
            "completion_date": "2026-10-01",
            "result": rng.choice(["passed", "failed"]),
        })

    completions = pd.DataFrame(
        completion_rows,
        columns=[
            "completion_id", "enrollment_id",
            "completion_date", "result",
        ],
    )

    # Export each table as CSV.
    output_path = OUTPUT_DIR / scale
    output_path.mkdir(parents=True, exist_ok=True)

    tables = {
        "employee": employees,
        "role": roles,
        "skill": skills,
        "role_skill_target": role_targets,
        "employee_skill": employee_skills,
        "course": courses,
        "course_skill": course_skills,
        "prerequisite": prerequisites,
        "enrollment": enrollments,
        "completion": completions,
        "budget": budgets,
    }

    for table_name, dataframe in tables.items():
        dataframe.to_csv(
            output_path / f"{table_name}.csv", index=False
        )

    manifest = {
        "seed": seed,
        "scale": scale,
        "generated_on": today.date().isoformat(),
        "row_counts": {
            name: len(dataframe)
            for name, dataframe in tables.items()
        },
        "source": "Synthetic data generated locally; no personal data.",
    }

    with open(output_path / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nGenerated {scale} dataset in: {output_path}")
    for name, dataframe in tables.items():
        print(f"{name:20s} {len(dataframe):>7,} rows")

    return tables


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scale", choices=["starter", "full"], default="starter"
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    generate_data(scale=args.scale, seed=args.seed)

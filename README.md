# Employee Skill Gap Analysis and Learning Path Recommendation System

## 1. Project Overview

This project generates reproducible synthetic employee-learning data and analyzes employee skill gaps against role-specific proficiency targets. It recommends eligible courses and allocates learning opportunities while considering prerequisites, course availability, capacity, and department budgets.

## 2. Key Features

- Reproducible synthetic data generation using a fixed random seed.
- Relational data tables with deterministic identifiers.
- Employee skill-gap analysis against role requirements.
- Course recommendations based on skill gaps and eligibility.
- Learning allocation subject to course capacity and department budgets.
- CSV, JSON, SQL, and SQLite exports.
- Ground-truth scenarios for important edge cases.
- Validation scripts and automated tests.

## 3. Technology Stack

- Python
- pandas and NumPy
- SQLite
- pytest
- Git and GitHub

## 4. Project Structure

data/
  starter/             # Small dataset for development
  ground_truth/        # Documented expected edge-case outcomes
outputs/
  sql/                 # SQLite database and SQL dump
  *.csv                # Analysis and allocation results
scripts/
  generate_data.py
  validate_data.py
  export_deliverables.py
  check_reproducibility.py
  validate_allocation.py
src/
  gap_analysis.py
  course_recommender.py
  allocate_learning.py
tests/
  test_pipeline.py
prompts/
  ai_prompt_history.md


## 5. Setup

Python 3.11 or a compatible Python version is recommended.

Create and activate a virtual environment, then install dependencies:

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install pandas numpy sqlalchemy pytest streamlit


## 6. Run the Project

Generate the starter dataset: python scripts/generate_data.py --scale starter


Validate the data: python scripts/validate_data.py --scale starter


Export JSON and SQL deliverables: python scripts/export_deliverables.py --scale starter


Run skill-gap analysis: python -m src.gap_analysis


Generate course recommendations: python -m src.course_recommender


Allocate learning opportunities: python -m src.allocate_learning


Validate allocations and run tests: python scripts/validate_allocation.py
                                    python -m pytest tests -v
                                    python scripts/check_reproducibility.py


Generate the full assessment-scale dataset: python scripts/generate_data.py --scale full
                                            python scripts/validate_data.py --scale full
                                            python scripts/export_deliverables.py --scale full


Run the full-scale pipeline only after confirming that the scripts accept and correctly use the full dataset paths.

## 7. Data Model

The generated dataset contains 11 tables:

- Employee: employee records and role assignments.
- Role: job roles and departments.
- Skill: skills and their categories.
- Role_skill_target: target proficiency levels for roles.
- Employee_skill: employee skill assessments.
- Course: course details, cost, capacity, and availability.
- Course_skill: skills taught by courses and expected gains.
- Prerequisite: required course prerequisites.
- Enrollment: employee course enrollments and status.
- Completion: course completion results.
- Budget: approved department learning budgets.

See "docs/data_dictionary.md" for the table columns and their meanings.

## 8. Edge Cases and Ground Truth

The ground-truth files document expected system behavior for:

1. Prerequisite violations.
2. Department budget overruns.
3. Duplicate completion records.
4. Missing or outdated skill reassessments.
5. Unavailable courses.

These scenarios are documented expected outcomes. They should be exercised using explicit test fixtures before claiming the application detects every case.

## 9. Reproducibility and Validation

The data generator uses a fixed seed by default. The reproducibility script compares generated CSV outputs. Data validation and allocation validation check important integrity and budget constraints.

Run the commands above to reproduce the results in your local environment.

## 10. AI Assistance and Personal Review

AI assistance was used to help plan and draft parts of the implementation, including synthetic-data export and ground-truth documentation. The generated code and recommendations must be reviewed and tested by the author before submission.

The author is responsible for verifying the data model, validation rules, recommendation logic, allocation constraints, assumptions, and limitations. The complete AI prompt history is maintained separately in "prompts/ai_prompt_history.md".

## 11. Limitations and Future Improvements

- The data is synthetic and does not represent real employees.
- Ground-truth definitions do not automatically demonstrate successful edge-case detection.
- Course recommendation quality depends on the generated skill assessments, role targets, and course-skill mappings.
- The allocation strategy is heuristic and may not produce a globally optimal allocation.
- A future version could include a dashboard, configurable reassessment windows, richer recommendation explanations, and more extensive edge-case tests.

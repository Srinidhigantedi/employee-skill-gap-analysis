# Employee Skill Gap Analysis and Learning Path Recommendation System

## 1. Project Overview

This project generates reproducible synthetic employee-learning data, identifies employee skill gaps against role-specific proficiency targets, recommends eligible learning courses, and allocates learning opportunities while considering prerequisites, course availability, course capacity, and department budgets.

## 2. Key Features

- Reproducible synthetic data generation using a fixed random seed.
- Relational data tables with deterministic identifiers.
- Employee skill-gap analysis against role requirements.
- Identification of skills that have not been assessed.
- Course recommendations based on employee skill gaps and course eligibility.
- Learning allocation subject to course capacity and department budgets.
- CSV, JSON, SQL, and SQLite exports.
- Separate ground-truth scenarios for important edge cases.
- Data validation scripts and automated tests.

## 3. Technology Stack

- Python 3.11
- pandas
- NumPy
- SQLAlchemy
- SQLite
- pytest
- Git and GitHub

## 4. Project Structure

```text
employee-skill-gap-analysis/
├── data/
│   ├── starter/
│   ├── full/
│   │   └── json/
│   └── ground_truth/
├── docs/
│   ├── ai_usage_disclosure.md
│   └── data_dictionary.md
├── outputs/
│   ├── full/
│   └── sql/
├── prompts/
│   └── ai_prompt_history.md
├── schema/
├── scripts/
│   ├── generate_data.py
│   ├── validate_data.py
│   ├── export_deliverables.py
│   ├── check_reproducibility.py
│   └── validate_allocation.py
├── src/
│   ├── gap_analysis.py
│   ├── course_recommender.py
│   └── allocate_learning.py
├── tests/
│   └── test_pipeline.py
├── requirements.txt
└── README.md
```

## 5. Setup

Python 3.11 or a compatible version is recommended.

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## 6. Run the Project

### Generate the starter dataset

```powershell
python scripts/generate_data.py --scale starter
```

### Validate starter data

```powershell
python scripts/validate_data.py --scale starter
```

### Export starter data

```powershell
python scripts/export_deliverables.py --scale starter
```

### Run starter analysis

```powershell
python -m src.gap_analysis
python -m src.course_recommender
python -m src.allocate_learning
```

### Generate the full assessment-scale dataset

```powershell
python scripts/generate_data.py --scale full
```

### Validate full data

```powershell
python scripts/validate_data.py --scale full
```

### Run full-scale analysis and recommendations

```powershell
python -m src.gap_analysis --scale full
python -m src.course_recommender --scale full
python -m src.allocate_learning --scale full
```

### Export full deliverables

```powershell
python scripts/export_deliverables.py --scale full
```

### Run automated tests and reproducibility check

```powershell
python -m pytest tests -v
python scripts/check_reproducibility.py
```

## 7. Data Model

The generated dataset contains 11 relational tables:

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

Refer to `docs/data_dictionary.md` for table columns and descriptions.

## 8. Edge Cases and Ground Truth

The ground-truth files document five expected edge-case scenarios:

1. Prerequisite violations.
2. Department budget overruns.
3. Duplicate completion records.
4. Missing or outdated skill reassessments.
5. Unavailable courses.

These scenarios document expected outcomes. They should be exercised using explicit test fixtures before claiming that every case is detected by the application.

## 9. Reproducibility and Validation

The synthetic data generator uses a fixed random seed by default.

The project includes scripts for data validation, allocation validation, and reproducibility checks.

The starter CSV reproducibility check was completed successfully for 11 generated CSV files. The full dataset was validated separately.

## 10. AI Assistance and Personal Review

AI assistance was used as a development aid for planning, implementation guidance, troubleshooting, code explanations, and documentation.

The AI prompt history is provided in `prompts/ai_prompt_history.md` as a reconstructed summary of development activities, not a verbatim transcript.

The author reviewed the commands and reported outputs during development. Further independent review is recommended before production use.

Refer to `docs/ai_usage_disclosure.md` for additional details.

## 11. Limitations and Future Improvements

- The data is synthetic and does not represent real employees.
- Ground-truth definitions do not automatically demonstrate successful edge-case detection.
- Course recommendation quality depends on generated skill assessments, role targets, and course-skill mappings.
- The allocation strategy is heuristic and may not produce a globally optimal allocation.
- Further edge-case testing and business-rule review are recommended.
- Future improvements could include a dashboard, configurable reassessment windows, richer recommendation explanations, and more extensive tests.s

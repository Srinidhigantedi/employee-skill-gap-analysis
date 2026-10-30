# AI Usage Disclosure

## How AI Was Used

AI assistance was used during project planning, implementation guidance, troubleshooting, code explanations, and preparation of validation and testing workflows.

AI was used as a development aid. The project code, generated outputs, and validation results were reviewed during development.

## Project Work and Validation

The project generates synthetic employee skill-gap and learning recommendation data.

The full-scale dataset contains:
- 5,000 employees
- 500 skills
- 1,000 courses
- 10,000 enrollments

The following activities were completed:
- Synthetic data generation for starter and full datasets.
- Data validation for data integrity and consistency.
- Employee skill-gap analysis.
- Eligible course recommendation generation.
- Learning allocation considering department budgets and course capacity.
- CSV, JSON, SQLite, and SQL exports.
- Ground-truth edge-case documentation.
- Automated testing using pytest.

## Validation Results

- Full dataset validation: 35 checks, 0 errors.
- Starter dataset validation: 0 errors reported.
- Automated test suite: 7 tests passed.
- Starter CSV reproducibility check: passed for 11 generated CSV files.
- Full-scale recommendation generation and learning allocation completed successfully.
- Eleven tables exported for the full dataset.

## Limitations

The reproducibility check was performed on the starter dataset, not the full dataset. The validation checks cover the implemented rules and do not guarantee that every possible business scenario is covered.

The generated data is synthetic and should not be treated as actual employee information.

## Transparency

AI assistance was used for guidance and development support. The implementation, commands, and reported outputs were reviewed during development. Further independent review is recommended before production use.
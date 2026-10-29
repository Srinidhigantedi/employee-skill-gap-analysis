
"""Export generated tables and create documented edge-case ground truth."""

import argparse
import json
import sqlite3
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

EDGE_CASES = [
    {
        "case_id": "EDGE-001",
        "scenario": "prerequisite_violation",
        "input_condition": "An employee attempts a course without passing its required prerequisite.",
        "expected_result": "BLOCK",
        "expected_reason": "Required prerequisite is not satisfied.",
        "severity": "high",
        "is_expected_to_pass": False,
    },
    {
        "case_id": "EDGE-002",
        "scenario": "budget_exceeded",
        "input_condition": "A proposed allocation makes department spending exceed its approved budget.",
        "expected_result": "REJECT_ALLOCATION",
        "expected_reason": "Department budget limit would be exceeded.",
        "severity": "high",
        "is_expected_to_pass": False,
    },
    {
        "case_id": "EDGE-003",
        "scenario": "duplicate_completion",
        "input_condition": "Two completion records exist for the same enrollment.",
        "expected_result": "FLAG_DUPLICATE",
        "expected_reason": "An enrollment should not have duplicate completion records.",
        "severity": "medium",
        "is_expected_to_pass": False,
    },
    {
        "case_id": "EDGE-004",
        "scenario": "missing_reassessment",
        "input_condition": "An employee's skill assessment is older than the allowed reassessment interval.",
        "expected_result": "FLAG_REASSESSMENT",
        "expected_reason": "The skill assessment needs to be refreshed before relying on it.",
        "severity": "medium",
        "is_expected_to_pass": False,
    },
    {
        "case_id": "EDGE-005",
        "scenario": "course_unavailable",
        "input_condition": "A recommendation is attempted for an inactive course or one outside its availability dates.",
        "expected_result": "EXCLUDE_COURSE",
        "expected_reason": "Unavailable courses must not be recommended.",
        "severity": "high",
        "is_expected_to_pass": False,
    },
]


def export_dataset(scale):
    data_dir = PROJECT_ROOT / "data" / scale
    json_dir = data_dir / "json"
    sql_dir = PROJECT_ROOT / "outputs" / "sql"

    if not data_dir.exists():
        raise FileNotFoundError(
            f"{data_dir} does not exist. Run generate_data.py first."
        )

    json_dir.mkdir(parents=True, exist_ok=True)
    sql_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(data_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV tables found in {data_dir}")

    tables = {}
    for csv_path in csv_files:
        df = pd.read_csv(csv_path, keep_default_na=False)
        table_name = csv_path.stem
        tables[table_name] = df

        # One JSON file per table, preserving the table's column names.
        df.to_json(
            json_dir / f"{table_name}.json",
            orient="records",
            indent=2,
            force_ascii=False,
        )

    # Create a portable SQLite database and SQL text dump.
    db_path = sql_dir / f"{scale}.sqlite"
    sql_path = sql_dir / f"{scale}.sql"

    with sqlite3.connect(db_path) as connection:
        for table_name, df in tables.items():
            df.to_sql(table_name, connection, if_exists="replace", index=False)

        with sql_path.open("w", encoding="utf-8") as sql_file:
            for statement in connection.iterdump():
                sql_file.write(statement + ";\n")

    # These are documented expected outcomes, not claims that the clean
    # generated dataset already contains these defects.
    ground_truth_dir = PROJECT_ROOT / "data" / "ground_truth"
    ground_truth_dir.mkdir(parents=True, exist_ok=True)

    ground_truth = pd.DataFrame(EDGE_CASES)
    ground_truth.to_csv(
        ground_truth_dir / "ground_truth.csv", index=False
    )

    with (ground_truth_dir / "ground_truth.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(EDGE_CASES, file, indent=2)

    summary = {
        "scale": scale,
        "tables_exported": sorted(tables.keys()),
        "row_counts": {
            name: int(len(df)) for name, df in tables.items()
        },
        "json_directory": str(json_dir.relative_to(PROJECT_ROOT)),
        "sqlite_database": str(db_path.relative_to(PROJECT_ROOT)),
        "sql_dump": str(sql_path.relative_to(PROJECT_ROOT)),
        "ground_truth_cases": len(EDGE_CASES),
        "note": (
            "Ground-truth cases define expected behavior for test scenarios. "
            "They do not imply the clean source tables contain these defects."
        ),
    }

    summary_path = PROJECT_ROOT / "outputs" / f"{scale}_export_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(f"Exported {len(tables)} tables for scale: {scale}")
    print(f"JSON files: {json_dir}")
    print(f"SQLite database: {db_path}")
    print(f"SQL dump: {sql_path}")
    print(f"Ground-truth cases: {len(ground_truth)}")
    print(f"Export summary: {summary_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export generated tables and ground-truth scenarios."
    )
    parser.add_argument(
        "--scale",
        choices=["starter", "full"],
        default="starter",
    )
    args = parser.parse_args()
    export_dataset(args.scale)

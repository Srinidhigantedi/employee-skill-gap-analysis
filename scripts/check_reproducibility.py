
"""Check that repeated data generation produces identical CSV files."""

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "starter"
GENERATOR = ROOT / "scripts" / "generate_data.py"


def csv_hashes():
    hashes = {}

    for path in sorted(DATA_DIR.glob("*.csv")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes[path.name] = digest

    return hashes


def run_generator():
    subprocess.run(
        [sys.executable, str(GENERATOR), "--scale", "starter"],
        cwd=ROOT,
        check=True,
    )


def main():
    print("Run 1: generating starter data...")
    run_generator()
    first_run = csv_hashes()

    print("\nRun 2: generating starter data again...")
    run_generator()
    second_run = csv_hashes()

    if first_run == second_run:
        print("\nPASS: All generated CSV files are reproducible.")
        print(f"CSV files compared: {len(first_run)}")
        return

    print("\nFAIL: Generated CSV files differ.")
    for filename in sorted(set(first_run) | set(second_run)):
        if first_run.get(filename) != second_run.get(filename):
            print(f"Different or missing file: {filename}")

    raise SystemExit(1)


if __name__ == "__main__":
    main()

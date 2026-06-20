from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from .constants import COLUMN_TYPE, DATA_COLUMNS
from .data_store import DefectDataStore


def run_csv_check() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / "smoke_defect_data.csv"
        store = DefectDataStore(temp_file)

        assert list(store.defect_data.columns) == DATA_COLUMNS
        inserted = store.add_defect_records(
            [
                {"type": "dirty", "confidence": 0.91, "x1": 10, "y1": 20, "x2": 30, "y2": 40},
                {"type": "scratch", "confidence": 0.82, "x1": 50, "y1": 60, "x2": 70, "y2": 80},
            ]
        )
        assert inserted == 2

        store.save()
        reloaded = DefectDataStore(temp_file)
        assert len(reloaded.defect_data) == 2
        assert set(reloaded.defect_data[COLUMN_TYPE]) == {"dirty", "scratch"}

    print("CSV read/write check passed.")


def run_model_check() -> None:
    from .inference import load_model

    model = load_model()
    class_count = len(getattr(model, "names", {}))
    print(f"Model load check passed. classes={class_count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run lightweight smoke checks for IPDDS.")
    parser.add_argument("--check-model", action="store_true", help="Also load the YOLO model weights.")
    args = parser.parse_args()

    run_csv_check()
    if args.check_model:
        run_model_check()


if __name__ == "__main__":
    main()

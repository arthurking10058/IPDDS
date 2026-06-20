from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

from .constants import DISPLAY_TIME_FORMAT, INTERVAL_MAP, TIME_RANGE_MAP
from .data_store import DefectDataStore


@dataclass
class StatsReport:
    generated_at: str
    time_range_label: str
    interval_label: str
    summary: dict
    batch_summaries: list[dict[str, object]]
    shift_summaries: list[dict[str, object]]
    scratch_time_series: list[dict[str, object]]
    dirty_time_series: list[dict[str, object]]


def _series_to_rows(series) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if series.empty:
        return rows
    for ts, value in series.items():
        rows.append(
            {
                "time": ts.strftime(DISPLAY_TIME_FORMAT),
                "count": int(value),
            }
        )
    return rows


def build_stats_report(store: DefectDataStore, time_range_label: str = "30分钟", interval_label: str = "5分钟") -> StatsReport:
    minutes = TIME_RANGE_MAP[time_range_label]
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=minutes)

    scratch_counts = store.get_defect_counts("scratch", start_time, end_time, INTERVAL_MAP[interval_label])
    dirty_counts = store.get_defect_counts("dirty", start_time, end_time, INTERVAL_MAP[interval_label])

    return StatsReport(
        generated_at=datetime.now().strftime(DISPLAY_TIME_FORMAT),
        time_range_label=time_range_label,
        interval_label=interval_label,
        summary=store.get_summary(),
        batch_summaries=store.get_batch_summaries(),
        shift_summaries=store.get_shift_summaries(),
        scratch_time_series=_series_to_rows(scratch_counts),
        dirty_time_series=_series_to_rows(dirty_counts),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an offline statistics report for IPDDS.")
    parser.add_argument("--time-range", choices=list(TIME_RANGE_MAP.keys()), default="30分钟")
    parser.add_argument("--interval", choices=list(INTERVAL_MAP.keys()), default="5分钟")
    args = parser.parse_args()

    store = DefectDataStore()
    report = build_stats_report(store, time_range_label=args.time_range, interval_label=args.interval)
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

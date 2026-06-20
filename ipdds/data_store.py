from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .constants import (
    COLUMN_CONFIDENCE,
    COLUMN_TIME,
    COLUMN_TYPE,
    CSV_ENCODING,
    DATA_COLUMNS,
    DATA_FILE,
    DISPLAY_TIME_FORMAT,
    FOCUS_DEFECT_TYPES,
    LEGACY_COLUMN_ALIASES,
)


class DefectDataStore:
    """CSV-backed defect record storage and query helpers."""

    def __init__(self, data_file=DATA_FILE):
        self.data_file = Path(data_file)
        self.defect_data = self._load()

    def _load(self) -> pd.DataFrame:
        if not self.data_file.exists():
            df = pd.DataFrame(columns=DATA_COLUMNS)
        else:
            df = self._read_csv()
        return self._normalize_columns(df)

    def _read_csv(self) -> pd.DataFrame:
        for encoding in (CSV_ENCODING, "utf-8"):
            try:
                return pd.read_csv(self.data_file, encoding=encoding)
            except UnicodeDecodeError:
                continue
        return pd.read_csv(self.data_file)

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {column: LEGACY_COLUMN_ALIASES[column] for column in df.columns if column in LEGACY_COLUMN_ALIASES}
        normalized = df.rename(columns=rename_map).copy()

        if COLUMN_TIME not in normalized.columns or COLUMN_TYPE not in normalized.columns:
            return pd.DataFrame(columns=DATA_COLUMNS)

        for column in DATA_COLUMNS:
            if column not in normalized.columns:
                normalized[column] = pd.NA

        normalized = normalized[DATA_COLUMNS]
        normalized[COLUMN_TIME] = pd.to_datetime(normalized[COLUMN_TIME], errors="coerce")
        return normalized

    def add_defect_records(self, records: list[dict[str, object]]) -> int:
        if not records:
            return 0
        current_time = datetime.now().strftime(DISPLAY_TIME_FORMAT)
        new_records = [
            {
                COLUMN_TIME: current_time,
                COLUMN_TYPE: record["type"],
                COLUMN_CONFIDENCE: record["confidence"],
                "x1": record["x1"],
                "y1": record["y1"],
                "x2": record["x2"],
                "y2": record["y2"],
            }
            for record in records
        ]
        new_df = pd.DataFrame(new_records, columns=DATA_COLUMNS)
        if self.defect_data.empty:
            self.defect_data = new_df
        else:
            self.defect_data = pd.concat([self.defect_data, new_df], ignore_index=True)
        self.defect_data[COLUMN_TIME] = pd.to_datetime(self.defect_data[COLUMN_TIME], errors="coerce")
        return len(new_records)

    def save(self) -> None:
        self.defect_data.to_csv(self.data_file, index=False, encoding=CSV_ENCODING)

    def get_export_data(self, data: pd.DataFrame | None = None) -> pd.DataFrame:
        export_df = self.defect_data.copy() if data is None else data.copy()
        if export_df.empty:
            return pd.DataFrame(columns=DATA_COLUMNS)
        if COLUMN_TIME in export_df.columns:
            export_df[COLUMN_TIME] = pd.to_datetime(export_df[COLUMN_TIME], errors="coerce").dt.strftime(DISPLAY_TIME_FORMAT)
        return export_df.reindex(columns=DATA_COLUMNS)

    def get_cap_count(self) -> int:
        return int((self.defect_data[COLUMN_TYPE] == "cap").sum())

    def get_total_defect_count(self) -> int:
        return int(self.defect_data[COLUMN_TYPE].isin(FOCUS_DEFECT_TYPES).sum())

    def get_dirty_count(self) -> int:
        return int((self.defect_data[COLUMN_TYPE] == "dirty").sum())

    def get_scratch_count(self) -> int:
        return int((self.defect_data[COLUMN_TYPE] == "scratch").sum())

    def get_filtered_data(self, defect_types: list[str], start_dt, end_dt) -> pd.DataFrame:
        df = self.defect_data.copy()
        if defect_types:
            df = df[df[COLUMN_TYPE].isin(defect_types)]
        if not df.empty:
            df = df[(df[COLUMN_TIME] >= start_dt) & (df[COLUMN_TIME] <= end_dt)]
        return df

    def get_defect_counts(self, defect_type: str, start_ts, end_ts, freq: str):
        time_mask = (self.defect_data[COLUMN_TIME] >= start_ts) & (self.defect_data[COLUMN_TIME] <= end_ts)
        type_mask = self.defect_data[COLUMN_TYPE] == defect_type
        filtered = self.defect_data[time_mask & type_mask]
        return filtered.groupby(pd.Grouper(key=COLUMN_TIME, freq=freq))[COLUMN_TYPE].count()

    def get_summary(self, data: pd.DataFrame | None = None) -> dict[str, Any]:
        df = self.defect_data if data is None else data.copy()
        if df.empty:
            return {
                "total_records": 0,
                "cap_count": 0,
                "defect_total": 0,
                "dirty_count": 0,
                "scratch_count": 0,
                "avg_confidence": None,
                "defect_rate": 0.0,
                "time_range_text": "暂无记录",
                "busiest_hour_text": "暂无记录",
                "top_defect_type_text": "暂无记录",
                "recent_summary_text": "暂无可汇总的检测记录。",
                "type_breakdown": {},
            }

        normalized = df.copy()
        normalized[COLUMN_TIME] = pd.to_datetime(normalized[COLUMN_TIME], errors="coerce")
        normalized = normalized.dropna(subset=[COLUMN_TIME])
        if normalized.empty:
            return {
                "total_records": 0,
                "cap_count": 0,
                "defect_total": 0,
                "dirty_count": 0,
                "scratch_count": 0,
                "avg_confidence": None,
                "defect_rate": 0.0,
                "time_range_text": "暂无有效时间记录",
                "busiest_hour_text": "暂无记录",
                "top_defect_type_text": "暂无记录",
                "recent_summary_text": "当前记录缺少有效时间字段，无法生成摘要。",
                "type_breakdown": {},
            }

        total_records = int(len(normalized))
        cap_count = int((normalized[COLUMN_TYPE] == "cap").sum())
        defect_df = normalized[normalized[COLUMN_TYPE].isin(FOCUS_DEFECT_TYPES)]
        defect_total = int(len(defect_df))
        dirty_count = int((normalized[COLUMN_TYPE] == "dirty").sum())
        scratch_count = int((normalized[COLUMN_TYPE] == "scratch").sum())

        confidence_series = pd.to_numeric(normalized[COLUMN_CONFIDENCE], errors="coerce").dropna()
        avg_confidence = float(confidence_series.mean()) if not confidence_series.empty else None
        defect_rate = float(defect_total / cap_count) if cap_count else 0.0

        start_time = normalized[COLUMN_TIME].min()
        end_time = normalized[COLUMN_TIME].max()
        time_range_text = f"{start_time.strftime(DISPLAY_TIME_FORMAT)} 至 {end_time.strftime(DISPLAY_TIME_FORMAT)}"

        hourly_counts = (
            normalized.groupby(pd.Grouper(key=COLUMN_TIME, freq="1h"))[COLUMN_TYPE]
            .count()
            .sort_values(ascending=False)
        )
        if not hourly_counts.empty and hourly_counts.iloc[0] > 0:
            busiest_hour = hourly_counts.index[0]
            busiest_hour_text = f"{busiest_hour.strftime('%Y-%m-%d %H:00')}，共 {int(hourly_counts.iloc[0])} 条"
        else:
            busiest_hour_text = "暂无记录"

        type_breakdown_series = normalized[COLUMN_TYPE].value_counts()
        type_breakdown = {str(key): int(value) for key, value in type_breakdown_series.items()}
        if defect_df.empty:
            top_defect_type_text = "暂无缺陷记录"
        else:
            top_defect_series = defect_df[COLUMN_TYPE].value_counts()
            top_type = str(top_defect_series.index[0])
            top_count = int(top_defect_series.iloc[0])
            top_defect_type_text = f"{top_type}（{top_count} 条）"

        recent_df = normalized.sort_values(COLUMN_TIME, ascending=False).head(20)
        recent_type_counts = recent_df[COLUMN_TYPE].value_counts()
        recent_parts = [f"{key} {int(value)} 条" for key, value in recent_type_counts.items()]
        recent_summary_text = "最近 20 条记录：" + "，".join(recent_parts)

        return {
            "total_records": total_records,
            "cap_count": cap_count,
            "defect_total": defect_total,
            "dirty_count": dirty_count,
            "scratch_count": scratch_count,
            "avg_confidence": avg_confidence,
            "defect_rate": defect_rate,
            "time_range_text": time_range_text,
            "busiest_hour_text": busiest_hour_text,
            "top_defect_type_text": top_defect_type_text,
            "recent_summary_text": recent_summary_text,
            "type_breakdown": type_breakdown,
        }

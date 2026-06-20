from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "defect_data.csv"
WEIGHTS_FILE = BASE_DIR / "weights" / "best.pt"
IMAGE_DIR = BASE_DIR / "image"
CSV_ENCODING = "utf-8-sig"
DISPLAY_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
EXPORT_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

COLUMN_TIME = "时间"
COLUMN_TYPE = "类型"
COLUMN_CONFIDENCE = "置信度"
BOX_COLUMNS = ["x1", "y1", "x2", "y2"]

DATA_COLUMNS = [COLUMN_TIME, COLUMN_TYPE, COLUMN_CONFIDENCE, *BOX_COLUMNS]
DEFECT_TYPES = ["cap", "dirty", "scratch"]
FOCUS_DEFECT_TYPES = ["dirty", "scratch"]
LEGACY_COLUMN_ALIASES = {
    "time": COLUMN_TIME,
    "label": COLUMN_TYPE,
    "class": COLUMN_TYPE,
    "confidence": COLUMN_CONFIDENCE,
}

TIME_RANGE_MAP = {
    "30分钟": 30,
    "1小时": 60,
    "6小时": 360,
    "24小时": 1440,
}

INTERVAL_MAP = {
    "1分钟": "1min",
    "5分钟": "5min",
    "10分钟": "10min",
    "30分钟": "30min",
}

STREAMLIT_PAGE = {
    "page_title": "瓶盖检测",
    "layout": "wide",
    "page_icon": "🔍",
}

PAGE_OPTIONS = {
    "检测页": "detect",
    "统计页": "stats",
}

APP_STYLE = """
<style>
:root {
    --app-text: #5f5368;
    --soft-blue: #64a8eb;
    --soft-pink: #ff8f96;
    --soft-lilac: #f4ecfb;
    --card-bg: linear-gradient(145deg, rgba(255, 255, 255, 0.84), rgba(255, 248, 252, 0.72));
    --card-border: rgba(255, 255, 255, 0.48);
    --card-shadow: 0 18px 42px rgba(166, 141, 178, 0.16);
    --input-bg: rgba(255, 255, 255, 0.94);
    --muted-text: #7a6e88;
    --divider-line: rgba(255, 255, 255, 0.42);
    --card-padding: 0.82rem;
}

.stApp {
    color: var(--app-text);
    background:
        radial-gradient(circle at top left, rgba(255, 255, 255, 0.42), transparent 30%),
        radial-gradient(circle at top right, rgba(255, 255, 255, 0.28), transparent 24%),
        linear-gradient(110deg, #ffd2d8 0%, #f3dbe8 47%, #d9dbfd 100%);
}

[data-testid="stAppViewContainer"] {
    background: transparent;
}

[data-testid="stHeader"] {
    background: rgba(255, 250, 252, 0.74) !important;
    backdrop-filter: blur(14px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.52);
}

[data-testid="stToolbar"] button,
[data-testid="stHeaderActionElements"] button,
[data-testid="stMainMenuButton"] button,
[data-testid="stBaseButton-headerNoPadding"],
[data-testid="stStatusWidget"] {
    color: var(--muted-text) !important;
}

[data-testid="stSidebar"] {
    background: rgba(255, 250, 252, 0.68);
    backdrop-filter: blur(12px);
}

.block-container {
    padding-top: 5.4rem;
    padding-bottom: 3rem;
}

.layout-band {
    margin: 1.2rem 0 1.5rem;
    padding: 1.15rem 1rem 1.25rem;
    border-radius: 30px;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.08));
    border: 1px solid rgba(255, 255, 255, 0.3);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.layout-band--hero {
    margin-top: 0.2rem;
}

.layout-band--charts,
.layout-band--insights {
    margin-top: 1.6rem;
}

[data-testid="stHorizontalBlock"] {
    gap: 1.15rem;
}

[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"],
.stExpander,
[data-testid="stImage"] {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 24px;
    box-shadow: var(--card-shadow);
    backdrop-filter: blur(12px);
}

[data-testid="stPlotlyChart"] {
    padding: var(--card-padding);
}

[data-testid="stImage"] {
    padding: var(--card-padding);
}

[data-testid="stDataFrame"] {
    padding: calc(var(--card-padding) - 0.3rem);
    overflow: hidden;
}

[data-testid="stDataFrame"] [data-testid="stTable"] {
    background: rgba(255, 255, 255, 0.95) !important;
}

[data-testid="stDataFrame"] thead {
    box-shadow: inset 0 -1px 0 rgba(214, 193, 227, 0.35);
}

[data-testid="stDataFrame"] thead tr th {
    background: linear-gradient(90deg, rgba(252, 197, 204, 0.95), rgba(222, 224, 255, 0.95)) !important;
    color: var(--app-text) !important;
    border-bottom: 1px solid rgba(214, 193, 227, 0.45) !important;
    font-weight: 800 !important;
    letter-spacing: 0.01em;
    padding-top: 0.88rem !important;
    padding-bottom: 0.88rem !important;
}

[data-testid="stDataFrame"] tbody tr:nth-child(odd) div {
    background: rgba(255, 248, 251, 0.95) !important;
}

[data-testid="stDataFrame"] tbody tr:nth-child(even) div {
    background: rgba(247, 243, 255, 0.95) !important;
}

[data-testid="stDataFrame"] tbody tr:hover div {
    background: rgba(255, 238, 244, 0.92) !important;
}

[data-testid="stDataFrame"] div,
[data-testid="stDataFrame"] span {
    color: var(--app-text) !important;
}

[data-testid="stDataFrame"] tbody td,
[data-testid="stDataFrame"] tbody td div {
    min-height: 2.8rem !important;
    line-height: 1.3 !important;
    align-items: center !important;
    padding-top: 0.7rem !important;
    padding-bottom: 0.7rem !important;
    border-bottom: 1px solid rgba(231, 220, 239, 0.65) !important;
}

[data-testid="stDataFrame"] tbody tr:last-child td,
[data-testid="stDataFrame"] tbody tr:last-child td div {
    border-bottom: none !important;
}

.stButton > button,
.stDownloadButton > button {
    min-height: 3.28rem;
    border: 1px solid rgba(255, 255, 255, 0.62) !important;
    border-radius: 18px !important;
    color: var(--app-text) !important;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(250, 237, 245, 0.92)) !important;
    box-shadow: 0 10px 24px rgba(171, 149, 182, 0.14);
    font-weight: 700 !important;
    letter-spacing: 0.01em;
    transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, border-color 0.18s ease;
}

.stButton > button {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(242, 247, 255, 0.94)) !important;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, rgba(255, 251, 252, 0.97), rgba(255, 236, 241, 0.95)) !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 14px 28px rgba(171, 149, 182, 0.18);
    border-color: rgba(255, 186, 197, 0.72) !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.99), rgba(226, 242, 255, 0.97)) !important;
}

.stDownloadButton > button:hover {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(255, 228, 235, 0.96)) !important;
}

.stButton > button:focus,
.stDownloadButton > button:focus {
    border-color: rgba(255, 154, 162, 0.74) !important;
    box-shadow: 0 0 0 4px rgba(255, 173, 188, 0.18), 0 14px 28px rgba(171, 149, 182, 0.18) !important;
}

.stButton > button:disabled,
.stDownloadButton > button:disabled {
    color: rgba(95, 83, 104, 0.42) !important;
    border-color: rgba(255, 255, 255, 0.35) !important;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.5), rgba(243, 236, 243, 0.4)) !important;
    box-shadow: none !important;
    opacity: 0.82;
    cursor: not-allowed;
}

.stExpander {
    overflow: hidden;
}

.stExpander .stExpanderHeader {
    color: var(--soft-pink) !important;
    font-weight: 700;
    font-size: 1rem;
}

.stExpander .stExpanderContent {
    background: transparent !important;
}

.stSelectbox > div > div,
.stDateInput > div > div,
.stMultiSelect [data-baseweb="select"],
.stMultiSelect > div > div,
.stDateInput input {
    background: var(--input-bg) !important;
    border: 1px solid rgba(214, 193, 227, 0.58) !important;
    border-radius: 18px !important;
    color: var(--app-text) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}

.stDateInput input,
.stSelectbox div[data-baseweb="select"] *,
.stMultiSelect div[data-baseweb="select"] * {
    color: var(--app-text) !important;
}

.stMultiSelect label,
.stDateInput label {
    color: var(--soft-pink) !important;
}

[data-baseweb="tag"] {
    background: linear-gradient(135deg, #ff9da4, #ffb6be) !important;
    color: white !important;
    border-radius: 12px !important;
    border: none !important;
}

div[data-baseweb="popover"],
div[data-baseweb="calendar"] {
    background: rgba(255, 255, 255, 0.96) !important;
    border: 1px solid rgba(214, 193, 227, 0.58) !important;
    box-shadow: 0 18px 40px rgba(156, 132, 177, 0.16) !important;
    border-radius: 20px !important;
    color: var(--app-text) !important;
}

li[role="option"],
div[role="option"] {
    background: rgba(255, 255, 255, 0.96) !important;
    color: var(--app-text) !important;
}

li[role="option"]:hover,
div[role="option"]:hover {
    background: rgba(255, 236, 242, 0.95) !important;
    color: var(--soft-pink) !important;
}

div[data-baseweb="calendar"] td {
    color: var(--soft-pink) !important;
}

div[data-baseweb="calendar"] td:hover {
    background: rgba(255, 221, 228, 0.7) !important;
}

div[data-baseweb="calendar"] td[aria-selected="true"] {
    background: linear-gradient(135deg, #ff9aa2, #f6b6d0) !important;
    color: white !important;
}

.stCaption,
[data-testid="stCaptionContainer"] {
    color: rgba(95, 83, 104, 0.82) !important;
}

.section-title-card {
    margin-bottom: 0.9rem;
    padding: 0.92rem 1.05rem 0.9rem;
    border-radius: 22px;
    background: linear-gradient(145deg, rgba(255, 255, 255, 0.8), rgba(253, 243, 248, 0.66));
    border: 1px solid rgba(255, 255, 255, 0.54);
    box-shadow: 0 14px 30px rgba(166, 141, 178, 0.11);
    backdrop-filter: blur(10px);
}

.section-kicker {
    display: inline-block;
    margin-bottom: 0.26rem;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: rgba(122, 110, 136, 0.72);
}

.section-heading {
    margin: 0;
    font-size: 1.74rem;
    font-weight: 800;
    line-height: 1.18;
    letter-spacing: 0.01em;
}

.section-heading .blue {
    color: #5fa7ea;
}

.section-heading .pink {
    color: #ff9199;
}

.section-heading .divider {
    display: inline-block;
    margin: 0 0.26rem;
    color: rgba(122, 110, 136, 0.34);
    font-weight: 600;
}

.metric-card {
    padding: 1.1rem 1rem;
    border-radius: 24px;
    border: 1px solid rgba(255, 255, 255, 0.62);
    box-shadow: 0 16px 34px rgba(171, 149, 182, 0.12);
    backdrop-filter: blur(12px);
    min-height: 156px;
}

.metric-card--blue {
    background: linear-gradient(160deg, rgba(255, 255, 255, 0.92), rgba(220, 238, 255, 0.88));
}

.metric-card--pink {
    background: linear-gradient(160deg, rgba(255, 255, 255, 0.92), rgba(255, 228, 233, 0.9));
}

.metric-label {
    margin: 0 0 0.55rem;
    font-size: 0.96rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}

.metric-label--blue {
    color: #559fe4;
}

.metric-label--pink {
    color: #ff8b93;
}

.metric-value {
    margin: 0;
    font-size: 2.35rem;
    font-weight: 800;
    line-height: 1.1;
    color: var(--app-text);
}

.metric-note {
    margin: 0.6rem 0 0;
    font-size: 0.84rem;
    color: rgba(95, 83, 104, 0.72);
}

video {
    border-radius: 24px !important;
    border: 6px solid rgba(255, 255, 255, 0.7) !important;
    box-shadow: 0 20px 40px rgba(160, 138, 176, 0.16) !important;
    background: rgba(255, 255, 255, 0.82) !important;
}

[data-testid="stPlotlyChart"] .modebar {
    background: rgba(255, 255, 255, 0.72) !important;
    border: 1px solid rgba(214, 193, 227, 0.48) !important;
    border-radius: 14px !important;
    box-shadow: 0 10px 24px rgba(166, 141, 178, 0.12) !important;
}

[data-testid="stPlotlyChart"] .modebar-btn path {
    fill: rgba(95, 83, 104, 0.72) !important;
}

[data-testid="stPlotlyChart"] + div,
.stExpander > div:first-child,
[data-testid="stDataFrame"] > div:first-child {
    border-radius: 22px !important;
}

.stMarkdown,
p,
label {
    color: var(--app-text);
}

hr {
    border-color: var(--divider-line);
}
</style>
"""

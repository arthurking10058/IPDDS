from __future__ import annotations

import io
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image
from streamlit_webrtc import VideoTransformerBase, webrtc_streamer

from .constants import COLUMN_TIME, DEFECT_TYPES, EXPORT_TIMESTAMP_FORMAT, INTERVAL_MAP, PAGE_OPTIONS, TIME_RANGE_MAP
from .stats_report import build_stats_report


class FrameCaptureTransformer(VideoTransformerBase):
    """Capture the latest frame from the webcam stream."""

    def __init__(self):
        self.frame = None

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")
        self.frame = image
        return frame


def ensure_session_state() -> None:
    defaults = {
        "captured_image": None,
        "detection_results": None,
        "filtered_data": None,
        "active_page": "detect",
        "dirty_time_range": "30分钟",
        "dirty_interval": "5分钟",
        "scratch_time_range": "30分钟",
        "scratch_interval": "5分钟",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def page_navigation() -> str:
    st.markdown(
        """
        <div class="section-title-card" style="padding-bottom: 0.8rem;">
            <div class="section-kicker">Workspace View</div>
            <h3 class="section-heading"><span class="blue">主线</span><span class="divider">/</span><span class="pink">视图切换</span></h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    labels = list(PAGE_OPTIONS.keys())
    current_value = st.session_state.active_page
    current_index = list(PAGE_OPTIONS.values()).index(current_value) if current_value in PAGE_OPTIONS.values() else 0
    selected_label = st.radio(
        "主线视图",
        options=labels,
        index=current_index,
        horizontal=True,
        label_visibility="collapsed",
    )
    selected_page = PAGE_OPTIONS[selected_label]
    st.session_state.active_page = selected_page
    return selected_page


def render_section_title(kicker: str, left_text: str, right_text: str | None = None) -> None:
    if right_text:
        heading = (
            f'<span class="blue">{left_text}</span>'
            '<span class="divider">/</span>'
            f'<span class="pink">{right_text}</span>'
        )
    else:
        heading = f'<span class="blue">{left_text}</span>'
    st.markdown(
        f"""
        <div class="section-title-card">
            <div class="section-kicker">{kicker}</div>
            <h3 class="section-heading">{heading}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


def video_stream_component():
    render_section_title("Live Vision", "实时视频")
    return webrtc_streamer(
        key="iriun-webcam",
        video_processor_factory=FrameCaptureTransformer,
        media_stream_constraints={
            "video": {"width": {"ideal": 1280}, "height": {"ideal": 720}},
            "audio": False,
        },
        async_processing=True,
    )


def defect_stats_component(defect_store) -> None:
    render_section_title("Quality Snapshot", "缺陷", "统计")
    cap_count = defect_store.get_cap_count()
    defect_total = defect_store.get_total_defect_count()
    dirty_count = defect_store.get_dirty_count()
    scratch_count = defect_store.get_scratch_count()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card metric-card--blue">
                <p class="metric-label metric-label--blue">瓶盖 / 缺陷</p>
                <p class="metric-value">{cap_count}/{defect_total}</p>
                <p class="metric-note">展示当前记录中的总瓶盖数与重点缺陷数</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card metric-card--pink">
                <p class="metric-label metric-label--pink">污渍 / 划痕</p>
                <p class="metric-value">{dirty_count}/{scratch_count}</p>
                <p class="metric-note">聚焦展示两类核心缺陷的实时累计情况</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def capture_component():
    render_section_title("Capture Control", "拍摄", "画面")
    image_placeholder = st.empty()

    if st.session_state.captured_image is not None:
        current_image = (
            st.session_state.detection_results
            if st.session_state.detection_results is not None
            else st.session_state.captured_image
        )
        image_placeholder.image(current_image, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    action = None
    with col1:
        if st.button("📸 拍摄", use_container_width=True):
            action = "capture"
    with col2:
        if st.button("💾 保存", disabled=st.session_state.captured_image is None, use_container_width=True):
            action = "save"
    with col3:
        if st.button("🔍 识别", disabled=st.session_state.captured_image is None, use_container_width=True):
            action = "detect"
    return action


def render_time_chart(title: str, title_color: str, bar_color: str, line_color: str, counts, empty_text: str):
    st.markdown(
        f"""
        <center>
            <p style="margin: 0 0 0.18rem; font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(122,110,136,0.72);">
                Trend Overview
            </p>
            <h3 style="color: {title_color}; margin-bottom: 0.38rem; font-size: 1.36rem; font-weight: 800;">{title}</h3>
        </center>
        """,
        unsafe_allow_html=True,
    )
    fig = go.Figure()
    if not counts.empty:
        time_labels = [ts.strftime("%H:%M") for ts in counts.index]
        fig.add_trace(
            go.Bar(
                x=time_labels,
                y=counts.values,
                marker=dict(color=bar_color, line=dict(color="rgba(255,255,255,0.92)", width=1.4)),
                opacity=0.92,
                text=counts.values,
                textposition="auto",
                textfont=dict(color="#5f5368", size=15, weight="bold"),
                hovertemplate="时间 %{x}<br>数量 %{y}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=time_labels,
                y=counts.values,
                mode="lines+markers",
                line=dict(color=line_color, width=3, shape="spline", smoothing=0.45),
                marker=dict(size=9, color="white", line=dict(color=line_color, width=2.2)),
                hovertemplate="时间 %{x}<br>数量 %{y}<extra></extra>",
            )
        )
    else:
        fig.add_annotation(
            text=empty_text,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="#7a6e88"),
        )

    fig.update_layout(
        margin=dict(t=20, b=50, l=40, r=20),
        xaxis_title="时间",
        yaxis_title="缺陷数量",
        height=300,
        showlegend=False,
        plot_bgcolor="rgba(255,255,255,0.72)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#5f5368"),
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.96)",
            bordercolor="rgba(214,193,227,0.6)",
            font=dict(color="#5f5368"),
        ),
        xaxis=dict(
            tickangle=45,
            showgrid=False,
            showline=True,
            linecolor="rgba(182,166,198,0.55)",
            tickfont=dict(color="#7a6e88", size=13),
            title_font=dict(color=line_color, size=15),
        ),
        yaxis=dict(
            gridcolor="rgba(214,193,227,0.36)",
            zeroline=False,
            tickfont=dict(color="#7a6e88", size=13),
            title_font=dict(color=line_color, size=15),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


def scratch_time_chart(defect_store) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<p style="color: #3399FF; font-size: 16px; margin-bottom: 0px;">统计时长</p>', unsafe_allow_html=True)
        time_range = st.selectbox("统计时长", list(TIME_RANGE_MAP.keys()), key="scratch_time_range", label_visibility="collapsed")
    with col2:
        st.markdown('<p style="color: #3399FF; font-size: 16px; margin-bottom: 0px;">统计间隔</p>', unsafe_allow_html=True)
        interval = st.selectbox("统计间隔", list(INTERVAL_MAP.keys()), index=1, key="scratch_interval", label_visibility="collapsed")
    report = build_stats_report(defect_store, time_range_label=time_range, interval_label=interval)
    counts = pd.Series(
        [row["count"] for row in report.scratch_time_series],
        index=pd.to_datetime([row["time"] for row in report.scratch_time_series]),
    )
    render_time_chart("划痕时间统计", "#66B3FF", "#66B3FF", "#3399FF", counts, "该时间段内无划痕数据")


def dirty_time_chart(defect_store) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<p style="color: #FF6666; font-size: 16px; margin-bottom: 0px;">统计时长</p>', unsafe_allow_html=True)
        time_range = st.selectbox("统计时长", list(TIME_RANGE_MAP.keys()), key="dirty_time_range", label_visibility="collapsed")
    with col2:
        st.markdown('<p style="color: #FF6666; font-size: 16px; margin-bottom: 0px;">统计间隔</p>', unsafe_allow_html=True)
        interval = st.selectbox("统计间隔", list(INTERVAL_MAP.keys()), index=1, key="dirty_interval", label_visibility="collapsed")
    report = build_stats_report(defect_store, time_range_label=time_range, interval_label=interval)
    counts = pd.Series(
        [row["count"] for row in report.dirty_time_series],
        index=pd.to_datetime([row["time"] for row in report.dirty_time_series]),
    )
    render_time_chart("污渍时间统计", "#FF9999", "#FF9999", "#FF6666", counts, "该时间段内无污渍数据")


def defect_pie_chart(defect_store) -> None:
    st.markdown(
        """
        <center>
            <p style="margin: 0 0 0.18rem; font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(122,110,136,0.72);">
                Ratio Overview
            </p>
            <h3 style="margin-bottom: 0.38rem; font-size: 1.36rem; font-weight: 800;">
                <span style='color: #66B3FF;'>缺陷</span>
                <span style='color: rgba(122,110,136,0.34); padding: 0 0.26rem;'>/</span>
                <span style='color: #FF9999;'>比例</span>
            </h3>
        </center>
        """,
        unsafe_allow_html=True,
    )
    dirty_count = defect_store.get_dirty_count()
    scratch_count = defect_store.get_scratch_count()
    total_defects = dirty_count + scratch_count
    if total_defects == 0:
        st.warning("暂无缺陷数据")
        return

    fig = go.Figure(
        data=[
            go.Pie(
                labels=["污渍 (dirty)", "划痕 (scratch)"],
                values=[dirty_count, scratch_count],
                hole=0.46,
                marker_colors=["#FF9999", "#66B3FF"],
                marker=dict(line=dict(color="rgba(255,255,255,0.92)", width=2)),
                textinfo="percent+label+value",
                textposition="inside",
                textfont=dict(size=14, color="white", weight="bold"),
                hovertemplate="%{label}<br>数量 %{value}<br>占比 %{percent}<extra></extra>",
            )
        ]
    )
    fig.add_annotation(
        text=f"总计<br>{total_defects}",
        font=dict(size=18, color="#5f5368", weight="bold"),
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        align="center",
    )
    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=False,
        plot_bgcolor="rgba(255,255,255,0.72)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#5f5368"),
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.96)",
            bordercolor="rgba(214,193,227,0.6)",
            font=dict(color="#5f5368"),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


def defect_summary(defect_store) -> None:
    st.markdown(
        """
        <center>
            <p style="margin: 0 0 0.18rem; font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(122,110,136,0.72);">
                Summary
            </p>
            <h3 style='color: #66B3FF; margin-bottom: 0.38rem; font-size: 1.36rem; font-weight: 800;'>缺陷统计摘要</h3>
        </center>
        """,
        unsafe_allow_html=True,
    )
    categories = ["总检测瓶盖数", "总污渍缺陷数", "总划痕缺陷数"]
    values = [defect_store.get_cap_count(), defect_store.get_dirty_count(), defect_store.get_scratch_count()]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=categories,
            y=values,
            marker_color=["#FFFF99", "#FF9999", "#99CCFF"],
            marker_line=dict(color="rgba(255,255,255,0.9)", width=1.4),
            text=values,
            textposition="auto",
            textfont=dict(size=14, color="#5f5368"),
            hovertemplate="%{x}<br>数量 %{y}<extra></extra>",
        )
    )
    fig.update_layout(
        margin=dict(t=20, b=30, l=20, r=20),
        height=300,
        plot_bgcolor="rgba(255,255,255,0.72)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#5f5368"),
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.96)",
            bordercolor="rgba(214,193,227,0.6)",
            font=dict(color="#5f5368"),
        ),
        yaxis=dict(showgrid=True, gridcolor="rgba(214,193,227,0.28)", showticklabels=False, zeroline=False),
        xaxis=dict(tickfont=dict(color="#5f5368", size=14), showgrid=False),
    )
    st.plotly_chart(fig, use_container_width=True)


def defect_record_summary(defect_store) -> None:
    st.markdown(
        """
        <center>
            <p style="margin: 0 0 0.18rem; font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(122,110,136,0.72);">
                Insight Report
            </p>
            <h3 style='color: #FF9999; margin-bottom: 0.38rem; font-size: 1.36rem; font-weight: 800;'>检测记录摘要</h3>
        </center>
        """,
        unsafe_allow_html=True,
    )

    summary = defect_store.get_summary()
    avg_confidence_text = f"{summary['avg_confidence']:.2%}" if summary["avg_confidence"] is not None else "暂无记录"
    defect_rate_text = f"{summary['defect_rate']:.2%}" if summary["cap_count"] else "暂无瓶盖记录"

    st.markdown(
        f"""
        <div class="metric-card metric-card--pink" style="min-height: auto;">
            <p class="metric-label metric-label--pink">时间范围</p>
            <p class="metric-note" style="margin-top: 0; font-size: 0.95rem;">{summary['time_range_text']}</p>
            <p class="metric-label metric-label--pink" style="margin-top: 1rem;">高峰时段</p>
            <p class="metric-note" style="margin-top: 0; font-size: 0.95rem;">{summary['busiest_hour_text']}</p>
            <p class="metric-label metric-label--pink" style="margin-top: 1rem;">主要缺陷</p>
            <p class="metric-note" style="margin-top: 0; font-size: 0.95rem;">{summary['top_defect_type_text']}</p>
            <p class="metric-label metric-label--pink" style="margin-top: 1rem;">平均置信度</p>
            <p class="metric-note" style="margin-top: 0; font-size: 0.95rem;">{avg_confidence_text}</p>
            <p class="metric-label metric-label--pink" style="margin-top: 1rem;">缺陷占比</p>
            <p class="metric-note" style="margin-top: 0; font-size: 0.95rem;">{defect_rate_text}</p>
            <p class="metric-label metric-label--pink" style="margin-top: 1rem;">批次摘要</p>
            <p class="metric-note" style="margin-top: 0; font-size: 0.95rem;">{summary['batch_summary_text']}</p>
            <p class="metric-label metric-label--pink" style="margin-top: 1rem;">班次摘要</p>
            <p class="metric-note" style="margin-top: 0; font-size: 0.95rem;">{summary['shift_summary_text']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(summary["recent_summary_text"])


def data_export(defect_store) -> None:
    st.markdown(
        """
        <center>
            <p style="margin: 0 0 0.18rem; font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(122,110,136,0.72);">
                Export Center
            </p>
            <h3 style="margin-bottom: 0.38rem; font-size: 1.36rem; font-weight: 800;">
                <span style='color: #66B3FF;'>数据</span>
                <span style='color: rgba(122,110,136,0.34); padding: 0 0.26rem;'>/</span>
                <span style='color: #FF9999;'>导出</span>
            </h3>
        </center>
        """,
        unsafe_allow_html=True,
    )
    timestamp = datetime.now().strftime(EXPORT_TIMESTAMP_FORMAT)
    export_df = defect_store.get_export_data()
    filtered_export_df = defect_store.get_export_data(st.session_state.filtered_data)
    current_image = (
        st.session_state.detection_results
        if st.session_state.detection_results is not None
        else st.session_state.captured_image
    )

    csv_data = export_df.to_csv(index=False).encode("utf-8-sig")
    filtered_csv_data = filtered_export_df.to_csv(index=False).encode("utf-8-sig")
    image_data = b""
    if current_image is not None:
        buffer = io.BytesIO()
        Image.fromarray(current_image).save(buffer, format="PNG")
        image_data = buffer.getvalue()

    st.download_button(
        label="📊 下载全部CSV",
        data=csv_data,
        file_name=f"ipdds_records_{timestamp}.csv",
        mime="text/csv",
        disabled=export_df.empty,
        use_container_width=True,
    )
    st.download_button(
        label="🖼️ 下载当前图像",
        data=image_data,
        file_name=f"ipdds_image_{timestamp}.png",
        mime="image/png",
        disabled=current_image is None,
        use_container_width=True,
    )
    st.download_button(
        label="📤 下载筛选结果",
        data=filtered_csv_data,
        file_name=f"ipdds_filtered_{timestamp}.csv",
        mime="text/csv",
        disabled=filtered_export_df.empty,
        use_container_width=True,
    )
    st.caption("导出文件名会自动附带时间戳，便于区分不同批次结果。")


def data_filter(defect_store) -> None:
    st.markdown(
        """
        <center>
            <p style="margin: 0 0 0.18rem; font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(122,110,136,0.72);">
                Filter View
            </p>
            <h3 style='color: #FF9999; margin-bottom: 0.38rem; font-size: 1.36rem; font-weight: 800;'>缺陷数据筛选</h3>
        </center>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("🔍 筛选选项", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<p style="color: #FF6666; font-size: 16px; margin-bottom: 0px;">选择缺陷类型</p>', unsafe_allow_html=True)
            defect_types = st.multiselect(
                "选择缺陷类型",
                options=DEFECT_TYPES,
                default=DEFECT_TYPES,
                label_visibility="collapsed",
            )
        with col2:
            today = datetime.today()
            st.markdown('<p style="color: #FF6666; font-size: 16px; margin-bottom: 0px;">开始日期</p>', unsafe_allow_html=True)
            start_date = st.date_input("开始日期", value=today - timedelta(days=7), label_visibility="collapsed")
            st.markdown('<p style="color: #FF6666; font-size: 16px; margin-bottom: 0px; margin-top: 10px;">结束日期</p>', unsafe_allow_html=True)
            end_date = st.date_input("结束日期", value=today, label_visibility="collapsed")

    if start_date > end_date:
        st.error("开始日期不能晚于结束日期，请调整筛选条件。")
        filtered = pd.DataFrame(columns=defect_store.defect_data.columns)
    else:
        start_dt = pd.Timestamp(datetime.combine(start_date, datetime.min.time()))
        end_dt = pd.Timestamp(datetime.combine(end_date, datetime.max.time()))
        filtered = defect_store.get_filtered_data(defect_types, start_dt, end_dt)

    if not filtered.empty:
        filtered = filtered.copy()
        filtered[COLUMN_TIME] = filtered[COLUMN_TIME].dt.strftime("%Y-%m-%d %H:%M:%S")

    st.session_state.filtered_data = filtered
    st.caption(f"当前筛选结果 {len(filtered)} 条")
    st.dataframe(filtered, height=200, use_container_width=True)

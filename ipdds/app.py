from __future__ import annotations

from datetime import datetime

import cv2
import streamlit as st
import torch
from PIL import Image

from .constants import APP_STYLE, EXPORT_TIMESTAMP_FORMAT, IMAGE_DIR, STREAMLIT_PAGE
from .data_store import DefectDataStore
from .inference import load_model, predict_single_image
from .ui_sections import (
    capture_component,
    data_export,
    data_filter,
    defect_record_summary,
    defect_pie_chart,
    defect_stats_component,
    defect_summary,
    dirty_time_chart,
    ensure_session_state,
    page_navigation,
    scratch_time_chart,
    video_stream_component,
)

torch.classes.__path__ = []


@st.cache_resource
def get_model():
    return load_model()


@st.cache_resource
def get_defect_store():
    return DefectDataStore()


def get_active_image():
    return st.session_state.detection_results if st.session_state.detection_results is not None else st.session_state.captured_image


def handle_actions(webrtc_ctx, button_action, defect_store: DefectDataStore) -> None:
    if button_action == "capture":
        if not webrtc_ctx or not getattr(webrtc_ctx, "video_transformer", None):
            st.warning("请先允许摄像头访问并等待视频预览加载完成。")
            return
        try:
            image = webrtc_ctx.video_transformer.frame
            if image is None:
                st.warning("当前还没有可用视频帧，请稍等片刻后再试。")
                return
            st.session_state.captured_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            st.session_state.detection_results = None
            st.rerun()
        except Exception as exc:
            st.error(f"拍摄失败: {exc}")
        return

    if button_action == "save" and st.session_state.captured_image is not None:
        try:
            IMAGE_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime(EXPORT_TIMESTAMP_FORMAT)
            image = get_active_image()
            filename_prefix = "detection" if st.session_state.detection_results is not None else "capture"
            filename = IMAGE_DIR / f"{filename_prefix}_{timestamp}.png"
            Image.fromarray(image).save(filename)
            st.success(f"图像已保存: {filename}")
            st.rerun()
        except Exception as exc:
            st.error(f"保存失败: {exc}")
        return

    if button_action == "detect" and st.session_state.captured_image is not None:
        try:
            model = get_model()
            annotated, _, records = predict_single_image(model, st.session_state.captured_image)
            st.session_state.detection_results = annotated
            if records:
                record_count = defect_store.add_defect_records([record.__dict__ for record in records])
                defect_store.save()
                st.success(f"检测完成，已记录 {record_count} 个识别结果。")
            else:
                st.info("未检测到缺陷")
            st.rerun()
        except Exception as exc:
            st.error(f"检测失败: {exc}")


def render_detect_page(defect_store: DefectDataStore) -> None:
    st.markdown('<div class="layout-band layout-band--hero">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1.2, 0.8, 1.2])
    with col1:
        webrtc_ctx = video_stream_component()
    with col2:
        defect_stats_component(defect_store)
    with col3:
        button_action = capture_component()
    st.markdown("</div>", unsafe_allow_html=True)

    handle_actions(webrtc_ctx, button_action, defect_store)


def render_stats_page(defect_store: DefectDataStore) -> None:
    st.markdown('<div class="layout-band layout-band--charts">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        scratch_time_chart(defect_store)
    with col2:
        defect_pie_chart(defect_store)
    with col3:
        dirty_time_chart(defect_store)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="layout-band layout-band--insights">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        defect_summary(defect_store)
    with col2:
        defect_record_summary(defect_store)
    with col3:
        data_export(defect_store)

    col1, col2 = st.columns([1.4, 1.6])
    with col1:
        data_filter(defect_store)
    with col2:
        st.empty()
    st.markdown("</div>", unsafe_allow_html=True)


def main_layout() -> None:
    ensure_session_state()
    defect_store = get_defect_store()

    active_page = page_navigation()
    st.divider()

    if active_page == "detect":
        render_detect_page(defect_store)
    else:
        render_stats_page(defect_store)


def run() -> None:
    st.set_page_config(**STREAMLIT_PAGE)
    st.markdown(APP_STYLE, unsafe_allow_html=True)
    try:
        main_layout()
    except Exception as exc:
        st.error(f"应用程序错误: {exc}")

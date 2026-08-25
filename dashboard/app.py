from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from time import monotonic
from typing import Any

import pandas as pd
import streamlit as st

from config import (
    DATA_PATH,
    HISTORY_DISPLAY_LIMIT,
    MODEL_PATH,
    SAMPLE_IMAGE_DIR,
    STREAM_INTERVAL_SECONDS,
)
from data_source import (
    CSVInspectionSource,
    MODEL_PROBABILITY_COLUMN,
    STREAM_ORDER_COLUMN,
    TIME_COLUMN,
    TYPE_COLUMN,
    discover_sample_images,
    image_for_position,
)
from explanation import FeatureSignalProvider, build_feature_signal_provider
from inference import TypeConditionedPredictor


st.set_page_config(
    page_title="AOI 수동 검사 대시보드",
    layout="wide",
)


def inject_factory_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stHeader"], [data-testid="stToolbar"], footer {
            display: none !important;
        }
        html, body, [data-testid="stAppViewContainer"], .stApp {
            background: #d8d8d8;
        }
        [data-testid="stMain"] {
            overflow: hidden;
        }
        [data-testid="stMainBlockContainer"] {
            max-width: 100%;
            height: 100vh;
            overflow: hidden;
            padding: 0;
        }
        [data-testid="stVerticalBlock"] {
            gap: 0.42rem;
        }
        [data-testid="stColumn"] > [data-testid="stVerticalBlock"] {
            gap: 0;
        }
        [data-testid="stVerticalBlock"][data-test-wrap="false"]
        [data-testid="stColumn"] > [data-testid="stVerticalBlock"] {
            gap: 0.2rem;
        }
        [data-testid="stVerticalBlock"]:has(
            > [data-testid="stElementContainer"] .factory-header
        ) {
            gap: 0;
        }
        [data-testid="stMarkdownContainer"]:has(.factory-header),
        [data-testid="stMarkdownContainer"]:has(.section-label),
        [data-testid="stMarkdownContainer"]:has(.inspection-record-bar),
        [data-testid="stMarkdownContainer"]:has(.inspection-metric) {
            margin-bottom: 0 !important;
        }
        [data-testid="stElementContainer"]:has(.factory-header)
        + [data-testid="stHorizontalBlock"] {
            gap: 0;
        }
        [data-testid="stElementContainer"]:has(.factory-header)
        + [data-testid="stHorizontalBlock"]
        > [data-testid="stColumn"]
        > [data-testid="stVerticalBlock"] {
            gap: 0;
        }
        [data-testid="stVerticalBlock"][data-test-wrap="false"] {
            gap: 0.4rem;
        }
        [data-testid="stHorizontalBlock"] {
            gap: 0;
        }
        [data-testid="stVerticalBlock"][data-test-wrap="false"]
        [data-testid="stHorizontalBlock"] {
            gap: 0.45rem;
        }
        .factory-header {
            box-sizing: border-box;
            height: 42px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #eeeeee;
            border: 1px solid #4c4c4c;
            color: #111111;
            padding: 0 0.7rem;
            font-family: Arial, sans-serif;
            font-weight: 700;
            line-height: 1;
            letter-spacing: 0.04em;
            white-space: nowrap;
            overflow: hidden;
        }
        .factory-header small {
            color: #333333;
            font-size: 0.76rem;
            font-weight: 600;
            letter-spacing: 0;
        }
        .factory-header-meta {
            display: flex;
            align-items: center;
            gap: 1.1rem;
            min-width: 0;
        }
        .factory-header-model {
            color: #5a5a5a !important;
            font-size: 0.68rem !important;
            font-weight: 500 !important;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .factory-status {
            border: 1px solid #555555;
            padding: 0.15rem 0.4rem;
            font-size: 0.65rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.04em !important;
        }
        .factory-status.status-running {
            background: #444444;
            color: #ffffff !important;
        }
        .factory-status.status-manual {
            background: #a93232;
            border-color: #7f1d1d;
            color: #ffffff !important;
        }
        .factory-status.status-finished {
            background: #c7c7c7;
            color: #222222 !important;
        }
        .section-label {
            box-sizing: border-box;
            height: 28px;
            display: flex;
            align-items: center;
            background: #d0d0d0;
            border: 0 solid #4c4c4c;
            border-right-width: 1px;
            color: #111111;
            font-family: Arial, sans-serif;
            font-size: 0.83rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            line-height: 1;
            padding: 0 0.5rem;
            white-space: nowrap;
            overflow: hidden;
        }
        [data-testid="stHorizontalBlock"]
        > [data-testid="stColumn"]:last-child .section-label {
            border-right-width: 0;
        }
        [data-testid="stVerticalBlock"][data-test-wrap="false"] {
            background: #eeeeee;
            border: 1px solid #4c4c4c !important;
            border-radius: 0 !important;
            box-shadow: none !important;
        }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #777777;
            border-radius: 0 !important;
            padding: 0.3rem 0.5rem;
        }
        [data-testid="stMetricLabel"] p {
            font-size: 0.75rem;
            font-weight: 700;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.45rem;
            font-weight: 800;
        }
        .inspection-metric {
            box-sizing: border-box;
            height: 70px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            background: #ffffff;
            border: 1px solid #777777;
            padding: 0.3rem 0.5rem;
            font-family: Arial, sans-serif;
            color: #111111;
            overflow: hidden;
        }
        .inspection-metric.probability-alert {
            background: #a93232;
            border-color: #7f1d1d;
            color: #ffffff;
        }
        .inspection-metric-label {
            font-size: 0.7rem;
            font-weight: 800;
            white-space: nowrap;
        }
        .inspection-metric-value {
            margin-top: 0.18rem;
            font-size: 1.3rem;
            font-weight: 800;
            white-space: nowrap;
        }
        .inspection-metric-limit {
            margin-top: 0.12rem;
            font-size: 0.62rem;
            font-weight: 700;
            white-space: nowrap;
        }
        [data-testid="stAlert"] {
            background: #d9d9d9 !important;
            border: 1px solid #777777 !important;
            border-radius: 0 !important;
            padding: 0.45rem 0.6rem;
        }
        [data-testid="stAlert"] * {
            color: #1a1a1a !important;
        }
        [data-testid="stAlertContainer"] {
            background: #d9d9d9 !important;
            border-radius: 0 !important;
        }
        [data-testid="stImage"] img {
            width: 100%;
            max-height: 215px;
            object-fit: contain;
            background: #121516;
            border: 1px solid #4e575c;
            border-radius: 0 !important;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child
        [data-testid="stImage"] img {
            max-height: 125px;
        }
        .st-key-previous-result-grid,
        .st-key-operator-history-grid {
            border-left-width: 0 !important;
        }
        .st-key-feature-signal-grid,
        .st-key-decision-grid,
        .st-key-operator-history-grid {
            border-top-width: 0 !important;
        }
        .inspection-record-bar {
            box-sizing: border-box;
            height: 26px;
            display: flex;
            align-items: center;
            background: #e3e3e3;
            border: 1px solid #777777;
            padding: 0 0.5rem;
            color: #363636;
            font-family: Arial, sans-serif;
            font-size: 0.72rem;
            font-weight: 700;
            line-height: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        [data-testid="stButton"] button {
            min-height: 40px;
            border: 1px solid #31383c;
            border-radius: 0 !important;
            box-shadow: none !important;
            font-weight: 800;
        }
        [data-testid="stButton"] button[kind="primary"] {
            background: #b52a2a !important;
            border-color: #7f1d1d !important;
            color: #ffffff !important;
        }
        [data-testid="stButton"] button[kind="primary"]:hover {
            background: #982222 !important;
        }
        [data-testid="stButton"] button[kind="secondary"] {
            background: #f7f7f7 !important;
            color: #111111 !important;
        }
        .stream-auto-decision {
            box-sizing: border-box;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #d5d5d5;
            border: 1px solid #555555;
            padding: 0 0.65rem;
            color: #111111;
            font-family: Arial, sans-serif;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.02em;
        }
        [data-testid="stMarkdownContainer"]:has(.feature-signal-board) {
            margin-bottom: 0 !important;
        }
        .feature-signal-board {
            font-family: Arial, sans-serif;
        }
        .feature-signal-note {
            box-sizing: border-box;
            height: 34px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #d9d9d9;
            border: 1px solid #696969;
            border-bottom: 0;
            padding: 0 0.55rem;
            color: #1a1a1a;
            font-size: 0.76rem;
            font-weight: 800;
        }
        .feature-signal-note span:last-child {
            border: 1px solid #696969;
            background: #f4f4f4;
            padding: 0.12rem 0.35rem;
            font-size: 0.68rem;
            letter-spacing: 0.04em;
        }
        .feature-signal-cells {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            grid-template-rows: repeat(2, 109px);
            border-top: 1px solid #696969;
            border-left: 1px solid #696969;
        }
        .feature-signal-card {
            box-sizing: border-box;
            min-width: 0;
            display: flex;
            flex-direction: column;
            justify-content: center;
            border-right: 1px solid #696969;
            border-bottom: 1px solid #696969;
            padding: 0.45rem 0.55rem;
            line-height: 1.15;
            overflow: hidden;
        }
        .feature-signal-card.signal-not-matched {
            background: #f4f4f4;
            color: #111111;
        }
        .feature-signal-card.signal-missing {
            background: #5d5d5d;
            color: #ffffff;
        }
        .feature-signal-card.signal-matched {
            background: #a86f10;
            color: #ffffff;
        }
        .feature-signal-name {
            font-size: 0.82rem;
            font-weight: 800;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .feature-signal-meta {
            margin-top: 0.18rem;
            font-size: 0.64rem;
            font-weight: 700;
            white-space: nowrap;
        }
        .feature-signal-value {
            margin-top: 0.18rem;
            font-size: 1.05rem;
            font-weight: 800;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .feature-signal-state {
            margin-top: 0.25rem;
            font-size: 0.7rem;
            font-weight: 700;
            white-space: nowrap;
        }
        .feature-signal-empty {
            grid-column: 1 / -1;
            grid-row: 1 / -1;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #cdcdcd;
            border-right: 1px solid #696969;
            border-bottom: 1px solid #696969;
            color: #2f2f2f;
            font-size: 0.86rem;
            font-weight: 800;
            letter-spacing: 0.02em;
        }
        .decision-strip,
        .history-row {
            border: 1px solid #696969;
            border-radius: 0;
            padding: 0.35rem 0.45rem;
        }
        .decision-strip {
            box-sizing: border-box;
            height: 64px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 0.12rem;
            line-height: 1.15;
            overflow: hidden;
        }
        .decision-title {
            font-size: 0.88rem;
            font-weight: 800;
            white-space: nowrap;
        }
        .decision-detail {
            font-size: 0.78rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .decision-normal,
        .history-normal {
            background: #f5f5f5;
            color: #111111;
        }
        .history-model-normal {
            background: #d1d1d1;
            color: #111111;
        }
        .decision-defect,
        .history-defect {
            background: #555555;
            color: #ffffff;
        }
        .history-row strong {
            font-weight: 800;
        }
        hr {
            margin: 0.35rem 0 !important;
            border-color: #a6adb1 !important;
        }
        p {
            margin-bottom: 0.15rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner="모델과 Test 데이터를 불러오는 중입니다...")
def load_dashboard_resources(
    csv_path: str,
    model_path: str,
) -> tuple[TypeConditionedPredictor, CSVInspectionSource]:
    predictor = TypeConditionedPredictor.from_file(model_path)
    source = CSVInspectionSource.from_csv(
        csv_path,
        predictor.validation_end_time,
        deduplicate_rows=predictor.deduplicate_rows,
    )
    return predictor, source


def load_image_paths(image_dir: str) -> list[Path]:
    return discover_sample_images(image_dir)


def initialize_session(source_signature: str) -> None:
    if st.session_state.get("source_signature") == source_signature:
        return

    st.session_state.source_signature = source_signature
    st.session_state.stream_cursor = 0
    st.session_state.manual_count = 0
    st.session_state.stream_status = "running"
    st.session_state.current_stream_view = None
    st.session_state.next_prediction_at = 0.0
    st.session_state.previous_item = None
    st.session_state.decision_history = []


def reset_demo() -> None:
    st.session_state.stream_cursor = 0
    st.session_state.manual_count = 0
    st.session_state.stream_status = "running"
    st.session_state.current_stream_view = None
    st.session_state.next_prediction_at = 0.0
    st.session_state.previous_item = None
    st.session_state.decision_history = []


def format_probability(probability: float) -> str:
    percentage = probability * 100
    if percentage >= 10:
        return f"{percentage:.1f}%"
    if percentage >= 1:
        return f"{percentage:.2f}%"
    if percentage >= 0.1:
        return f"{percentage:.3f}%"
    return f"{percentage:.4f}%"


def format_value(value: Any) -> str:
    if value is None or pd.isna(value):
        return "값 없음"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def render_image(image_path: str | Path | None) -> None:
    if image_path:
        st.image(str(image_path), width="stretch")
    else:
        st.info(
            "샘플 이미지 대기 중\n\n"
            "`dashboard/assets/sample_images/`에 "
            "`inspection_001.jpg`부터 이미지를 넣어주세요."
        )


def build_current_view(
    row: dict[str, Any],
    position: int,
    predictor: TypeConditionedPredictor,
    signal_provider: FeatureSignalProvider,
    sample_images: list[Path],
) -> dict[str, Any]:
    inspection_type = int(row[TYPE_COLUMN])
    if MODEL_PROBABILITY_COLUMN in row:
        probability = float(row[MODEL_PROBABILITY_COLUMN])
    else:
        probability = predictor.predict_defect_probability(row)
    feature_signals = signal_provider.get_signals(
        row,
        inspection_type,
        count=6,
    )
    image_path = image_for_position(sample_images, position)

    return {
        "record_id": row["record_id"],
        "timestamp": row[TIME_COLUMN],
        "inspection_type": inspection_type,
        "defect_probability": probability,
        "decision_threshold": predictor.decision_threshold,
        "feature_signals": feature_signals,
        STREAM_ORDER_COLUMN: int(row[STREAM_ORDER_COLUMN]),
        "image_path": str(image_path) if image_path else None,
        # Test 정답은 작업자 판정 전에 화면에 표시하지 않는다.
        "ground_truth": int(row["class"]),
    }


def record_model_normal(current_view: dict[str, Any]) -> None:
    st.session_state.decision_history.insert(
        0,
        {
            "record_id": current_view["record_id"],
            TIME_COLUMN: current_view[TIME_COLUMN],
            "inspection_type": int(current_view[TYPE_COLUMN]),
            "defect_probability": float(
                current_view["defect_probability"]
            ),
            STREAM_ORDER_COLUMN: int(
                current_view[STREAM_ORDER_COLUMN]
            ),
            "history_source": "model",
        },
    )


def advance_stream_tick(
    source: CSVInspectionSource,
    predictor: TypeConditionedPredictor,
    signal_provider: FeatureSignalProvider,
    sample_images: list[Path],
) -> None:
    """0.3초 tick마다 이전 정상 건을 기록하고 다음 한 행만 추론한다."""
    if st.session_state.stream_status != "running":
        return
    if monotonic() < float(st.session_state.next_prediction_at):
        return

    current_view = st.session_state.current_stream_view
    if (
        current_view is not None
        and current_view.get("model_decision") == "normal"
    ):
        record_model_normal(current_view)
        st.session_state.stream_cursor += 1

    if st.session_state.stream_cursor >= len(source):
        st.session_state.current_stream_view = None
        st.session_state.stream_status = "finished"
        return

    row = source.get_item(int(st.session_state.stream_cursor))
    if row is None:
        st.session_state.current_stream_view = None
        st.session_state.stream_status = "finished"
        return

    probability = predictor.predict_defect_probability(row)
    row[MODEL_PROBABILITY_COLUMN] = probability
    current_view = build_current_view(
        row,
        int(st.session_state.stream_cursor),
        predictor,
        signal_provider,
        sample_images,
    )
    is_manual_review = probability >= predictor.decision_threshold
    current_view["model_decision"] = (
        "defect" if is_manual_review else "normal"
    )
    st.session_state.current_stream_view = current_view
    st.session_state.next_prediction_at = (
        monotonic() + STREAM_INTERVAL_SECONDS
    )
    if is_manual_review:
        st.session_state.stream_status = "manual_review"


def submit_decision(current_view: dict[str, Any], decision: str) -> None:
    decided_item = {
        **current_view,
        "operator_decision": decision,
        "decided_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    st.session_state.previous_item = decided_item
    st.session_state.decision_history.insert(0, decided_item)
    st.session_state.stream_cursor += 1
    st.session_state.manual_count += 1
    st.session_state.current_stream_view = None
    st.session_state.stream_status = "running"
    # 작업자 입력은 자동 tick과 별개의 이벤트다. 다음 행을 즉시 준비해
    # 판정 완료 화면이 0.3초 동안 남는 현상을 방지한다.
    st.session_state.next_prediction_at = 0.0


def render_current_panel(
    current_view: dict[str, Any] | None,
    stream_position: int,
    stream_total: int,
    manual_number: int,
) -> None:
    if current_view is None:
        st.markdown(
            '<div class="section-label">CURRENT INSPECTION / 현재 검사</div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True, key="current-inspection-grid"):
            st.success("Test 스트림의 모든 검사 건을 처리했습니다.")
            if stream_total > 0 and st.button(
                "데모 처음부터 다시 시작",
                width="stretch",
            ):
                reset_demo()
                st.rerun()
        return

    timestamp = current_view["timestamp"]
    st.markdown(
        '<div class="section-label">CURRENT INSPECTION / 현재 검사</div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True, key="current-inspection-grid"):
        is_manual_review = (
            current_view.get("model_decision") == "defect"
        )
        stream_mode = (
            f"MANUAL REVIEW #{manual_number:,}"
            if is_manual_review
            else "MODEL AUTO CHECK"
        )
        st.markdown(
            '<div class="inspection-record-bar">'
            f'STREAM {stream_position + 1:,} / {stream_total:,} &nbsp;|&nbsp; '
            f'{stream_mode} &nbsp;|&nbsp; '
            f'RECORD #{current_view["record_id"]} &nbsp;|&nbsp; '
            f'{escape(str(timestamp))}'
            '</div>',
            unsafe_allow_html=True,
        )
        image_column, info_column = st.columns([1.7, 1], gap="medium")
        with image_column:
            render_image(current_view["image_path"])

        with info_column:
            metric_type, metric_probability = st.columns(2, gap="small")
            with metric_type:
                st.markdown(
                    '<div class="inspection-metric">'
                    '<div class="inspection-metric-label">INSPECTION TYPE</div>'
                    '<div class="inspection-metric-value">TYPE '
                    f'{current_view["inspection_type"]}</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
            with metric_probability:
                probability_alert = (
                    current_view["defect_probability"]
                    >= current_view["decision_threshold"]
                )
                probability_class = (
                    " probability-alert" if probability_alert else ""
                )
                st.markdown(
                    f'<div class="inspection-metric{probability_class}">'
                    '<div class="inspection-metric-label">DEFECT PROBABILITY</div>'
                    '<div class="inspection-metric-value">'
                    f'{format_probability(current_view["defect_probability"])}</div>'
                    '<div class="inspection-metric-limit">GLOBAL LIMIT '
                    f'{format_probability(current_view["decision_threshold"])}</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            feature_signals = current_view["feature_signals"]
            if feature_signals:
                top_signal = feature_signals[0]
                st.info(
                    "**GLOBAL SHAP TOP FEATURE · STATIC**  \n"
                    f"{top_signal.feature}  |  "
                    f"|SHAP| `{top_signal.contribution:.4f}`  \n"
                    f"현재 값 `{format_value(top_signal.value)}`  |  "
                    f"대표 조건 `{top_signal.condition}`"
                )
            else:
                st.info(
                    "**GLOBAL SHAP · STATIC**  \n"
                    "TYPE 4  |  유효한 중요 feature 없음  \n"
                    "전체 feature의 |SHAP| = 0"
                )

    feature_signals = current_view["feature_signals"]
    st.markdown(
        '<div class="section-label">GLOBAL SHAP / TYPE별 정적 중요 FEATURE</div>',
        unsafe_allow_html=True,
    )
    with st.container(
        height=270,
        border=True,
        key="feature-signal-grid",
    ):
        cards = []
        for signal in feature_signals:
            cards.append(
                f'<div class="feature-signal-card signal-{signal.level}">'
                f'<div class="feature-signal-name">{escape(signal.feature)}</div>'
                f'<div class="feature-signal-meta">GLOBAL #{signal.rank} · '
                f'|SHAP| {signal.contribution:.4f}</div>'
                f'<div class="feature-signal-value">'
                f'{escape(format_value(signal.value))}</div>'
                f'<div class="feature-signal-state">'
                f'{escape(signal.label)}</div>'
                f'</div>'
            )

        if not cards:
            cards.append(
                '<div class="feature-signal-empty">'
                'TYPE 4 · 유효한 GLOBAL SHAP 신호 없음'
                '</div>'
            )

        st.markdown(
            '<div class="feature-signal-board">'
            '<div class="feature-signal-note">'
            '<span>Dongjin 027 · 전역 |SHAP| 상위 6개 · 현재 값 / 대표 split</span>'
            '<span>STATIC</span>'
            '</div>'
            '<div class="feature-signal-cells">'
            f'{"".join(cards)}'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with st.container(border=True, key="decision-grid"):
        if is_manual_review:
            normal_column, defect_column = st.columns(2, gap="medium")
            with normal_column:
                st.button(
                    "NORMAL / 정상 판정",
                    width="stretch",
                    key=f"normal-{current_view['record_id']}",
                    on_click=submit_decision,
                    args=(current_view, "normal"),
                )
            with defect_column:
                st.button(
                    "DEFECT / 실제 불량 판정",
                    type="primary",
                    width="stretch",
                    key=f"defect-{current_view['record_id']}",
                    on_click=submit_decision,
                    args=(current_view, "defect"),
                )
        else:
            st.markdown(
                '<div class="stream-auto-decision">'
                '<span>MODEL NORMAL / 자동 정상 판정</span>'
                '<span>NEXT INSPECTION · 0.3 SEC</span>'
                '</div>',
                unsafe_allow_html=True,
            )


def render_previous_panel(previous_item: dict[str, Any] | None) -> None:
    st.markdown(
        '<div class="section-label">LAST RESULT / 직전 검사 결과</div>',
        unsafe_allow_html=True,
    )
    with st.container(
        height=225,
        border=True,
        key="previous-result-grid",
    ):
        if previous_item is None:
            st.caption("아직 완료된 판정이 없습니다.")
            return

        render_image(previous_item["image_path"])
        decision_label = (
            "실제 불량"
            if previous_item["operator_decision"] == "defect"
            else "정상"
        )
        decision_class = (
            "decision-defect"
            if previous_item["operator_decision"] == "defect"
            else "decision-normal"
        )
        previous_signals = previous_item["feature_signals"]
        shap_summary = (
            f"Global SHAP {previous_signals[0].feature}"
            if previous_signals
            else "Global SHAP 유효 신호 없음"
        )
        st.markdown(
            f'<div class="decision-strip {decision_class}">'
            f'<div class="decision-title">TYPE '
            f'{previous_item["inspection_type"]} | {decision_label}</div>'
            f'<div class="decision-detail">불량 확률 '
            f'{format_probability(previous_item["defect_probability"])}</div>'
            f'<div class="decision-detail">{escape(shap_summary)} · STATIC</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_history_panel(
    history: list[dict[str, Any]],
    total_count: int,
) -> None:
    st.markdown(
        f'<div class="section-label">INSPECTION LOG / 판정 히스토리 '
        f'· {total_count:,}건</div>',
        unsafe_allow_html=True,
    )

    with st.container(
        height=397,
        border=True,
        key="operator-history-grid",
    ):
        if not history:
            st.caption("검사 처리가 시작되면 이곳에 기록이 쌓입니다.")
            return

        for index, item in enumerate(history):
            is_model_decision = item.get("history_source") == "model"
            if is_model_decision:
                decision_label = "모델판정 정상"
                history_class = "history-model-normal"
                decided_time = pd.Timestamp(item[TIME_COLUMN]).strftime(
                    "%H:%M:%S"
                )
            else:
                is_defect = item["operator_decision"] == "defect"
                decision_label = (
                    "작업자판정 실제 불량" if is_defect else "작업자판정 정상"
                )
                history_class = (
                    "history-defect" if is_defect else "history-normal"
                )
                decided_time = pd.Timestamp(item["decided_at"]).strftime(
                    "%H:%M:%S"
                )

            st.markdown(
                f'<div class="history-row {history_class}">'
                f'<strong>{decision_label} | Type {item["inspection_type"]}</strong><br>'
                f'{decided_time} | Record #{item["record_id"]}<br>'
                f'모델 불량 확률 {format_probability(item["defect_probability"])}'
                f'</div>',
                unsafe_allow_html=True,
            )
            if index < len(history) - 1:
                st.divider()


@st.fragment(run_every=STREAM_INTERVAL_SECONDS)
def render_stream_dashboard(
    predictor: TypeConditionedPredictor,
    source: CSVInspectionSource,
    signal_provider: FeatureSignalProvider,
    sample_images: list[Path],
) -> None:
    try:
        advance_stream_tick(
            source,
            predictor,
            signal_provider,
            sample_images,
        )
    except Exception as error:
        st.error(f"실시간 모델 판정을 처리하지 못했습니다: {error}")
        st.stop()

    current_view = st.session_state.current_stream_view
    stream_status = str(st.session_state.stream_status)
    stream_position = int(st.session_state.stream_cursor)
    manual_number = int(st.session_state.manual_count) + (
        1 if stream_status == "manual_review" else 0
    )
    stream_display = min(stream_position + 1, len(source))
    status_label, status_class = {
        "running": ("RUNNING", "status-running"),
        "manual_review": ("MANUAL REVIEW", "status-manual"),
        "finished": ("FINISHED", "status-finished"),
    }.get(stream_status, ("UNKNOWN", "status-finished"))

    st.markdown(
        f"""
        <div class="factory-header">
            <span>AOI MANUAL INSPECTION</span>
            <div class="factory-header-meta">
                <small class="factory-header-model">MODEL · {escape(predictor.experiment_id)}</small>
                <small class="factory-status {status_class}">{status_label}</small>
                <small>STREAM {stream_display:,} / {len(source):,} · MANUAL {manual_number:,}</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    main_column, side_column = st.columns([3, 1.15], gap="large")
    with main_column:
        render_current_panel(
            current_view,
            stream_position,
            len(source),
            manual_number,
        )
    with side_column:
        render_previous_panel(st.session_state.previous_item)
        render_history_panel(
            st.session_state.decision_history[:HISTORY_DISPLAY_LIMIT],
            len(st.session_state.decision_history),
        )


def main() -> None:
    inject_factory_styles()

    try:
        predictor, source = load_dashboard_resources(
            str(DATA_PATH),
            str(MODEL_PATH),
        )
        signal_provider = build_feature_signal_provider()
        sample_images = load_image_paths(str(SAMPLE_IMAGE_DIR))
    except Exception as error:
        st.error(f"대시보드를 초기화하지 못했습니다: {error}")
        st.stop()

    source_signature = (
        f"{DATA_PATH}:{MODEL_PATH}:{predictor.validation_end_time}:"
        f"{predictor.deduplicate_rows}:{predictor.decision_threshold}:"
        f"timed-stream:{STREAM_INTERVAL_SECONDS}:{len(source)}"
    )
    initialize_session(source_signature)
    render_stream_dashboard(
        predictor,
        source,
        signal_provider,
        sample_images,
    )


if __name__ == "__main__":
    main()

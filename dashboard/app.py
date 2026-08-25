from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from config import (
    DATA_PATH,
    HISTORY_DISPLAY_LIMIT,
    MOCK_CAUSE_FEATURE_BY_TYPE,
    MODEL_PATH,
    SAMPLE_IMAGE_DIR,
    TREND_WINDOW_SIZE,
)
from data_source import (
    CSVInspectionSource,
    STREAM_ORDER_COLUMN,
    TIME_COLUMN,
    TYPE_COLUMN,
    discover_sample_images,
    image_for_position,
)
from inference import TypeConditionedPredictor, get_mock_cause_feature


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
        [data-testid="stMarkdownContainer"]:has(.section-label) {
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
        .st-key-feature-trend-grid,
        .st-key-decision-grid,
        .st-key-operator-history-grid {
            border-top-width: 0 !important;
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
        [data-testid="stSelectbox"] [data-baseweb="select"],
        [data-testid="stSelectbox"] [data-baseweb="select"] * {
            border-radius: 0 !important;
        }
        [data-testid="stSelectbox"] [data-baseweb="select"] > div {
            min-height: 34px;
            background: #ffffff;
            border-color: #515b60;
        }
        [data-testid="stSelectbox"] label p {
            font-size: 0.75rem;
            font-weight: 800;
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


@st.cache_resource(show_spinner="모델을 불러오는 중입니다...")
def load_predictor(model_path: str) -> TypeConditionedPredictor:
    return TypeConditionedPredictor.from_file(model_path)


@st.cache_data(show_spinner="Test 검사 데이터를 준비하는 중입니다...")
def load_source(
    csv_path: str,
    test_start_exclusive: str,
) -> CSVInspectionSource:
    return CSVInspectionSource.from_csv(csv_path, test_start_exclusive)


def load_image_paths(image_dir: str) -> list[Path]:
    return discover_sample_images(image_dir)


def initialize_session(source_signature: str) -> None:
    if st.session_state.get("source_signature") == source_signature:
        return

    st.session_state.source_signature = source_signature
    st.session_state.cursor = 0
    st.session_state.previous_item = None
    st.session_state.decision_history = []


def reset_demo() -> None:
    st.session_state.cursor = 0
    st.session_state.previous_item = None
    st.session_state.decision_history = []


def format_probability(probability: float) -> str:
    return f"{probability * 100:.1f}%"


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
    sample_images: list[Path],
) -> dict[str, Any]:
    inspection_type = int(row[TYPE_COLUMN])
    probability = predictor.predict_defect_probability(row)
    important_features = predictor.important_features(inspection_type, count=2)
    feature_options = predictor.feature_columns(inspection_type)
    cause = get_mock_cause_feature(row, MOCK_CAUSE_FEATURE_BY_TYPE)
    image_path = image_for_position(sample_images, position)

    return {
        "record_id": row["record_id"],
        "timestamp": row[TIME_COLUMN],
        "inspection_type": inspection_type,
        "defect_probability": probability,
        "cause": cause,
        "important_features": important_features,
        "feature_options": feature_options,
        STREAM_ORDER_COLUMN: int(row[STREAM_ORDER_COLUMN]),
        "image_path": str(image_path) if image_path else None,
        # Test 정답은 작업자 판정 전에 화면에 표시하지 않는다.
        "ground_truth": int(row["class"]),
    }


def submit_decision(current_view: dict[str, Any], decision: str) -> None:
    decided_item = {
        **current_view,
        "operator_decision": decision,
        "decided_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    st.session_state.previous_item = decided_item
    st.session_state.decision_history.insert(0, decided_item)
    st.session_state.cursor += 1
    st.rerun()


def render_current_panel(
    current_view: dict[str, Any] | None,
    position: int,
    total: int,
    source: CSVInspectionSource,
) -> None:
    if current_view is None:
        st.markdown(
            '<div class="section-label">CURRENT INSPECTION / 현재 검사</div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True, key="current-inspection-grid"):
            st.success("Test 큐의 모든 검사 건을 판정했습니다.")
            if st.button("데모 처음부터 다시 시작", width="stretch"):
                reset_demo()
                st.rerun()
        return

    timestamp = current_view["timestamp"]
    st.markdown(
        '<div class="section-label">CURRENT INSPECTION / 현재 검사</div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True, key="current-inspection-grid"):
        st.caption(
            f"QUEUE {position + 1:,} / {total:,}  |  "
            f"RECORD #{current_view['record_id']}  |  {timestamp}"
        )
        image_column, info_column = st.columns([1.7, 1], gap="medium")
        with image_column:
            render_image(current_view["image_path"])

        with info_column:
            metric_type, metric_probability = st.columns(2, gap="small")
            with metric_type:
                st.metric(
                    "INSPECTION TYPE",
                    f"TYPE {current_view['inspection_type']}",
                )
            with metric_probability:
                st.metric(
                    "DEFECT PROBABILITY",
                    format_probability(current_view["defect_probability"]),
                )

            cause = current_view["cause"]
            st.info(
                f"**CAUSE FEATURE · DEMO**  \n"
                f"{cause['feature']}  |  현재 값 "
                f"`{format_value(cause['value'])}`  \n"
                "SHAP 연동 준비 중"
            )

    st.markdown(
        '<div class="section-label">FEATURE TREND / 공정 로그</div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True, key="feature-trend-grid"):
        chart_columns = st.columns(2, gap="medium")
        feature_options = current_view["feature_options"]
        inspection_type = current_view["inspection_type"]

        for chart_index, chart_column in enumerate(chart_columns):
            default_feature = current_view["important_features"][chart_index]
            default_index = feature_options.index(default_feature)
            with chart_column:
                selected_feature = st.selectbox(
                    f"TREND {chart_index + 1} FEATURE",
                    options=feature_options,
                    index=default_index,
                    key=f"trend-{chart_index + 1}-type-{inspection_type}",
                )
                trend = source.get_feature_trend(
                    current_view,
                    selected_feature,
                    window_size=TREND_WINDOW_SIZE,
                )
                if trend.empty:
                    st.warning("표시할 과거 로그가 없습니다.")
                else:
                    current_value = format_value(
                        trend.iloc[-1][selected_feature]
                    )
                    chart_data = trend.set_index(TIME_COLUMN)[[selected_feature]]
                    st.line_chart(
                        chart_data,
                        color="#404040",
                        height=173,
                    )
                    st.caption(f"CURRENT VALUE  {current_value}")

    with st.container(border=True, key="decision-grid"):
        normal_column, defect_column = st.columns(2, gap="medium")
        with normal_column:
            normal_clicked = st.button(
                "NORMAL / 정상 판정",
                width="stretch",
                key=f"normal-{current_view['record_id']}",
            )
        with defect_column:
            defect_clicked = st.button(
                "DEFECT / 실제 불량 판정",
                type="primary",
                width="stretch",
                key=f"defect-{current_view['record_id']}",
            )

    if normal_clicked:
        submit_decision(current_view, "normal")
    if defect_clicked:
        submit_decision(current_view, "defect")


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
        st.markdown(
            f'<div class="decision-strip {decision_class}">'
            f'<div class="decision-title">TYPE '
            f'{previous_item["inspection_type"]} | {decision_label}</div>'
            f'<div class="decision-detail">불량 확률 '
            f'{format_probability(previous_item["defect_probability"])}</div>'
            f'<div class="decision-detail">원인 '
            f'{previous_item["cause"]["feature"]} · DEMO</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_history_panel(history: list[dict[str, Any]]) -> None:
    st.markdown(
        f'<div class="section-label">OPERATOR LOG / 판정 히스토리 '
        f'· {len(history):,}건</div>',
        unsafe_allow_html=True,
    )

    with st.container(
        height=397,
        border=True,
        key="operator-history-grid",
    ):
        if not history:
            st.caption("판정 버튼을 누르면 이곳에 기록이 쌓입니다.")
            return

        for index, item in enumerate(history[:HISTORY_DISPLAY_LIMIT]):
            is_defect = item["operator_decision"] == "defect"
            decision_label = "실제 불량" if is_defect else "정상"
            history_class = "history-defect" if is_defect else "history-normal"
            decided_time = pd.Timestamp(item["decided_at"]).strftime("%H:%M:%S")

            st.markdown(
                f'<div class="history-row {history_class}">'
                f'<strong>{decision_label} | Type {item["inspection_type"]}</strong><br>'
                f'{decided_time} | Record #{item["record_id"]}<br>'
                f'모델 불량 확률 {format_probability(item["defect_probability"])}'
                f'</div>',
                unsafe_allow_html=True,
            )
            if index < min(len(history), HISTORY_DISPLAY_LIMIT) - 1:
                st.divider()


def main() -> None:
    inject_factory_styles()

    try:
        predictor = load_predictor(str(MODEL_PATH))
        source = load_source(str(DATA_PATH), predictor.validation_end_time)
        sample_images = load_image_paths(str(SAMPLE_IMAGE_DIR))
    except Exception as error:
        st.error(f"대시보드를 초기화하지 못했습니다: {error}")
        st.stop()

    source_signature = (
        f"{DATA_PATH}:{MODEL_PATH}:{predictor.validation_end_time}:{len(source)}"
    )
    initialize_session(source_signature)

    position = int(st.session_state.cursor)
    row = source.get_item(position)

    try:
        current_view = (
            build_current_view(
                row,
                position,
                predictor,
                sample_images,
            )
            if row is not None
            else None
        )
    except Exception as error:
        st.error(f"현재 검사 건을 준비하지 못했습니다: {error}")
        st.stop()

    st.markdown(
        f"""
        <div class="factory-header">
            <span>AOI MANUAL INSPECTION</span>
            <small>TEST QUEUE {min(position + 1, len(source)):,} / {len(source):,}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

    main_column, side_column = st.columns([3, 1.15], gap="large")
    with main_column:
        render_current_panel(current_view, position, len(source), source)
    with side_column:
        render_previous_panel(st.session_state.previous_item)
        render_history_panel(st.session_state.decision_history)


if __name__ == "__main__":
    main()

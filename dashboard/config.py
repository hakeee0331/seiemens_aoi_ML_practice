from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 대시보드의 유일한 화면 기준이다. 모바일·반응형 레이아웃은 지원하지 않는다.
TARGET_VIEWPORT_WIDTH = 1280
TARGET_VIEWPORT_HEIGHT = 720

DATA_PATH = PROJECT_ROOT / "data" / "raw" / "dataset.csv"
MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "0824_kimjaehak_006_type_conditioned_baseline.pkl"
)
SAMPLE_IMAGE_DIR = Path(__file__).resolve().parent / "assets" / "sample_images"

HISTORY_DISPLAY_LIMIT = 50

# SHAP 연동 전 화면 구성을 위한 명시적인 데모 값이다.
MOCK_CAUSE_FEATURE_BY_TYPE = {
    0: "inspection_feat24",
    1: "inspection_feat48",
    2: "inspection_feat96",
    3: "inspection_feat95",
    4: "inspection_feat34",
}

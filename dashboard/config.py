from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 대시보드의 유일한 화면 기준이다. 모바일·반응형 레이아웃은 지원하지 않는다.
TARGET_VIEWPORT_WIDTH = 1280
TARGET_VIEWPORT_HEIGHT = 720
STREAM_INTERVAL_SECONDS = 0.3

DATA_PATH = PROJECT_ROOT / "data" / "raw" / "dataset.csv"
MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "0825_peace_005_type_expert_fold_ensemble.pkl"
)
SAMPLE_IMAGE_DIR = Path(__file__).resolve().parent / "assets" / "sample_images"

HISTORY_DISPLAY_LIMIT = 50

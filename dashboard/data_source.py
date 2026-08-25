from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import pandas as pd


RECORD_ID = "record_id"
TIME_COLUMN = "timestamp"
TARGET_COLUMN = "class"
TYPE_COLUMN = "inspection_type"
STREAM_ORDER_COLUMN = "_stream_order"
MODEL_PROBABILITY_COLUMN = "_model_defect_probability"

SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


class CSVInspectionSource:
    """시간순 Test 행을 하나씩 제공하고 과거 feature 로그를 조회한다."""

    def __init__(
        self,
        all_rows: pd.DataFrame,
        test_rows: pd.DataFrame,
        test_start_exclusive: pd.Timestamp,
    ) -> None:
        self._all_rows = all_rows
        self._test_rows = test_rows
        self.test_start_exclusive = test_start_exclusive

    @classmethod
    def from_csv(
        cls,
        csv_path: str | Path,
        test_start_exclusive: str | pd.Timestamp,
        deduplicate_rows: bool = True,
    ) -> "CSVInspectionSource":
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")

        raw = pd.read_csv(csv_path, low_memory=False)
        first_column = raw.columns[0]
        if first_column.startswith("Unnamed:"):
            raw = raw.rename(columns={first_column: RECORD_ID})
        elif first_column != RECORD_ID:
            raise ValueError(f"예상하지 못한 첫 번째 컬럼입니다: {first_column}")

        required_columns = {
            RECORD_ID,
            TIME_COLUMN,
            TARGET_COLUMN,
            TYPE_COLUMN,
        }
        missing_columns = required_columns - set(raw.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"CSV 필수 컬럼이 누락되었습니다: {missing}")

        if not raw[RECORD_ID].is_unique:
            raise ValueError("record_id는 고유해야 합니다.")

        if deduplicate_rows:
            # 구형 baseline artifact의 학습 전처리와 동일한 중복 제거 정책이다.
            dedup_columns = [
                column
                for column in raw.columns
                if column not in {RECORD_ID, TIME_COLUMN}
            ]
            clean = raw.drop_duplicates(
                subset=dedup_columns,
                keep="first",
            ).copy()
        else:
            clean = raw.copy()

        clean[TIME_COLUMN] = pd.to_datetime(
            clean[TIME_COLUMN],
            errors="raise",
            utc=True,
        )
        clean = clean.sort_values(
            [TIME_COLUMN, RECORD_ID],
            kind="stable",
        ).reset_index(drop=True)
        clean[STREAM_ORDER_COLUMN] = range(len(clean))

        boundary = pd.Timestamp(test_start_exclusive)
        if boundary.tzinfo is None:
            boundary = boundary.tz_localize("UTC")
        else:
            boundary = boundary.tz_convert("UTC")

        test_rows = clean.loc[clean[TIME_COLUMN] > boundary].reset_index(drop=True)
        if test_rows.empty:
            raise ValueError(
                "Test 시작 시점 이후에 표시할 CSV 행이 없습니다: "
                f"{boundary.isoformat()}"
            )

        return cls(clean, test_rows, boundary)

    def __len__(self) -> int:
        return len(self._test_rows)

    @property
    def first_test_timestamp(self) -> pd.Timestamp:
        return self._test_rows.iloc[0][TIME_COLUMN]

    @property
    def last_test_timestamp(self) -> pd.Timestamp:
        return self._test_rows.iloc[-1][TIME_COLUMN]

    def get_item(self, position: int) -> dict[str, Any] | None:
        if position < 0 or position >= len(self):
            return None
        return self._test_rows.iloc[position].to_dict()

    def get_feature_trend(
        self,
        current_item: dict[str, Any],
        feature: str,
        window_size: int,
    ) -> pd.DataFrame:
        if feature not in self._all_rows.columns:
            return pd.DataFrame(columns=[TIME_COLUMN, feature])

        inspection_type = int(current_item[TYPE_COLUMN])
        stream_order = int(current_item[STREAM_ORDER_COLUMN])
        history = self._all_rows.loc[
            (self._all_rows[TYPE_COLUMN] == inspection_type)
            & (self._all_rows[STREAM_ORDER_COLUMN] <= stream_order),
            [TIME_COLUMN, feature],
        ].tail(window_size)
        return history.reset_index(drop=True)


def discover_sample_images(image_dir: str | Path) -> list[Path]:
    image_dir = Path(image_dir)
    if not image_dir.exists():
        return []

    return sorted(
        path
        for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
    )


def image_for_position(
    sample_images: Iterable[Path],
    position: int,
) -> Path | None:
    images = list(sample_images)
    if not images:
        return None
    return images[position % len(images)]

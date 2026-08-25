from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


class TypeConditionedPredictor:
    """Inspection Type별 XGBoost 모델 artifact를 감싼 추론 인터페이스."""

    def __init__(self, artifact: dict[str, Any]) -> None:
        required_keys = {
            "models_by_type",
            "feature_columns_by_type",
            "decision_threshold",
            "validation_end_time",
        }
        missing_keys = required_keys - set(artifact)
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise ValueError(f"모델 artifact 필수 키가 누락되었습니다: {missing}")

        self._artifact = artifact
        self._models = artifact["models_by_type"]
        self._feature_columns = artifact["feature_columns_by_type"]

    @classmethod
    def from_file(cls, model_path: str | Path) -> "TypeConditionedPredictor":
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_path}")
        return cls(joblib.load(model_path))

    @property
    def validation_end_time(self) -> str:
        return str(self._artifact["validation_end_time"])

    @property
    def decision_threshold(self) -> float:
        return float(self._artifact["decision_threshold"])

    def predict_defect_probability(self, row: dict[str, Any]) -> float:
        inspection_type = int(row["inspection_type"])
        if inspection_type not in self._models:
            raise ValueError(
                f"지원하지 않는 Inspection Type입니다: {inspection_type}"
            )

        feature_columns = self._feature_columns[inspection_type]
        missing_columns = [
            column for column in feature_columns if column not in row
        ]
        if missing_columns:
            missing = ", ".join(missing_columns[:5])
            raise ValueError(f"모델 입력 feature가 누락되었습니다: {missing}")

        model_input = pd.DataFrame(
            [[row[column] for column in feature_columns]],
            columns=feature_columns,
        )
        probability = self._models[inspection_type].predict_proba(model_input)[0, 1]
        return float(probability)

    def important_features(
        self,
        inspection_type: int,
        count: int = 2,
    ) -> list[str]:
        inspection_type = int(inspection_type)
        model = self._models[inspection_type]
        feature_columns = self._feature_columns[inspection_type]
        importances = np.asarray(model.feature_importances_, dtype=float)

        if len(importances) != len(feature_columns):
            return list(feature_columns[:count])

        ranked_positions = np.argsort(importances)[::-1]
        return [feature_columns[index] for index in ranked_positions[:count]]

    def feature_columns(self, inspection_type: int) -> list[str]:
        inspection_type = int(inspection_type)
        if inspection_type not in self._feature_columns:
            raise ValueError(
                f"지원하지 않는 Inspection Type입니다: {inspection_type}"
            )
        return list(self._feature_columns[inspection_type])


def get_mock_cause_feature(
    row: dict[str, Any],
    feature_by_type: dict[int, str],
) -> dict[str, Any]:
    """SHAP 준비 전 UI 확인용으로만 사용하는 명시적인 임시 설명값."""

    inspection_type = int(row["inspection_type"])
    feature = feature_by_type.get(inspection_type, "inspection_feat1")
    return {
        "feature": feature,
        "value": row.get(feature),
        "is_placeholder": True,
    }

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


class TypeConditionedPredictor:
    """단일 Type 모델과 체크포인트 앙상블을 감싼 추론 인터페이스."""

    def __init__(self, artifact: dict[str, Any]) -> None:
        required_keys = {
            "feature_columns_by_type",
            "decision_threshold",
            "validation_end_time",
        }
        missing_keys = required_keys - set(artifact)
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise ValueError(f"모델 artifact 필수 키가 누락되었습니다: {missing}")

        self._artifact = artifact
        self._feature_columns = artifact["feature_columns_by_type"]
        self._important_feature_cache: dict[int, list[str]] = {}

        if "models_by_type" in artifact:
            self._mode = "single"
            self._models = artifact["models_by_type"]
            self._members = None
            self._final_checkpoints = []
        elif "members" in artifact and "final_member_checkpoints" in artifact:
            self._mode = "ensemble"
            self._models = None
            self._members = artifact["members"]
            self._final_checkpoints = list(artifact["final_member_checkpoints"])
            if not self._final_checkpoints:
                raise ValueError("앙상블 checkpoint 목록이 비어 있습니다.")
        else:
            raise ValueError(
                "모델 artifact에 models_by_type 또는 ensemble members가 없습니다."
            )

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
    def experiment_id(self) -> str:
        return str(self._artifact.get("experiment_id", "unknown_model"))

    @property
    def decision_threshold(self) -> float:
        return float(self._artifact["decision_threshold"])

    @property
    def deduplicate_rows(self) -> bool:
        return bool(self._artifact.get("deduplicate_rows", True))

    def predict_defect_probability(self, row: dict[str, Any]) -> float:
        inspection_type = int(row["inspection_type"])
        if inspection_type not in self._feature_columns:
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

        if self._mode == "single":
            probability = self._models[inspection_type].predict_proba(
                model_input
            )[0, 1]
            return float(probability)

        probabilities = []
        for checkpoint in self._final_checkpoints:
            member = self._members[checkpoint][inspection_type]
            member_features = member.get("feature_columns", feature_columns)
            member_input = model_input[member_features]
            transformed = member["preprocessor"].transform(member_input)
            probability = member["model"].predict_proba(transformed)[0, 1]
            probabilities.append(float(probability))
        return float(np.mean(probabilities))

    def important_features(
        self,
        inspection_type: int,
        count: int = 2,
    ) -> list[str]:
        inspection_type = int(inspection_type)
        feature_columns = self._feature_columns[inspection_type]

        if inspection_type not in self._important_feature_cache:
            if self._mode == "single":
                scores = self._single_model_importances(
                    self._models[inspection_type],
                    feature_columns,
                )
            else:
                scores = self._ensemble_importances(
                    inspection_type,
                    feature_columns,
                )
            ranked_positions = np.argsort(-scores, kind="stable")
            self._important_feature_cache[inspection_type] = [
                feature_columns[index] for index in ranked_positions
            ]

        return self._important_feature_cache[inspection_type][:count]

    @staticmethod
    def _single_model_importances(
        model: Any,
        feature_columns: list[str],
    ) -> np.ndarray:
        importances = np.asarray(model.feature_importances_, dtype=float)

        if len(importances) != len(feature_columns):
            return np.zeros(len(feature_columns), dtype=float)
        return importances

    def _ensemble_importances(
        self,
        inspection_type: int,
        feature_columns: list[str],
    ) -> np.ndarray:
        feature_positions = {
            feature: index for index, feature in enumerate(feature_columns)
        }
        scores = np.zeros(len(feature_columns), dtype=float)

        for checkpoint in self._final_checkpoints:
            member = self._members[checkpoint][inspection_type]
            model_importances = np.asarray(
                member["model"].feature_importances_,
                dtype=float,
            )
            encoded_names = member["preprocessor"].get_feature_names_out()
            if len(model_importances) != len(encoded_names):
                continue

            for encoded_name, importance in zip(
                encoded_names,
                model_importances,
                strict=True,
            ):
                raw_feature = self._raw_feature_name(
                    str(encoded_name),
                    feature_columns,
                )
                if raw_feature is not None:
                    scores[feature_positions[raw_feature]] += float(importance)

        return scores

    @staticmethod
    def _raw_feature_name(
        encoded_name: str,
        feature_columns: list[str],
    ) -> str | None:
        stripped_name = encoded_name.split("__", maxsplit=1)[-1]
        matches = [
            feature
            for feature in feature_columns
            if stripped_name == feature or stripped_name.startswith(f"{feature}_")
        ]
        if not matches:
            return None
        return max(matches, key=len)

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

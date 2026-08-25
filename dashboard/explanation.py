from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from inference import TypeConditionedPredictor


@dataclass(frozen=True)
class FeatureSignal:
    """UI가 SHAP 구현 방식과 무관하게 소비하는 feature 신호 규격."""

    feature: str
    value: Any
    level: str
    label: str
    source: str
    contribution: float | None = None
    direction: str = "unknown"


class FeatureSignalProvider(Protocol):
    """현재 검사 행을 UI용 feature 신호로 변환하는 교체 지점."""

    def get_signals(
        self,
        row: dict[str, Any],
        inspection_type: int,
        count: int = 6,
    ) -> list[FeatureSignal]: ...


class DemoFeatureSignalProvider:
    """SHAP 연동 전 2x3 그리드의 동작을 확인하기 위한 데모 공급자."""

    _LEVELS = (
        ("low", "영향 낮음"),
        ("caution", "주의 신호"),
        ("high", "불량 방향 영향"),
        ("low", "영향 낮음"),
        ("caution", "주의 신호"),
        ("low", "영향 낮음"),
    )

    def __init__(self, predictor: TypeConditionedPredictor) -> None:
        self._predictor = predictor

    def get_signals(
        self,
        row: dict[str, Any],
        inspection_type: int,
        count: int = 6,
    ) -> list[FeatureSignal]:
        features = self._predictor.important_features(
            inspection_type,
            count=count,
        )
        record_id = int(row["record_id"])
        offset = record_id % len(self._LEVELS)

        signals = []
        for index, feature in enumerate(features):
            level, label = self._LEVELS[(index + offset) % len(self._LEVELS)]
            signals.append(
                FeatureSignal(
                    feature=feature,
                    value=row.get(feature),
                    level=level,
                    label=label,
                    source="demo",
                )
            )
        return signals


def build_feature_signal_provider(
    predictor: TypeConditionedPredictor,
) -> FeatureSignalProvider:
    """실제 SHAP 공급자가 준비되면 이 팩토리의 반환 구현만 교체한다."""

    return DemoFeatureSignalProvider(predictor)

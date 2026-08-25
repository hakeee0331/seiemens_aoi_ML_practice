from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class GlobalShapRule:
    """Dongjin 027 Global SHAP 결과에서 가져온 정적 표시 규칙."""

    feature: str
    raw_feature: str
    importance: float
    operator: Literal["lt", "eq"]
    threshold: float


@dataclass(frozen=True)
class FeatureSignal:
    """UI가 정적 SHAP 저장 방식과 무관하게 소비하는 feature 신호 규격."""

    feature: str
    raw_feature: str
    value: Any
    level: str
    label: str
    source: str
    rank: int
    contribution: float
    condition: str
    direction: str = "unknown"


class FeatureSignalProvider(Protocol):
    """현재 검사 행을 UI용 feature 신호로 변환하는 교체 지점."""

    def get_signals(
        self,
        row: dict[str, Any],
        inspection_type: int,
        count: int = 6,
    ) -> list[FeatureSignal]: ...


# notebooks/0826_dongjin_027_global_ensemble_shap.ipynb에서 계산한
# Test 전체의 Type별 mean(|SHAP|) 상위 6개와 Total Cover 최대 split이다.
GLOBAL_SHAP_RULES_BY_TYPE: dict[int, tuple[GlobalShapRule, ...]] = {
    0: (
        GlobalShapRule("inspection_feat41", "inspection_feat41", 0.8916, "lt", 0.4833),
        GlobalShapRule("meta_feat2=1", "meta_feat2", 0.7688, "eq", 1),
        GlobalShapRule("inspection_feat24", "inspection_feat24", 0.5144, "lt", 0.4542),
        GlobalShapRule("meta_feat4=0", "meta_feat4", 0.4432, "eq", 0),
        GlobalShapRule("meta_feat1=10", "meta_feat1", 0.3970, "eq", 10),
        GlobalShapRule("inspection_feat25", "inspection_feat25", 0.2829, "lt", 0.6167),
    ),
    1: (
        GlobalShapRule("inspection_feat48", "inspection_feat48", 1.2720, "lt", 0.0708),
        GlobalShapRule("inspection_feat24", "inspection_feat24", 0.6964, "lt", 0.0333),
        GlobalShapRule("meta_feat1=22", "meta_feat1", 0.5671, "eq", 22),
        GlobalShapRule("meta_feat4=28", "meta_feat4", 0.4157, "eq", 28),
        GlobalShapRule("inspection_feat4", "inspection_feat4", 0.3447, "lt", 0.4346),
        GlobalShapRule("inspection_feat3", "inspection_feat3", 0.3380, "lt", 0.5526),
    ),
    2: (
        GlobalShapRule("meta_feat1=27", "meta_feat1", 1.0023, "eq", 27),
        GlobalShapRule("inspection_feat96", "inspection_feat96", 0.9118, "lt", 0.2653),
        GlobalShapRule("inspection_feat95", "inspection_feat95", 0.6849, "lt", 0.2692),
        GlobalShapRule("inspection_feat12", "inspection_feat12", 0.6188, "lt", 0.0498),
        GlobalShapRule("inspection_feat22", "inspection_feat22", 0.5021, "lt", 0.7593),
        GlobalShapRule("meta_feat4=41", "meta_feat4", 0.4317, "eq", 41),
    ),
    3: (
        GlobalShapRule("meta_feat4=7", "meta_feat4", 0.7811, "eq", 7),
        GlobalShapRule("inspection_feat95", "inspection_feat95", 0.7195, "lt", 0.1538),
        GlobalShapRule("inspection_feat12", "inspection_feat12", 0.7046, "lt", 0.0092),
        GlobalShapRule("inspection_feat96", "inspection_feat96", 0.6594, "lt", 0.2245),
        GlobalShapRule("meta_feat1=27", "meta_feat1", 0.6477, "eq", 27),
        GlobalShapRule("inspection_feat94", "inspection_feat94", 0.4275, "lt", 0.2123),
    ),
    # Type 4는 027 분석에서 모든 feature의 mean(|SHAP|)가 0이다.
    4: (),
}


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(value != value)
    except (TypeError, ValueError):
        return False


def _equals(value: Any, expected: float) -> bool:
    try:
        return float(value) == float(expected)
    except (TypeError, ValueError):
        return str(value) == str(expected)


def _format_condition(rule: GlobalShapRule) -> str:
    if rule.operator == "eq":
        return f"= {rule.threshold:g}"
    return f"< {rule.threshold:.4f}"


class StaticGlobalShapProvider:
    """미리 계산된 Global SHAP 순위와 대표 split을 현재 행에 적용한다."""

    def get_signals(
        self,
        row: dict[str, Any],
        inspection_type: int,
        count: int = 6,
    ) -> list[FeatureSignal]:
        rules = GLOBAL_SHAP_RULES_BY_TYPE.get(int(inspection_type), ())[:count]
        signals = []

        for rank, rule in enumerate(rules, start=1):
            value = row.get(rule.raw_feature)
            condition = _format_condition(rule)

            if _is_missing(value):
                level = "missing"
                label = f"값 없음 · 대표 조건 {condition}"
                direction = "unknown"
            else:
                if rule.operator == "eq":
                    matched = _equals(value, rule.threshold)
                else:
                    matched = float(value) < rule.threshold
                level = "matched" if matched else "not-matched"
                state = "조건 일치" if matched else "조건 불일치"
                label = f"{state} · {condition}"
                direction = "condition_met" if matched else "condition_not_met"

            signals.append(
                FeatureSignal(
                    feature=rule.feature,
                    raw_feature=rule.raw_feature,
                    value=value,
                    level=level,
                    label=label,
                    source="global_shap_static",
                    rank=rank,
                    contribution=rule.importance,
                    condition=condition,
                    direction=direction,
                )
            )

        return signals


def build_feature_signal_provider() -> FeatureSignalProvider:
    return StaticGlobalShapProvider()

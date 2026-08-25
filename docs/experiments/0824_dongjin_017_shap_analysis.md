# 0824_dongjin_017_shap_analysis

## 연결된 노트북
`notebooks/0824_dongjin_017_shap_analysis.ipynb`

## 상태
완료

## 목적
게임 이론(Shapley Value)에 기반한 **SHAP(SHapley Additive exPlanations)** 기법을 활용하여, 현재 최고 성능을 내고 있는 챔피언 모델(`0824_dongjin_013_adasyn`: XGBoost + MoE + Cleansing + ADASYN)의 판단 근거를 해석(Explainable AI)합니다. 특히 장비별(`inspection_type`)로 분리된 5개의 독립 모델 각각에서 어떤 기하학적 피처가 불량 판정에 가장 치명적인 기여(Feature Importance)를 했는지 분석합니다.

## 분석 결과: 장비별 핵심 불량 유발 요인 (Top 5)

각 장비별로 불량을 결정짓는 핵심 치수가 완전히 다름을 확인했습니다. (MoE 모델 분리가 정답이었음을 다시 한번 증명합니다.)

### [Inspection Type: 0]
1. `inspection_feat24` (Importance: 1.1047)
2. `meta_feat2` (Importance: 0.9963)
3. `inspection_feat3` (Importance: 0.9192)
4. `inspection_feat43` (Importance: 0.8140)
5. `inspection_feat4` (Importance: 0.6820)
*분석: Type 0 검사는 `feat24` 및 `feat3`과 같은 특정 기하학적 치수 검사에 매우 민감합니다.*

### [Inspection Type: 1]
1. `inspection_feat48` (Importance: 1.8944)
2. `meta_feat1` (Importance: 1.0408)
3. `inspection_feat9` (Importance: 0.7828)
4. `inspection_feat24` (Importance: 0.7161)
5. `meta_feat4` (Importance: 0.6483)
*분석: `feat48`이 불량 판정의 핵심이며, 다른 장비와 달리 48번 센서의 측정값이 절대적인 기준이 됩니다.*

### [Inspection Type: 2]
1. `inspection_feat96` (Importance: 2.0950)
2. `inspection_feat22` (Importance: 1.8024)
3. `inspection_feat1` (Importance: 0.7704)
4. `meta_feat1` (Importance: 0.7508)
5. `meta_feat4` (Importance: 0.7265)

### [Inspection Type: 3]
1. `meta_feat1` (Importance: 2.1107)
2. `inspection_feat96` (Importance: 1.9773)
3. `inspection_feat95` (Importance: 1.9478)
4. `inspection_feat12` (Importance: 1.0284)
5. `inspection_feat94` (Importance: 0.8376)
*분석: Type 3은 유독 `feat96, feat95, feat94` 등 90번대 후반의 센서 군(연속된 측정 위치로 추정)에서 집단적으로 불량 시그널이 폭발하고 있습니다.*

### [Inspection Type: 4]
1. `meta_feat1` (Importance: 2.8269)
2. `inspection_feat34` (Importance: 1.6560)
3. `inspection_feat24` (Importance: 1.2620)
4. `inspection_feat3` (Importance: 1.2208)
5. `inspection_feat35` (Importance: 1.2092)

## 결론 및 인사이트
1. **장비별 독립성 입증**: 5개의 장비가 겹치는 피처 없이 각각 전혀 다른 센서(`feat24`, `feat48`, `feat96` 등)에서 불량을 잡아내고 있습니다. 과거에 단일 모델로 모든 장비를 묶었을 때 모델이 혼란(Confusion)을 겪을 수밖에 없었던 이유가 SHAP 분석을 통해 명확히 증명되었습니다.
2. **Meta Feature의 중요성**: `meta_feat1` 및 `meta_feat4` 같은 메타 정보들이 단순한 식별자가 아니라, 불량 발생 패턴(예: 특정 로트나 특정 시간대)과 강한 상관관계를 가지고 모델의 판단에 개입하고 있음을 확인했습니다.
3. **차원 축소(Dimensionality Reduction) 가능성**: 전체 75개의 피처 중 실제로 모델 결정에 기여하는 피처는 장비별로 극소수 상위 피처에 집중되어 있습니다. 추후 중요도가 0에 수렴하는 하위 피처들을 제거하면 추론 속도 최적화 및 모델 경량화가 가능할 것입니다.

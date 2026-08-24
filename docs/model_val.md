# 모델 평가 목록

이 문서는 여러 실험 노트북에서 생성한 모델의 최종 Test 성능을 한곳에서 비교하기 위한 요약표다. 상세 전처리, 학습 과정, 전체 지표와 해석은 연결된 노트북 및 실험 문서에서 확인한다.

## 기록 기준

- Validation이 아닌, 학습과 모델 선택에 사용하지 않은 **Test 데이터**의 결과만 기록한다.
- 한 행은 하나의 `실험 + 모델 + threshold` 결과를 나타낸다.
- 같은 모델이라도 threshold 또는 Test 구간이 다르면 별도 행으로 기록한다.
- 지표 수치는 노트북을 처음부터 끝까지 실행한 최종 출력과 일치해야 한다.
- 비교 시 Test 기간과 데이터 처리 조건이 같은지 먼저 확인한다.

## 지표 정의

- `PR-AUC`: 실제 불량인 `class=1`을 positive로 계산한 Average Precision이다.
- `Threshold`: 확률을 최종 클래스 판정으로 바꾸는 의사결정 임계값이다.
- `Real Defect Recall`: 실제 불량 중 모델이 불량으로 탐지한 비율로 `TP / (TP + FN)`이다.
- `TP`: 실제 불량을 불량으로 올바르게 탐지한 수다.
- `FN`: 실제 불량을 false call로 잘못 판정한 수다.
- `False Call Reduction`: 실제 false call 중 모델이 false call로 판정해 수동검사를 줄일 수 있는 비율로 `TN / (TN + FP)`이다.

## 최종 Test 평가

| Experiment | Model | Test period (UTC) | PR-AUC | Threshold | Real Defect Recall | TP | FN | False Call Reduction | Notebook |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| [`0824_kimjaehak_005_xgboost_baseline`](experiments/0824_kimjaehak_005_xgboost_baseline.md) | XGBoost baseline | 1970-10-13 13:14:58 ~ 1970-11-02 14:21:28 | 0.237 | 0.500 | 26.2% | 590 | 1,659 | 98.7% | [notebook](../notebooks/0824_kimjaehak_005_xgboost_baseline.ipynb) |
| [`0824_kimjaehak_006_type_conditioned_baseline`](experiments/0824_kimjaehak_006_type_conditioned_baseline.md) | Type-conditioned XGBoost baseline | 1970-10-13 13:14:58 ~ 1970-11-02 14:21:28 | 0.315 | 0.500 | 31.6% | 711 | 1,538 | 98.7% | [notebook](../notebooks/0824_kimjaehak_006_type_conditioned_baseline.ipynb) |
| [`0824_lsw_003_structure_comparison`](experiments/0824_lsw_003_structure_comparison.md) | XGBoost 통합모델 (Slip Rate ≤1% 임계값) | 1970-10-13 13:14:58 ~ 1970-11-02 14:21:28 | 0.237 | ~0.000 | 99.8% | 2,244 | 5 | 0.1% | [notebook](../notebooks/0824_lsw_003_structure_comparison.ipynb) |
| [`0824_lsw_003_structure_comparison`](experiments/0824_lsw_003_structure_comparison.md) | XGBoost 5분리모델 (유형별 임계값, pooled) | 1970-10-13 13:14:58 ~ 1970-11-02 14:21:28 | 해당 없음(유형별 상이) | 유형별 상이 | 96.2% | 2,164 | 85 | 31.4% | [notebook](../notebooks/0824_lsw_003_structure_comparison.ipynb) |

표에는 비교하기 쉬운 반올림 값을 표시한다. 정확한 계산값과 confusion matrix는 연결된 실험 문서와 노트북에 기록한다.

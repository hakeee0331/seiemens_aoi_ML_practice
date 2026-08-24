# 0824_kimjaehak_006_type_conditioned_baseline

## 연결된 노트북

`notebooks/0824_kimjaehak_006_type_conditioned_baseline.ipynb`

## 상태

완료

## 목적

기존 통합 XGBoost baseline과 동일한 데이터 정리 및 시간순 평가 조건을 유지하면서, `inspection_type`별 유효 피처와 개별 모델을 적용하는 type-conditioned baseline을 구성한다.

## 이전 실험 대비 주요 변경사항

- 전체 `data/raw/dataset.csv`를 불러오고 첫 번째 익명 행 식별자 열을 `record_id`로 명명한다.
- 기존 `0824_kimjaehak_005_xgboost_baseline`과 동일하게 `record_id`와 `timestamp`를 제외한 나머지 컬럼이 모두 같은 행을 중복으로 판단한다.
- 중복 행은 원본 순서에서 처음 등장한 행만 유지한다.
- 중복 제거 후 전체 데이터에 공통 timestamp-group 60/20/20 시간순 분할을 적용한다.
- 공통 기간 경계를 유지한 상태에서 `inspection_type`별 Train/Validation/Test DataFrame을 생성한다.
- 공통 `meta_feat`와 `mapping.json`에 정의된 해당 type의 `inspection_feat`만 모델 입력으로 사용한다.
- 검사유형별 XGBoost 모델 5개를 학습하고 type별 예측확률을 원래 행 순서로 결합한다.
- 기존 baseline과 동일한 threshold 0.5에서 전체 및 type별 Validation/Test 성능을 평가한다.

## 평가 방법

- 동일한 중복 제거 기준과 timestamp-group 시간순 분할을 사용한다.
- `class=1`을 실제 불량 positive class로 사용한다.
- 기본 의사결정 임계값은 기존 baseline과 동일한 0.5를 사용한다.
- 전체 및 `inspection_type`별 confusion matrix, Accuracy, Precision, Recall, Specificity, F1, ROC-AUC, PR-AUC를 계산한다.
- Test는 모델이나 임계값 선택에 사용하지 않고 최종 평가에만 사용한다.

## 주요 결과

- 원본 440,274행에서 48,282개 중복 행을 제거해 391,992행을 사용했다.
- Test confusion matrix는 TN 75,192건, FP 955건, FN 1,538건, TP 711건이다.
- Test Accuracy 0.968200, Precision 0.426771, Recall 0.316141, Specificity 0.987458, F1 0.363218이다.
- Test ROC-AUC는 0.873366, PR-AUC는 0.315411이다.
- 기존 통합 XGBoost baseline 대비 PR-AUC는 0.236803에서 0.315411로, Recall은 0.262339에서 0.316141로, F1은 0.306573에서 0.363218로 증가했다.

| inspection_type | Test 행 | 모델 피처 | PR-AUC | Precision | Recall | False Call Reduction | TP | FN |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 16,784 | 48 | 0.068391 | 1.000000 | 0.007519 | 1.000000 | 1 | 132 |
| 1 | 11,112 | 56 | 0.391866 | 0.369948 | 0.455357 | 0.941131 | 357 | 427 |
| 2 | 19,153 | 69 | 0.356827 | 0.513742 | 0.345661 | 0.987534 | 243 | 460 |
| 3 | 30,591 | 69 | 0.269568 | 0.526316 | 0.182421 | 0.996699 | 110 | 493 |
| 4 | 756 | 25 | 0.021803 | 0.000000 | 0.000000 | 0.975342 | 0 | 26 |

## 운영 관점 핵심 지표

| Model | PR-AUC | Threshold | Real Defect Recall | TP | FN | False Call Reduction |
|---|---:|---:|---:|---:|---:|---:|
| Type-conditioned XGBoost baseline | 0.315 | 0.500 | 31.6% | 711 | 1,538 | 98.7% |

## 결론 및 다음 단계

- 동일한 데이터, 분할, XGBoost 설정과 threshold에서 type-conditioning이 통합 baseline보다 전체 PR-AUC와 Recall을 개선했다.
- type 1과 2는 상대적으로 높은 PR-AUC와 Recall을 보였지만 type 0과 4는 threshold 0.5에서 실제 불량을 거의 탐지하지 못했다.
- 전체 Recall 0.316141은 운영 안전 목표에 부족하므로 threshold 0.5를 운영 임계값으로 사용하지 않는다.
- 후속 실험에서는 Test를 보지 않고 Validation에서 type별 최소 Recall 제약을 만족하는 threshold를 선택한다.
- type 4는 Train 3,518행과 실제 불량 13건으로 표본이 작아 별도 모델과 threshold의 불확실성을 함께 고려한다.

## 저장 모델

`models/0824_kimjaehak_006_type_conditioned_baseline.pkl`

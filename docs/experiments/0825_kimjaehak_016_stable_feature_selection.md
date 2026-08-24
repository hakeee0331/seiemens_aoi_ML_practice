# 0825_kimjaehak_016_stable_feature_selection

## 연결된 노트북

`notebooks/0825_kimjaehak_016_stable_feature_selection.ipynb`

## 상태

완료 — 노트북 전체 실행과 결과 검증 완료

## 목적

Mapping 기반 검사유형별 XGBoost에서 시간적으로 안정적인 저기여 피처만 보수적으로 제거하면 성능을 유지하면서 모델을 단순화할 수 있는지 검증한다.

`0824_dongjin_020_dim_reduction`은 SHAP·RuleFit 상위 피처 21개만 남기는 공격적인 축소에서 Test PR-AUC가 크게 하락했다. 이번 실험은 전역 Top-K를 모든 검사유형에 강제하지 않고, Train 내부 미래 구간에서 반복 측정한 permutation importance를 사용해 유형별 축소 후보를 만든다.

## 이전 실험 대비 주요 변경사항

- 006 baseline과 동일한 중복 제거, 전체 시간 경계, mapping 기반 type별 피처와 XGBoost 설정을 사용했다.
- 전체 Train 안에 5개 시간 window를 만들고 3개 expanding Fold에서 permutation importance를 계산했다.
- 검사유형별로 전체·상위 75%·상위 50%·안정적 양수 중요도·meta 제외 후보를 비교했다.
- 피처 순위는 Train 내부 데이터만으로 계산하고 후보 선택은 기존 Validation PR-AUC로 수행했다.
- Test를 확인하기 전에 후보 구성과 선택 허용폭을 고정했다.
- 비용함수와 운영 threshold는 최적화하지 않고 threshold `0.5`만 보조 평가했다.

## 데이터와 실행 검증

- 중복 제거 후 데이터: 391,992행
- Train / Validation / Test: 235,222 / 78,374 / 78,396행
- mapping 기반 피처 수:
  - Type 0: 48개
  - Type 1: 56개
  - Type 2: 69개
  - Type 3: 69개
  - Type 4: 25개
- 코드 셀 11개 전체 실행, 오류 0건
- permutation 평가 2,328회
- Type 4의 첫 importance Fold는 평가 양성이 0개라 제외하고 나머지 2개 Fold만 사용
- 모델 파일은 저장하지 않음

## 평가 방법

### Train 내부 시간 importance

Train을 timestamp 그룹 기준 약 20% 단위 `I01~I05`로 나누고 다음 Fold를 사용했다.

| Fold | 학습 | Importance 평가 |
|---:|---|---|
| 1 | I01~I02 | I03 |
| 2 | I01~I03 | I04 |
| 3 | I01~I04 | I05 |

각 Fold에서 피처 하나를 3회 독립적으로 섞고, 원래 PR-AUC와 섞은 뒤 PR-AUC의 차이를 importance로 계산했다.

```text
importance = original PR-AUC - permuted PR-AUC
stable score = median(importance) × positive importance 비율
```

### 축소 후보

- `all_features`: mapping 피처 전체
- `top_75_pct`: stable score 상위 75%
- `top_50_pct`: stable score 상위 50%
- `stable_positive`: importance 중앙값이 양수이고 반복의 절반 이상에서 양수
- `no_meta`: 공통 meta 피처 4개 제외

모든 후보는 최소 5개 피처를 유지했다.

### Validation 선택 규칙

Validation PR-AUC 최고 후보와 다음 허용폭 이내인 후보 중 피처 수가 가장 작은 후보를 선택했다.

```text
tolerance = min(0.01, 최고 Validation PR-AUC의 5%)
```

희소 type에서 절대 허용폭 0.01이 과도한 열화를 허용하지 않도록 상대 허용폭을 함께 적용했다.

### 사전 성공 기준

- 전체 type 모델의 피처 수 합계를 25% 이상 감소
- Test에서 type별 허용 열화폭을 벗어나지 않은 유형이 4개 이상
- 보조 pooled PR-AUC 하락이 절대 0.01 이내

3개 type만 유지하면 부분 지지, 그 외는 지지하지 않는 것으로 정했다.

## 주요 결과

### Validation 기반 선택

| inspection_type | 선택 후보 | 피처 수 | 감소율 | Baseline Validation PR-AUC | 선택 모델 Validation PR-AUC |
|---:|---|---:|---:|---:|---:|
| 0 | no_meta | 48 → 44 | 8.3% | 0.002405 | 0.007489 |
| 1 | all_features | 56 → 56 | 0.0% | 0.586063 | 0.586063 |
| 2 | no_meta | 69 → 65 | 5.8% | 0.050334 | 0.428081 |
| 3 | all_features | 69 → 69 | 0.0% | 0.140335 | 0.140335 |
| 4 | top_50_pct | 25 → 13 | 48.0% | 0.054825 | 0.071144 |

Type 1과 Type 3은 피처 축소 후보가 최고 Validation 성능의 허용폭을 벗어나 전체 피처를 유지했다. Type 0·2는 meta 피처를 제외했고 Type 4만 절반 수준의 축소 후보가 선택됐다.

### 검사유형별 Test

| inspection_type | 선택 후보 | Baseline PR-AUC | 선택 모델 PR-AUC | ΔPR-AUC | ΔRecall | ΔTN | ΔFN |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | no_meta | 0.068391 | 0.049924 | -0.018467 | -0.007519 | 0 | +1 |
| 1 | all_features | 0.391866 | 0.391866 | 0.000000 | 0.000000 | 0 | 0 |
| 2 | no_meta | 0.356827 | 0.617585 | +0.260758 | -0.125178 | +216 | +88 |
| 3 | all_features | 0.269568 | 0.269568 | 0.000000 | 0.000000 | 0 | 0 |
| 4 | top_50_pct | 0.021803 | 0.059086 | +0.037283 | +0.038462 | +17 | -1 |

Type 2는 meta 피처를 제외하자 Validation과 Test PR-AUC가 모두 크게 상승했다. 그러나 threshold 0.5에서는 Recall이 12.52%p 낮아지고 FN이 88건 증가했다. 이는 피처 제거에 따른 raw probability scale 변화가 섞인 결과이므로, PR-AUC 개선과 운영 판정 개선을 같은 의미로 해석하지 않는다.

Type 0의 no-meta 후보는 Validation에서는 개선됐지만 Test PR-AUC가 0.018467 하락해 시간 전이에 실패했다. Type 4는 Test PR-AUC와 Recall이 함께 개선됐지만 importance 평가 양성이 Fold별 6개와 3개뿐이어서 불확실성이 크다.

### Pooled Test

| 모델 | PR-AUC | Precision | Recall | F1 | TN | FP | FN | TP | False Call Reduction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 전체 mapping baseline | 0.315411 | 0.426771 | 0.316141 | 0.363218 | 75,192 | 955 | 1,538 | 711 | 98.75% |
| Validation 선택 축소 모델 | 0.339216 | 0.463197 | 0.277012 | 0.346689 | 75,425 | 722 | 1,626 | 623 | 99.05% |

- 전체 피처 수 합계: 267개 → 247개
- 전체 피처 감소율: 7.5%
- type별 허용 열화폭 이내: 4/5
- pooled ΔPR-AUC: +0.023805
- 고정 threshold 0.5에서 TN은 233건 증가했지만 FN도 88건 증가

Pooled PR-AUC는 서로 다른 type 모델의 raw score scale 차이에 영향을 받을 수 있어 보조 지표로만 해석한다.

## 결론

- 사전 목표였던 피처 25% 감소에 크게 미달했으므로 보수적 feature selection 가설은 **지지되지 않았다(`not_supported`)**.
- Type 1·3은 mapping 피처를 그대로 유지해야 Validation 성능이 보존됐다. 이는 약한 피처 조합을 공격적으로 제거하면 성능이 하락한다는 `dongjin_020`의 결론을 지지한다.
- 모든 type에서 meta 피처를 일괄 제거하면 안 된다. Type 2에서는 큰 PR-AUC 개선이 있었지만 Type 0에서는 미래 Test 성능이 악화했다.
- Type 2의 no-meta 결과는 별도 가설로는 유망하지만 Test를 이미 확인했으므로 이 실험에서 선택 규칙을 수정하거나 추가 탐색하지 않는다.
- Type 4의 축소 결과는 양성 표본 부족으로 재현성 검증이 필요하다.

후속 실험을 진행한다면 Type 2의 meta 피처가 기간별로 어떤 shortcut 또는 drift 신호를 만드는지 진단하고, 새로운 시간 Fold에서 no-meta 효과를 재검증해야 한다. 비용·threshold 최적화는 이 실험과 분리한다.

## 저장 모델

비교 실험이므로 모델 파일을 저장하지 않았다.

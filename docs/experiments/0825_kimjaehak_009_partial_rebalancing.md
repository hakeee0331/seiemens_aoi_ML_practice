# 0825_kimjaehak_009_partial_rebalancing

## 연결된 노트북

`notebooks/0825_kimjaehak_009_partial_rebalancing.ipynb`

## 상태

완료 — 노트북 전체 실행과 결과 검증 완료

## 목적

`0824_kimjaehak_006_type_conditioned_baseline`의 데이터 처리, 시간순 분할, mapping 기반 검사유형별 피처와 XGBoost 구조를 유지하면서 클래스 불균형 보정의 **적용 강도**를 검증한다.

기존 불균형 실험에서는 SMOTE, ADASYN, Random Undersampling을 주로 소수·다수 클래스가 1:1이 되도록 적용했다. 완전한 균형은 합성 불량을 지나치게 늘리거나 정상 표본을 과도하게 제거하여, PR-AUC가 개선되더라도 Recall, F1 또는 confusion matrix가 악화될 수 있다.

이 실험은 불균형 처리 기법을 적용할지 여부만 비교하지 않고, 원본 분포와 1:1 사이의 부분 리샘플링 비율을 탐색한다. 또한 단일 random seed의 우연한 결과를 최적 설정으로 선택하지 않도록 상위 후보의 seed 안정성을 별도로 검증한다.

## 배경과 기존 실험과의 차이

- `0824_kimjaehak_006_type_conditioned_baseline`은 클래스 불균형 보정 없이 검사유형별 XGBoost 5개를 학습했다.
- `0824_dongjin_012_smote`, `013_adasyn`, `014_undersampling`은 각 리샘플링 기법의 적용 가능성을 확인했지만 리샘플링 강도를 체계적으로 비교하지 않았다.
- `0824_lsw_004_imbalance_handling`은 검사유형별로 class weight, SMOTE, ADASYN, undersampling을 비교했으나 대부분 기본 1:1 비율과 단일 seed를 사용했다.
- 본 실험은 새로운 합성 기법을 추가하지 않는다. 동일 기법에서 **목표 클래스 비율과 seed 안정성**만 변화시켜 기존 실험의 빈틈을 검증한다.

## 가설

### 주가설

소수·다수 클래스를 완전히 1:1로 맞추는 것보다 중간 수준의 부분 리샘플링이 검사유형별 Validation PR-AUC와 Test 일반화 성능의 균형을 개선한다.

### 보조 가설

- 검사유형마다 원래 양성 비율과 분류 난도가 다르므로 최적 기법과 목표 비율도 다르다.
- 단일 seed에서 가장 높은 PR-AUC를 기록한 설정이 여러 seed에서는 불안정할 수 있다.
- 평균 성능이 약간 낮더라도 seed 변동성이 작은 설정이 미래 Test에서 더 안전할 수 있다.

## 고정 조건

다음 조건은 006 baseline과 동일하게 유지한다.

- `record_id`, `timestamp`를 제외하고 입력과 `class`가 모두 같은 행의 중복 제거
- 동일 timestamp 그룹을 분리하지 않는 누적 행 수 기준 약 60/20/20 시간순 Train/Validation/Test 분할
- 전체 데이터에서 공통 시간 경계를 계산한 후 `inspection_type`별 분리
- `mapping.json`에 정의된 유형별 `inspection_feat`와 공통 `meta_feat` 사용
- 검사유형별 XGBoost 모델 5개
- XGBoost 파라미터와 random seed `42` 고정
- Train에만 리샘플링 적용
- Validation과 Test의 원래 클래스 비율 및 행 구성 유지
- `scale_pos_weight` 미적용

변경하는 요소는 리샘플링 기법, 목표 minority/majority 비율, 리샘플링 random seed뿐이다.

## 비교 대상

### 기법

- Baseline: 리샘플링 없음
- SMOTE
- ADASYN
- Random Undersampling

### 목표 비율

`sampling_strategy`는 리샘플링 이후 `minority / majority` 비율이다.

| 목표 비율 | 의미 |
|---:|---|
| 0.05 | 약 1:20 |
| 0.10 | 약 1:10 |
| 0.25 | 약 1:4 |
| 0.50 | 약 1:2 |
| 1.00 | 1:1 완전 균형 |

목표 비율이 해당 검사유형의 원래 minority/majority 비율 이하이거나 리샘러가 표본 구조상 실행되지 못하면 실패 사유를 결과표에 기록하고 후보에서 제외한다.

## 실험 절차

### 1단계: 부분 리샘플링 비율 Screening

- 모든 검사유형에서 Baseline과 `3개 기법 × 5개 목표 비율`을 비교한다.
- 리샘플링 seed는 `42`로 고정한다.
- 후보 순위는 유형별 Validation PR-AUC로만 계산한다.
- 검사유형별 상위 비-baseline 후보 2개를 다음 단계로 전달한다.
- Test 예측이나 Test 라벨은 후보 선택에 사용하지 않는다.

예상 학습 횟수는 `5개 유형 × 16개 설정 = 80회`다.

### 2단계: seed 안정성 검증

- 1단계에서 선택된 유형별 상위 후보 2개를 seed `42~51`로 반복한다.
- XGBoost seed는 `42`로 고정하고 리샘플러 seed만 변경한다.
- 후보별 Validation PR-AUC 평균, 표준편차, 최솟값, 최댓값과 Baseline을 이긴 seed 비율을 기록한다.
- 다음 보수적 점수로 검사유형별 최종 설정을 고정한다.

```text
robust_score = mean(Validation PR-AUC) - std(Validation PR-AUC)
```

- Baseline도 표준편차 0인 후보로 선택 풀에 포함한다.
- 부분 리샘플링 후보가 불안정하거나 Baseline보다 낮으면 해당 유형은 Baseline을 유지한다.

예상 추가 학습 횟수는 `5개 유형 × 후보 2개 × seed 10개 = 100회`다.

### 3단계: 최종 Test 평가

- 2단계에서 고정된 검사유형별 설정을 `FINAL_RESAMPLING_SEED=42`로 다시 학습한다.
- 설정 고정 이후 Test를 한 번 평가한다.
- Test 결과를 확인한 뒤 기법, 목표 비율, seed, 후보 수 또는 선택 기준을 수정하지 않는다.
- 변경이 필요하면 새로운 실험 ID로 분리한다.

## 평가 방법

### 후보 선택의 주지표

- 검사유형별 Validation PR-AUC
- 여러 seed의 Validation PR-AUC 평균과 표준편차
- `robust_score`

서로 다른 검사유형 모델의 원시 확률은 같은 스케일이라고 보장되지 않는다. 따라서 후보 선택과 주 결론은 유형별 PR-AUC를 우선한다. Pooled PR-AUC는 전체 방향을 확인하는 보조 지표로만 사용한다.

### 최종 Test 지표

- PR-AUC
- ROC-AUC
- Accuracy
- Precision
- Recall
- Specificity
- F1
- TN, FP, FN, TP
- Baseline 대비 ΔTN, ΔFN

다음 두 판정 조건을 함께 기록한다.

1. 고정 threshold `0.5`: 006 baseline과 직접 비교
2. Validation 최대 F1 threshold: 리샘플링에 따른 확률 스케일 변화를 고려한 보조 비교

Validation 최대 F1 threshold는 유형별로 선택하고 Test에서는 고정한다. 이 과정은 확률 calibration을 수행하는 별도 실험과 구분한다.

## 사전 해석 기준

### 부분 리샘플링 가설을 지지하는 결과

- 하나 이상의 유형에서 1:1보다 낮은 목표 비율이 가장 높은 `robust_score`를 기록한다.
- 선택된 부분 리샘플링이 여러 seed에서 Baseline을 일관되게 이긴다.
- Test에서 유형별 PR-AUC가 개선되고 ΔTN·ΔFN이 한쪽으로 심각하게 붕괴하지 않는다.
- 일부 유형은 Baseline을 유지하고 일부 유형만 부분 리샘플링을 선택하는 결과도 가설을 지지한다.

### 가설을 지지하지 않는 결과

- 모든 부분 리샘플링 후보의 `robust_score`가 Baseline보다 낮다.
- Screening 1위 설정이 seed에 따라 크게 변한다.
- Validation 개선이 Test에 전이되지 않는다.
- PR-AUC 개선과 달리 confusion matrix에서 FP 또는 FN이 과도하게 증가한다.

## 예상 한계와 주의사항

- Type 0과 Type 4는 양성 표본이 특히 적어 Validation PR-AUC와 seed 안정성 추정의 불확실성이 크다.
- SMOTE와 ADASYN은 라벨 오류나 드문 경계 표본을 합성하여 확대할 수 있다.
- Random Undersampling은 목표 비율이 커질수록 정상 데이터 정보 손실이 증가한다.
- 단일 시간순 60/20/20 분할에서 얻은 결과이므로 다른 시간 구간에서도 동일한 설정이 우수하다고 일반화할 수 없다.
- 총 학습 횟수가 약 190회이므로 실행 시간이 길 수 있다.
- Pooled 확률 기반 지표는 유형별 모델의 확률 스케일 차이에 영향을 받을 수 있다.

## 주요 결과

### 실행 및 데이터 검증

- 코드 셀 13개 전체 실행, 오류 0건
- 원본 440,274행에서 baseline 기준 중복 48,282행 제거
- 최종 분석 데이터 391,992행
- Train 235,222행 / Validation 78,374행 / Test 78,396행
- Screening 80회, seed 안정성 검증 100회와 최종 비교 학습 완료

### Validation 기반 설정 선택

| inspection_type | 최종 설정 | Validation PR-AUC 평균 | 표준편차 | robust score | 후보의 Baseline 승리 seed 비율 |
|---:|---|---:|---:|---:|---:|
| 0 | baseline | 0.002405 | 0 | 0.002405 | 해당 없음 |
| 1 | baseline | 0.586063 | 0 | 0.586063 | 해당 없음 |
| 2 | undersample, ratio 0.25 | 0.215149 | 0.110551 | 0.104598 | 90% |
| 3 | baseline | 0.140335 | 0 | 0.140335 | 해당 없음 |
| 4 | baseline | 0.054825 | 0 | 0.054825 | 해당 없음 |

Type 2에서만 약 1:4 부분 undersampling이 선택됐다. 나머지 유형은 단일 seed Screening에서 일부 리샘플링 후보가 높았더라도 여러 seed의 변동성을 패널티로 반영하면 baseline보다 `robust_score`가 낮았다.

주요 탈락 사례는 다음과 같다.

- Type 0 undersampling 0.50: PR-AUC `0.003074 ± 0.001792`, robust score 0.001282로 baseline 0.002405보다 낮음
- Type 1 ADASYN 0.50: PR-AUC `0.576088 ± 0.036756`, robust score 0.539332로 baseline 0.586063보다 낮고 10개 seed 중 3개만 baseline을 이김
- Type 3 undersampling 0.10: PR-AUC `0.125587 ± 0.057688`, robust score 0.067898로 baseline 0.140335보다 낮음
- Type 4 undersampling 1.00: PR-AUC `0.075772 ± 0.026678`, robust score 0.049094로 baseline 0.054825보다 낮음

### Type 2 Test 상세

| Threshold 정책 | 모델 | Threshold | PR-AUC | Precision | Recall | F1 | TN | FP | FN | TP |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 고정 0.5 | baseline | 0.500000 | 0.356827 | 0.513742 | 0.345661 | 0.413265 | 18,220 | 230 | 460 | 243 |
| 고정 0.5 | undersample 0.25 | 0.500000 | 0.561603 | 0.388018 | 0.598862 | 0.470917 | 17,786 | 664 | 282 | 421 |
| Validation F1 | baseline | 0.738900 | 0.356827 | 0.515284 | 0.167852 | 0.253219 | 18,339 | 111 | 585 | 118 |
| Validation F1 | undersample 0.25 | 0.970494 | 0.561603 | 0.861017 | 0.361309 | 0.509018 | 18,409 | 41 | 449 | 254 |

고정 threshold 0.5에서 Type 2는 다음과 같이 변했다.

- PR-AUC: 0.356827 → 0.561603
- Recall: 34.57% → 59.89%
- F1: 0.413265 → 0.470917
- TN: -434
- FN: -178

Validation F1 threshold를 고정해 적용하면 selected 모델은 baseline 대비 TN이 70건 증가하고 FN이 136건 감소해 두 방향에서 동시에 개선됐다.

### Pooled Test 결과

| Threshold 정책 | 모델 | PR-AUC | Precision | Recall | F1 | TN | FP | FN | TP |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 고정 0.5 | baseline | 0.315411 | 0.426771 | 0.316141 | 0.363218 | 75,192 | 955 | 1,538 | 711 |
| 고정 0.5 | selected | 0.383311 | 0.390255 | 0.395287 | 0.392755 | 74,758 | 1,389 | 1,360 | 889 |
| Validation F1 | baseline | 0.315411 | 0.257785 | 0.198755 | 0.224454 | 74,860 | 1,287 | 1,802 | 447 |
| Validation F1 | selected | 0.383311 | 0.323889 | 0.259226 | 0.287972 | 74,930 | 1,217 | 1,666 | 583 |

고정 threshold 0.5에서 pooled PR-AUC는 0.315411에서 0.383311, Recall은 31.61%에서 39.53%, F1은 0.363218에서 0.392755로 상승했다. TN 434건을 더 잃는 대신 FN 178건을 줄였다.

Validation F1 threshold 정책에서는 selected 모델이 baseline 대비 TN 70건과 TP 136건을 추가 확보했다. 다만 서로 다른 type 모델의 원시 확률 스케일은 직접 비교 가능하다고 보장되지 않으므로 pooled PR-AUC는 보조 지표로만 사용한다.

## 결론 및 다음 단계

- 1:1 완전 균형을 모든 검사유형에 일괄 적용하는 전략은 채택하지 않는다.
- 부분 리샘플링 가설은 **Type 2에 한해 지지**된다.
- 최종 구성은 Type 2에만 1:4 Random Undersampling을 적용하고 Type 0·1·3·4는 baseline을 유지한다.
- Type 2의 Test PR-AUC와 F1은 개선됐지만 seed별 Validation PR-AUC 표준편차가 0.110551로 커, 결과가 표본 추출과 시간 구간에 민감할 가능성이 남는다.
- Validation F1 threshold는 Type 3에서 0.999992를 선택해 Test Recall이 0.995%로 붕괴했다. sparse positive와 drift가 있는 데이터에서 단일 Validation F1 최적화는 안정적인 운영 threshold가 아니다.
- Test를 이미 사용했으므로 현재 실험 안에서 비율이나 선택 기준을 다시 조정하지 않는다.
- 후속 실험에서는 새로운 ID를 사용해 walk-forward 구간에서 Type 2의 1:4 undersampling 재현성을 검증한다.
- `docs/experiments/index.md`와 `docs/model_val.md`는 다른 채팅의 진행 중 변경과 충돌할 수 있어 이번 단계에서 수정하지 않았다.

## 저장 모델

이번 실험은 비교 목적이므로 모델 파일을 저장하지 않는다. 실행 중 모델은 노트북 메모리의 `final_models` 딕셔너리에서 확인한다.

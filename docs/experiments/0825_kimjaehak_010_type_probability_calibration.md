# 0825_kimjaehak_010_type_probability_calibration

## 연결된 노트북

`notebooks/0825_kimjaehak_010_type_probability_calibration.ipynb`

## 상태

완료

## 목적

`kimjaehak_006`의 type별 XGBoost 5개를 고정한 채, 직전 시간 구간에서 raw score를 확률로 보정하면 type·구간별 threshold를 다시 최적화하지 않고 하나의 비용 기반 확률 threshold를 사용할 수 있는지 검증한다.

`kimjaehak_008`은 직전 구간의 raw score에서 Slip Rate 1%를 만족하는 threshold를 직접 골랐지만 다음 구간에서 안전성이 유지되지 않았다. 이번 실험은 score의 절대값이 시간과 type에 따라 다른 문제를 Platt calibration으로 보정하는 대응이다.

## 이전 실험 대비 주요 변경사항

- W01~W06으로 학습한 `kimjaehak_006` 구조와 mapping 기반 피처를 유지했다.
- W07→W08, W08→W09, W09→W10 순서로 직전 구간에서 Platt calibrator를 fit하고 다음 구간에 적용했다.
- 양성 20개 이상, 음성 100개 이상인 type은 별도 calibrator를 갱신했다.
- type 표본이 부족하고 과거 type calibrator도 없으면 해당 직전 구간 전체의 pooled calibrator를 사용했다. 과거 type calibrator가 있으면 이를 유지했다.
- Platt slope가 음수이면 모델 score 순서를 뒤집지 않도록 slope를 0으로 제한하고 직전 양성률의 상수 확률을 사용했다.
- False positive 비용 1, false negative 비용 100을 가정했다. 보정된 불량 확률의 손익분기 threshold는 `1 / (1 + 100) = 0.00990099`로 모든 type과 구간에서 고정했다.

## 평가 방법

- 고정 모델 학습: W01~W06
- calibration과 평가:
  - W07 calibration → W08 평가
  - W08 calibration → W09 평가
  - W09 calibration → W10 평가
- 비교 정책:
  - raw score, threshold 0.5
  - raw score, 비용 threshold 0.00990099
  - calibrated probability, 비용 threshold 0.00990099
- 분류 지표: Slip Rate, False Call Reduction, TN/FP/FN/TP, Recall
- 확률 지표: Brier score, log loss, 평균 예측확률과 실제 양성률
- 비용: `FP × 1 + FN × 100`
- Test 기간: 1970-10-05 10:39:05 ~ 1970-11-02 14:21:28 UTC

## 주요 결과

### `kimjaehak_006` 재현

W09~W10 raw score, threshold 0.5에서 PR-AUC 0.315411과 Recall 0.316141을 재현했다.

### W08~W10 전체 정책 비교

| 정책 | Threshold | Slip Rate | Recall | False Call Reduction | TN | FP | FN | TP | 비용(1:100) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw score | 0.5 | 66.2655% | 33.7345% | 98.9167% | 113,768 | 1,246 | 1,707 | 869 | 171,946 |
| Raw score | 0.00990099 | 35.1320% | 64.8680% | 93.0374% | 107,006 | 8,008 | 905 | 1,671 | 98,508 |
| Calibrated probability | 0.00990099 | **25.5435%** | **74.4565%** | 80.1381% | 92,170 | 22,844 | 658 | 1,918 | **88,644** |

같은 비용 threshold에서 calibration은 raw 정책보다 FN을 247건 줄이고 비용을 9,864 낮췄다. 반면 FP는 14,836건 늘고 False Call Reduction은 12.90%p 감소했다.

Calibrated probability의 pooled PR-AUC는 0.141942로 raw score의 0.298083보다 낮았다. type마다 서로 다른 보정식을 적용하면 type 내부의 순서는 유지되더라도 type 사이 확률 순서가 바뀌므로, 이 값은 5개 모델을 합친 전체 행의 새로운 순위를 평가한 결과다. 희소 type의 상수확률 fallback은 내부 동률도 만든다. 따라서 calibration 채택 여부는 pooled PR-AUC 하나가 아니라 type별 순위와 Brier/log loss, 최종 TN·FN을 함께 봐야 한다.

### 구간별 calibrated 비용 정책

| 평가 구간 | Slip Rate | False Call Reduction | TN | FP | FN | TP | 비용(1:100) |
|---|---:|---:|---:|---:|---:|---:|---:|
| W08 | 29.3578% | 95.8474% | 37,253 | 1,614 | 96 | 231 | 11,214 |
| W09 | 44.1020% | 96.7142% | 36,999 | 1,257 | 415 | 526 | 42,757 |
| W10 | 11.2385% | 47.2883% | 17,918 | 19,973 | 147 | 1,161 | 34,673 |

세 구간 모두 Slip Rate 1% 목표에 크게 미달했다. 특히 직전 W08의 라벨로 보정한 W09에서 Slip Rate가 44.10%였다. W10에서는 Recall이 높아졌지만 재검사 절감이 47.29%로 급락했다.

### 확률 보정 품질

| 정책 | Brier score | Log loss | 평균 예측확률 | 실제 양성률 |
|---|---:|---:|---:|---:|
| Raw score | 0.020556 | 0.106902 | 2.1923% | 2.1907% |
| Calibrated probability | 0.022032 | **0.095347** | 2.1639% | 2.1907% |

전체 평균에서는 calibration이 log loss를 개선했지만 Brier score는 악화했다. 구간별로도 일관되지 않았다.

- W08 Brier: 0.009770 → 0.007471로 개선
- W09 Brier: 0.022200 → 0.023453으로 악화
- W10 Brier: 0.029695 → 0.035172로 악화
- W08 calibrated 평균 확률은 0.3420%로 실제 0.8343%를 과소추정했다.
- W09는 0.6198% 대 실제 2.4007%로 더 크게 과소추정했다.
- W10은 5.5296% 대 실제 3.3368%로 과대추정했다.

### 희소 type 처리

- type calibrator 갱신 9회, pooled fallback 5회, 과거 type calibrator 유지 1회였다.
- W08의 type 4는 fitted slope가 -0.175660으로 나왔다. 순위를 뒤집지 않도록 slope를 0으로 제한하고 W08 양성률 6.9606%의 상수 확률로 대체했다.
- 이 type 4 calibrator가 W09 평가에 사용됐고, W09 표본이 48행뿐이라 W10에도 유지됐다. 따라서 monotonic fallback은 type×평가구간 기준 2회 적용됐다.

## 결론

Platt calibration과 고정 비용 threshold는 raw 비용 정책보다 총비용을 약 10.0% 줄였지만, 프로젝트의 안전 목표인 Slip Rate 1%와는 큰 차이가 있었다. 확률 품질도 W08에서만 개선되고 W09~W10에서는 Brier score가 악화해 시간에 걸쳐 안정적이지 않았다.

비용 threshold `0.00990099`는 FP:FN 비용비율 1:100에서 기대비용을 최소화하기 위한 기준이지 Slip Rate 1%를 보장하는 기준이 아니다. 따라서 이 결과를 안전 정책으로 채택하지 않는다.

`kimjaehak_008`과 이번 실험 모두 고정된 W01~W06 모델로는 후반 drift에 안정적으로 대응하지 못했다. 계획한 조건부 다음 단계로, calibration 구간보다 앞선 데이터까지 expanding 또는 rolling 방식으로 모델을 재학습하고 같은 walk-forward 평가를 수행한다.

## 저장 모델

비교 실험이므로 모델 파일을 저장하지 않았다.

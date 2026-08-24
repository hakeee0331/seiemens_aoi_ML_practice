# 0825_kimjaehak_011_walk_forward_retraining

## 연결된 노트북

`notebooks/0825_kimjaehak_011_walk_forward_retraining.ipynb`

## 상태

완료

## 목적

`kimjaehak_008`의 직전 구간 threshold와 `kimjaehak_010`의 확률 calibration이 고정된 W01~W06 모델의 후반 drift에 안정적으로 대응하지 못했다. 이번 실험은 동일한 mapping 기반 type별 XGBoost를 expanding 또는 rolling 방식으로 재학습하면 다음 구간의 순위 성능과 안전 운영 지표가 개선되는지 검증한다.

## 이전 실험 대비 주요 변경사항

- 중복 제거, 10개 시간 window, `mapping.json` 기반 type별 피처와 XGBoost 설정은 이전 실험과 동일하다.
- 세 가지 학습 정책을 비교했다.
  - Fixed: 모든 fold에서 W01~W06
  - Expanding: W01부터 calibration 직전 window까지 누적
  - Rolling-6: calibration 직전의 최근 6개 window
- 각 fold의 모델 학습 데이터에는 calibration과 평가 window를 포함하지 않았다.
- 각 모델의 직전 calibration 구간에서 Slip Rate 1%를 만족하는 가장 높은 type별 threshold를 선택해 다음 구간에 적용했다.
- 양성 20개 또는 음성 100개 미만인 type은 threshold `0`으로 두어 전량 재검사했다.
- 재학습하면 raw score scale이 바뀔 수 있으므로 과거 모델의 threshold를 새 모델에 재사용하지 않았다.

## 평가 방법

| 평가 구간 | Fixed 학습 | Expanding 학습 | Rolling-6 학습 | Threshold 선택 |
|---|---|---|---|---|
| W08 | W01~W06 | W01~W06 | W01~W06 | W07 |
| W09 | W01~W06 | W01~W07 | W02~W07 | W08 |
| W10 | W01~W06 | W01~W08 | W03~W08 | W09 |

- 안전 지표: Slip Rate = `FN / (TP + FN)`
- 재검사 절감: False Call Reduction = `TN / (TN + FP)`
- 모델 순위: PR-AUC, ROC-AUC
- 비용: `FP × 1 + FN × 100`
- Test 기간: 1970-10-05 10:39:05 ~ 1970-11-02 14:21:28 UTC

동일한 학습 window 조합은 캐시해 중복 학습하지 않았다. 실제로는 5개 학습 기간 조합마다 type 모델 5개, 총 25개 모델을 학습했다.

## 주요 결과

### W08~W10 전체

| 학습 정책 | PR-AUC | Slip Rate | Recall | False Call Reduction | TN | FP | FN | TP | 비용(1:100) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Fixed | 0.298083 | **2.6398%** | **97.3602%** | 11.6925% | 13,448 | 101,566 | 68 | 2,508 | 108,366 |
| Expanding | **0.344535** | 2.9503% | 97.0497% | **18.4804%** | **21,255** | 93,759 | 76 | 2,500 | **101,359** |
| Rolling-6 | 0.320067 | 3.4550% | 96.5450% | 15.6833% | 18,038 | 96,976 | 89 | 2,487 | 105,876 |

Expanding은 Fixed보다 PR-AUC가 0.046452 높고 TN이 7,807건 많으며 비용이 7,007 낮았다. 그러나 FN도 8건 늘어 Slip Rate가 0.3105%p 악화했다. Rolling-6도 PR-AUC, TN과 비용은 Fixed보다 나았지만 FN이 21건 늘었다.

### 구간별 결과

| 평가 구간 | 정책 | PR-AUC | Slip Rate | False Call Reduction | TN | FN | 비용(1:100) |
|---|---|---:|---:|---:|---:|---:|---:|
| W08 | Fixed/Expanding/Rolling-6 | 0.278423 | **0.6116%** | 1.0266% | 399 | 2 | 38,668 |
| W09 | Fixed | 0.314224 | 2.2317% | 21.3038% | 8,150 | 21 | 32,206 |
| W09 | Expanding | 0.303211 | 4.1445% | **43.4468%** | 16,621 | 39 | **25,535** |
| W09 | Rolling-6 | **0.328431** | 3.9320% | 36.3603% | 13,910 | 37 | 28,046 |
| W10 | Fixed | 0.353813 | 3.4404% | **12.9292%** | **4,899** | 45 | 37,492 |
| W10 | Expanding | **0.503099** | **2.6758%** | 11.1768% | 4,235 | **35** | **37,156** |
| W10 | Rolling-6 | 0.429903 | 3.8226% | 9.8414% | 3,729 | 50 | 39,162 |

W08은 세 정책의 학습 기간이 모두 W01~W06이므로 결과가 완전히 일치해 구현 일관성을 확인했다. Expanding은 W10 PR-AUC를 크게 높이고 FN을 10건 줄였지만, W09에서는 오히려 FN이 18건 늘었다. 후반 데이터를 추가 학습하는 효과가 구간마다 달랐다.

### 안전 목표와 fallback

- W08 이후 어느 학습 정책도 구간 전체 Slip Rate 1%를 만족하지 못했다.
- type×평가구간 15개 중 1% 목표를 만족한 수는 Fixed 9개, Expanding 9개, Rolling-6 10개였다.
- 각 정책에서 희소 표본으로 threshold 0을 사용한 경우는 6회였다.
- 이 목표 충족 횟수에는 전량 재검사 fallback으로 Slip Rate 0%가 된 type도 포함된다. 따라서 횟수만으로 재검사 절감 효과를 의미하지 않는다.
- Expanding W10도 type 1/2/3의 Slip Rate가 각각 1.3783%/7.7703%/1.0791%로 목표를 초과했다.

## 결론

Expanding 재학습은 전체 PR-AUC, False Call Reduction과 비용을 개선해 모델 적응 관점에서는 가장 유망했다. 그러나 프로젝트의 우선 제약인 Slip Rate 1%를 안정적으로 만족하지 못했고, Fixed보다 전체 FN도 증가했다. 따라서 현재 threshold 규칙과 함께 안전 운영안으로 채택하지 않는다.

Rolling-6은 최근 데이터에 더 집중했지만 Expanding보다 PR-AUC, Slip Rate, False Call Reduction과 비용이 모두 열세여서 우선순위에서 제외한다.

세 실험을 합치면 다음과 같다.

1. `kimjaehak_008`: 직전 raw threshold만 갱신해도 미래 1% 안전성은 유지되지 않았다.
2. `kimjaehak_010`: type별 확률 calibration과 고정 비용 threshold는 비용을 줄였지만 안전 목표와 큰 차이가 있었다.
3. `kimjaehak_011`: Expanding 재학습은 순위와 비용을 개선했지만 threshold의 시간 전이 실패를 해결하지 못했다.

따라서 현재 데이터만으로 `Slip Rate ≤ 1%`와 의미 있는 재검사 절감을 동시에 보장하는 모델 정책은 찾지 못했다. 다음 단계에서는 평균적인 point estimate만으로 threshold를 고르지 말고, 양성 표본 수에 따른 불확실성을 반영한 upper confidence bound 또는 conformal risk control을 검토해야 한다. 이때도 희소 type은 전량 재검사 fallback을 유지해야 한다.

## 저장 모델

비교 실험이므로 모델 파일을 저장하지 않았다.

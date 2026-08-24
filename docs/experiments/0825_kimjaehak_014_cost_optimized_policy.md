# 0825_kimjaehak_014_cost_optimized_policy

## 연결된 노트북

`notebooks/0825_kimjaehak_014_cost_optimized_policy.ipynb`

## 상태

완료

## 목적

`kimjaehak_013`에서 비용 없이 선택한 Expanding 모델에 비용 기반 의사결정을 추가했을 때 다음 시간 구간의 총비용이 줄어드는지 검증한다.

실제 현장의 FP와 FN 비용은 아직 정해지지 않았다. 따라서 FP 비용을 1로 두고 FN 비용을 10, 25, 50, 100, 200으로 바꿔 민감도를 확인한다. 특정 1:100 가정만으로 결론을 정하지 않는다.

## 이전 실험 대비 주요 변경사항

- `kimjaehak_013`과 같은 Fixed 및 Expanding 모델, 학습 기간, 평가 기간을 사용했다.
- Expanding은 비용 결과를 보기 전에 `kimjaehak_013`의 주 지표로 선택했다.
- 각 모델이 직전 구간과 다음 구간에 낸 점수를 만들고, 비용 정책은 직전 구간에서만 정해 다음 구간에 고정 적용했다.
- 비용을 사용하지 않는 raw threshold 0.5와 전량 재검사를 두 기준선으로 추가했다.
- 비용 정책 세 가지를 사전에 정의했다.
  - `raw_empirical_cost`: 직전 구간에서 `FP + FN × 비용비율`을 직접 최소화하는 type별 raw threshold
  - `raw_guarded_cost`: 표본이 부족한 type은 전량 재검사하고 나머지만 empirical threshold 적용
  - `platt_analytic_cost`: 직전 구간에서 Platt calibration 후 이론적 비용 threshold 적용
- 비용 정책 간 최저값은 사후 관측 비교이며, 운영 정책을 미리 선택해 독립적으로 검증한 결과가 아니다.

## 평가 방법

| 평가 구간 | 모델 학습 | 비용 정책 선택 |
|---|---|---|
| W08 | Fixed / Expanding 모두 W01~W06 | W07 |
| W09 | Fixed W01~W06, Expanding W01~W07 | W08 |
| W10 | Fixed W01~W06, Expanding W01~W08 | W09 |

- 총비용: `FP × 1 + FN × FN 비용비율`
- 비용비율: FP:FN = 1:10, 1:25, 1:50, 1:100, 1:200
- 비교 기준: raw threshold 0.5, 전량 재검사
- 운영 trade-off 참고: FN, FP, Recall, Slip Rate, False Call Reduction
- Test 기간: 1970-10-05 10:39:05 ~ 1970-11-02 14:21:28 UTC

희소 type 기준은 직전 구간 양성 20개 미만 또는 음성 100개 미만이다. 이 기준에 해당한 type×모델×fold 조합은 12개였다. Platt calibration은 희소 type에 해당 fold의 pooled calibrator를 사용했고, 음수 slope 2회는 순위를 뒤집지 않도록 상수확률로 대체했다.

## 주요 결과

### 비용비율 1:100 전체 정책 비교

| 모델 | 정책 | 총비용 | FP | FN | Recall | False Call Reduction | Raw 0.5 대비 절감 |
|---|---|---:|---:|---:|---:|---:|---:|
| Fixed | Raw 0.5 | 171,946 | 1,246 | 1,707 | 33.73% | 98.92% | 기준 |
| Fixed | Raw empirical cost | 91,747 | 20,947 | 708 | 72.52% | 81.79% | 46.64% |
| Fixed | Raw guarded cost | 119,469 | 63,269 | 562 | 78.18% | 44.99% | 30.52% |
| Fixed | Platt analytic cost | **88,666** | 22,766 | 659 | 74.42% | 80.21% | **48.43%** |
| Fixed | All manual | 115,014 | 115,014 | 0 | 100.00% | 0.00% | 33.11% |
| Expanding | Raw 0.5 | 171,225 | 925 | 1,703 | 33.89% | 99.20% | 기준 |
| Expanding | Raw empirical cost | **69,627** | 16,627 | 530 | 79.43% | 85.54% | **59.34%** |
| Expanding | Raw guarded cost | 97,044 | 59,344 | 377 | 85.36% | 48.40% | 43.32% |
| Expanding | Platt analytic cost | 81,747 | 17,747 | 640 | 75.16% | 84.57% | 52.26% |
| Expanding | All manual | 115,014 | 115,014 | 0 | 100.00% | 0.00% | 32.83% |

1:100에서 Expanding + raw empirical 비용 정책은 raw 0.5보다 101,598, 전량 재검사보다 45,387 낮았다. 다음 구간별로도 raw 0.5와 전량 재검사를 각각 3/3회 이겼다.

동일한 raw empirical 정책끼리 비교하면 Fixed 91,747에서 Expanding 69,627로 22,120, 약 24.1% 감소했다. 동일한 Platt analytic 정책에서도 Fixed 88,666에서 Expanding 81,747로 약 7.8% 감소했다. 따라서 1:100의 비용 개선에는 Expanding 모델 자체의 개선과 비용 threshold의 추가 효과가 모두 존재한다.

### 비용비율 민감도

아래 표의 정책은 사전에 정의한 세 비용 정책 중 각 비용비율에서 사후 관측 총비용이 가장 낮았던 정책이다. 독립적인 정책 선택 결과가 아니라 민감도 요약이다.

| 모델 | 비용비율 | 관측상 최저 정책 | 총비용 | Raw 0.5 대비 절감 | Raw 0.5보다 낮은 구간 | All manual보다 낮은 구간 |
|---|---:|---|---:|---:|---:|---:|
| Expanding | 1:10 | Platt analytic | 17,729 | 1.26% | 1/3 | 3/3 |
| Expanding | 1:25 | Raw empirical | 29,097 | 33.11% | 2/3 | 3/3 |
| Expanding | 1:50 | Raw empirical | 46,200 | 46.33% | 3/3 | 3/3 |
| Expanding | 1:100 | Raw empirical | 69,627 | 59.34% | 3/3 | 3/3 |
| Expanding | 1:200 | Platt analytic | 108,172 | 68.33% | 3/3 | 1/3 |
| Fixed | 1:10 | Platt analytic | 22,404 | -22.32% | 0/3 | 3/3 |
| Fixed | 1:25 | Platt analytic | 38,741 | 11.79% | 3/3 | 3/3 |
| Fixed | 1:50 | Raw empirical | 54,835 | 36.68% | 3/3 | 3/3 |
| Fixed | 1:100 | Platt analytic | 88,666 | 48.43% | 3/3 | 2/3 |
| Fixed | 1:200 | Platt analytic | 129,623 | 62.17% | 3/3 | 1/3 |

Expanding은 모든 비용비율에서 관측상 최저 비용 정책이 aggregate raw 0.5와 전량 재검사보다 낮았다. 다만 1:10에서는 raw 0.5 대비 이득이 1.26%에 불과하고 1/3개 구간에서만 이겼다. 1:200에서는 aggregate로 전량 재검사보다 6,842 낮지만 구간별 승리는 1/3뿐이었다. 평균 비용 이득만으로 시간 안정성을 주장할 수 없는 이유다.

## 결론

후속 실험의 질문에 대한 답은 두 단계로 나뉜다.

1. `kimjaehak_013`: 비용을 전혀 사용하지 않아도 Expanding의 순위 성능이 Fixed보다 좋았다.
2. `kimjaehak_014`: Expanding의 같은 예측에 직전 구간 비용 threshold를 적용하면, 특히 1:50~1:100 가정에서 raw 0.5보다 다음 구간 비용이 반복적으로 낮았다.

따라서 비용 관점의 개선은 확인됐다. 특히 1:100에서 Expanding + raw empirical 정책은 raw 0.5 대비 59.34% 비용을 줄였고, 동일 비용 정책의 Fixed보다도 24.1% 낮았다.

하지만 아직 최종 운영 정책은 아니다.

- 실제 FP·FN 비용이 정해지지 않아 어느 비용비율을 채택할지 결정할 수 없다.
- 비용 정책 세 개 중 최저 정책은 평가 결과를 본 뒤 고른 사후 비교다.
- 평가 구간이 W08~W10 세 개뿐이며 희소 type fallback과 calibration 불안정성이 남아 있다.
- 1:100의 Expanding + raw empirical 정책도 FN 530건, Slip Rate 20.57%다. 비용 최소화는 낮은 Slip Rate를 자동으로 보장하지 않는다.

다음 단계는 현장 비용의 합의 가능한 범위를 먼저 정한 뒤 정책 하나를 고정하고, 새로운 미래 시간 구간에 단 한 번 적용해 비용과 FN을 확인하는 것이다. 안전상 허용 가능한 FN 상한이 있다면 비용 목적함수와 별도의 제약조건으로 함께 둬야 한다.

## 저장 모델

비교 실험이므로 모델 파일을 저장하지 않았다.

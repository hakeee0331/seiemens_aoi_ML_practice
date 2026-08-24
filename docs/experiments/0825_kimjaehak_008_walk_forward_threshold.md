# 0825_kimjaehak_008_walk_forward_threshold

## 연결된 노트북

`notebooks/0825_kimjaehak_008_walk_forward_threshold.ipynb`

## 상태

완료

## 목적

`kimjaehak_006`의 검사유형별 XGBoost 5개를 고정한 상태에서, 직전 시간 구간의 라벨로 선택한 `inspection_type`별 threshold가 다음 구간에서도 안전하게 작동하는지 walk-forward로 검증한다.

운영 목표는 실제 불량을 정상으로 통과시키는 Slip Rate를 1% 이하로 제한하면서, 실제 false call을 정상으로 분류해 수동 재검사를 줄이는 False Call Reduction을 최대화하는 것이다.

## 이전 실험 대비 주요 변경사항

- 데이터 로딩, 중복 제거, `mapping.json` 기반 type별 피처와 XGBoost 설정은 `kimjaehak_006`과 동일하게 유지했다.
- 전체 기간을 timestamp-group 기준 W01~W10으로 나눴다.
- 모델 5개는 W01~W06으로 한 번만 학습하고 이후에는 재학습하지 않았다.
- threshold는 W07에서 선택해 W08에 적용하고, W08→W09, W09→W10 순서로 갱신했다.
- 각 type의 직전 구간에서 `Slip Rate ≤ 1%`를 만족하는 가장 높은 threshold를 선택했다. threshold가 높을수록 TN이 단조롭게 증가하므로, 이는 안전 제약 안에서 TN을 최대화하는 선택이다.
- 직전 구간의 양성이 20개 미만이거나 음성이 100개 미만이면 새 threshold를 추정하지 않았다. 첫 구간에는 `0`을 사용해 전량 재검사하고, 이후에는 직전 threshold를 유지했다.
- 미래 평가 구간의 라벨은 threshold 선택에 사용하지 않았다.

## 평가 방법

- 고정 모델 학습: W01~W06
- threshold 선택과 다음 구간 평가:
  - W07 선택 → W08 평가
  - W08 선택 → W09 평가
  - W09 선택 → W10 평가
- 비교 정책:
  - 고정 threshold `0.5`
  - 직전 구간의 type별 walk-forward threshold
- 주요 지표:
  - Slip Rate = `FN / (TP + FN)`
  - False Call Reduction = `TN / (TN + FP)`
  - TN, FN, Recall, PR-AUC
- Test 기간: 1970-10-05 10:39:05 ~ 1970-11-02 14:21:28 UTC

## 주요 결과

### `kimjaehak_006` 재현

기존 Test 구간인 W09~W10에서 고정 threshold 0.5를 적용한 결과가 재현됐다.

| PR-AUC | Recall | TN | FP | FN | TP |
|---:|---:|---:|---:|---:|---:|
| 0.315411 | 0.316141 | 75,192 | 955 | 1,538 | 711 |

### 구간별 정책 비교

| 평가 구간 | 정책 | Slip Rate | False Call Reduction | TN | FN |
|---|---|---:|---:|---:|---:|
| W08 | 고정 0.5 | 51.6820% | 99.2513% | 38,576 | 169 |
| W08 | Walk-forward type threshold | **0.6116%** | 1.0266% | 399 | 2 |
| W09 | 고정 0.5 | 70.4570% | 98.9779% | 37,865 | 663 |
| W09 | Walk-forward type threshold | **2.2317%** | 21.3038% | 8,150 | 21 |
| W10 | 고정 0.5 | 66.8960% | 98.5115% | 37,327 | 875 |
| W10 | Walk-forward type threshold | **3.4404%** | 12.9292% | 4,899 | 45 |

W08에서는 전체 Slip Rate 1% 목표를 만족했지만 W09와 W10에서는 실패했다. 직전 구간에서 만족한 제약이 다음 구간에 자동으로 전달되지 않았다.

### W08~W10 전체 비교

| 정책 | PR-AUC | Slip Rate | Recall | False Call Reduction | TN | FP | FN | TP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 고정 0.5 | 0.298083 | 66.2655% | 33.7345% | 98.9167% | 113,768 | 1,246 | 1,707 | 869 |
| Walk-forward type threshold | 0.298083 | **2.6398%** | **97.3602%** | 11.6925% | 13,448 | 101,566 | 68 | 2,508 |

모델과 확률은 같으므로 PR-AUC는 두 정책에서 동일하다. Walk-forward threshold는 고정 0.5보다 FN을 1,639건 줄였지만, 동시에 TN도 100,320건 줄였다.

### threshold 갱신 안정성

- type×구간 threshold 결정 15회 중 표본 조건을 만족해 새로 갱신한 경우는 9회였다.
- 초기 안전 fallback 또는 직전 값 유지가 6회였다.
- type×평가구간 15개 중 실제 다음 구간에서 Slip Rate 1%를 만족한 경우는 9개였다.
- W09에서는 type 1의 Slip Rate가 2.2901%, type 3이 4.6154%였다.
- W10에서는 type 0/1/2/3이 각각 2.9412%/1.5314%/6.4189%/5.0360%로 목표를 초과했다.
- type 4는 W09의 음성 표본이 35개뿐이라 W10 threshold를 갱신하지 않고 W08에서 선택한 값을 유지했다. W10에서는 전량 재검사되어 Slip Rate 0%, False Call Reduction 0%였다.

## 결론

직전 구간에서 type별 threshold를 직접 선택하는 방식은 고정 0.5보다 불량 미검출을 크게 줄였지만, 다음 구간의 Slip Rate 1%를 안정적으로 보장하지 못했다. 시간에 따라 라벨률과 모델 점수 분포가 변하기 때문에 W08에서 안전했던 score 경계가 W09와 W10에서는 같은 의미를 갖지 않았다.

또한 전체 Slip Rate를 2.64%까지 낮추는 동안 False Call Reduction이 11.69%에 그쳤다. 안전성을 높이기 위해 재검사 절감 효과 대부분을 포기했는데도 목표를 달성하지 못했으므로 이 정책을 운영안으로 채택하지 않는다.

다음 독립 실험에서는 고정 모델의 type별 raw score를 확률로 calibration하고, type·구간마다 다시 최적화한 threshold 대신 비용비율로 사전에 고정한 확률 threshold를 적용한다. 이를 통해 raw score 경계의 시간 불안정성과 확률 보정의 효과를 분리해 검증한다.

## 저장 모델

비교 실험이므로 모델 파일을 저장하지 않았다.

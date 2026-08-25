# 0825_peace_015_type_expert_sensor_anomaly_features

## 연결된 노트북

`notebooks/0825_peace_015_type_expert_sensor_anomaly_features.ipynb`

## 상태

완료

## 목적

`0825_peace_004_type_expert_walk_forward`의 분할, XGBoost 파라미터, 임계값 선택 규칙은 그대로 두고, 타입별 mapped sensor에 Train-only robust z 기반 센서 이상도 집계 피처 5개만 추가했을 때 미래 Recall/FCR 안정성과 Validation 성능이 개선되는지 확인한다.

## 주요 변경사항

- 타입별 `inspection_feat`에 아래 5개 파생 변수를 추가했다.
  - `sensor_max_abs_robust_z`
  - `sensor_mean_abs_robust_z`
  - `sensor_p95_abs_robust_z`
  - `sensor_abnormal_count_2`
  - `sensor_abnormal_count_3`
- median, MAD, scale은 각 Fold와 최종 Validation 학습에서 해당 Train 구간으로만 추정했다.
- `004`와 동일한 3-Fold expanding Walk-forward와 0~70% Train / 70~80% Validation 구조를 유지했다.
- 후보 비교 단계이므로 80~100% Test는 추론하지 않았다.

## Walk-forward 결과

| 전략 | 평균 PR-AUC | 평균 Recall | 최저 Recall | Recall 99% 달성 Fold | 평균 False Call Reduction |
|---|---:|---:|---:|---:|---:|
| 고정 0.5 | 0.060189 | 0.079184 | 0.032895 | 0/3 | 0.997696 |
| 공통 임계값 | 0.060189 | 0.967105 | 0.901316 | 2/3 | 0.194477 |
| 타입별 임계값 | 0.060189 | 0.920474 | 0.782895 | 1/3 | 0.332762 |

## 004 대비 비교

- Walk-forward 공통 임계값 평균 Recall: `0.969298 -> 0.967105`로 소폭 하락
- Walk-forward 공통 임계값 평균 FCR: `0.169449 -> 0.194477`로 개선
- Validation 공통 임계값 Recall: `0.991597 -> 0.991597`로 동일
- Validation 공통 임계값 FCR: `0.699398 -> 0.690101`로 소폭 하락
- Validation PR-AUC: `0.449656 -> 0.491343`로 개선

## Validation 결과

| 전략 | PR-AUC | Recall | False Call Reduction | TP | FN | FP | TN |
|---|---:|---:|---:|---:|---:|---:|---:|
| 고정 0.5 | 0.491343 | 0.417367 | 0.998099 | 149 | 208 | 83 | 43,586 |
| 공통 임계값 | 0.491343 | 0.991597 | 0.690101 | 354 | 3 | 13,533 | 30,136 |
| 타입별 임계값 | 0.491343 | 0.994398 | 0.553367 | 355 | 2 | 19,504 | 24,165 |

## 결론 및 다음 단계

- 센서 이상도 집계는 PR-AUC를 확실히 올렸지만, 운영 기준으로 중요하게 보던 공통 임계값 Validation FCR은 `004`보다 약간 낮아졌다.
- Walk-forward 공통 임계값 평균 FCR은 개선됐지만 평균 Recall은 미세하게 하락했고, 최저 Recall도 `90.1%`라서 99% 안정성 문제는 그대로 남아 있다.
- 타입별 임계값 전략도 `004`보다 의미 있는 개선을 만들지 못했다.
- 결론적으로 센서 이상도 피처는 “랭킹 품질 개선”은 보였지만, 현재 목표인 high-recall 운영 성능 개선은 제한적이다.

## 저장 모델

해당 없음. 후보 비교 단계로 Validation까지만 평가했다.

## 실행 로그

`docs/peace/0825_peace_015_type_expert_sensor_anomaly_features.log`

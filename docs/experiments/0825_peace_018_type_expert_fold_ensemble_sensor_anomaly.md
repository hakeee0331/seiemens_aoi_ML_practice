# 0825_peace_018_type_expert_fold_ensemble_sensor_anomaly

## 연결된 노트북

`notebooks/0825_peace_018_type_expert_fold_ensemble_sensor_anomaly.ipynb`

## 상태

완료

## 목적

`0825_peace_005_type_expert_fold_ensemble`의 시간순 분할, XGBoost 파라미터, 체크포인트 앙상블과 임계값 규칙을 고정하고 `0825_peace_015_type_expert_sensor_anomaly_features`의 센서 이상도 파생변수 5개만 추가했을 때 Recall 99% 제약의 미래 안정성과 FCR이 개선되는지 확인한다.

## 주요 변경사항

- 005와 같은 0~30%, 0~40%, 0~50%, 0~70% 누적 체크포인트에서 타입별 XGBoost 5개를 학습했다.
- 각 체크포인트의 타입별 Train에서만 mapped sensor의 median/MAD를 계산했다.
- `max_abs_z`, `mean_abs_z`, `p95_abs_z`, `abnormal_count_2`, `abnormal_count_3` 5개를 추가했다.
- Fold 1/2/3은 각각 1/2/3개 체크포인트 확률을 동일 가중 평균했다.
- 최종 Validation은 4개 체크포인트 확률을 평균했다.
- 후보 선택 단계이므로 80~100% Test는 추론하지 않았다.

## Walk-forward 결과

| 전략 | 평균 PR-AUC | 평균 Recall | 최저 Recall | Recall 99% 달성 Fold | 평균 False Call Reduction |
|---|---:|---:|---:|---:|---:|
| 고정 0.5 | 0.063709 | 0.064058 | 0.013158 | 0/3 | 0.997855 |
| 공통 임계값 | 0.063709 | 0.954172 | 0.888158 | 1/3 | 0.205068 |
| 타입별 임계값 | 0.063709 | 0.933632 | 0.822368 | 1/3 | 0.340961 |

## 005 대비 비교

- Walk-forward 공통 임계값 평균 Recall: `0.986842 -> 0.954172` (`-3.27%p`)
- Walk-forward 최저 Recall: `0.960526 -> 0.888158` (`-7.24%p`)
- Recall 99% 달성 Fold: `2/3 -> 1/3`
- Walk-forward 평균 FCR: `0.176359 -> 0.205068` (`+2.87%p`)
- Validation PR-AUC: `0.382650 -> 0.389631` (`+0.006981`)
- Validation 공통 임계값 FCR: `0.611074 -> 0.529208` (`-8.19%p`)

## Validation 결과

| 전략 | PR-AUC | Recall | False Call Reduction | TP | FN | FP | TN |
|---|---:|---:|---:|---:|---:|---:|---:|
| 고정 0.5 | 0.389631 | 0.168067 | 0.999359 | 60 | 297 | 28 | 43,641 |
| 공통 임계값 | 0.389631 | 0.991597 | 0.529208 | 354 | 3 | 20,559 | 23,110 |
| 타입별 임계값 | 0.389631 | 0.994398 | 0.600472 | 355 | 2 | 17,447 | 26,222 |

## 결론 및 다음 단계

- PR-AUC와 Walk-forward 평균 FCR은 소폭 개선됐지만, 핵심 목표인 미래 Recall 안정성은 크게 악화됐다.
- Validation에서 Recall을 동일하게 99.16%로 맞춰도 FP가 `16,984 -> 20,559`로 3,575개 증가했다.
- 따라서 센서 이상도 5개 전체를 005 Fold 앙상블에 추가하는 구성은 채택하지 않는다.
- 005를 Champion으로 유지하고, 추가 분석이 필요하면 편차 요약 3개와 이상 센서 개수 2개를 분리해 어느 그룹이 Recall을 악화시키는지만 진단할 수 있다.

## 저장 모델

해당 없음. 후보 비교 단계로 Validation까지만 평가했다.

## 실행 로그

`docs/peace/0825_peace_018_type_expert_fold_ensemble_sensor_anomaly.log`

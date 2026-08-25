# 0825_peace_011_type_expert_fold_ensemble_time_weight

## 연결된 노트북

`notebooks/0825_peace_011_type_expert_fold_ensemble_time_weight.ipynb`

## 상태

완료

## 목적

실행 완료된 `0825_peace_005_type_expert_fold_ensemble`의 시간 분할, 체크포인트 구성, 타입별 유효 피처, XGBoost 파라미터, 확률 평균 방식, 임계값 선택, 최종 Validation/Test 평가 절차를 그대로 유지한 채, 각 체크포인트×타입 학습에만 train-local 시간순 `sample_weight 1.0→2.0`를 추가했을 때 성능 변화가 있는지 확인한다.

## 주요 변경사항

- 베이스라인은 `005` Fold 앙상블이며, 0.30 / 0.40 / 0.50 / 0.70 누적 체크포인트와 Fold별 멤버 구성은 그대로 유지했다.
- 모델링 변경은 체크포인트별 타입 학습 `model.fit(..., sample_weight=...)` 하나뿐이며, 클래스 가중치와 추가 파라미터 변경은 적용하지 않았다.
- 각 학습에서 earliest timestamp는 1.0, latest timestamp는 2.0이 되도록 선형 시간 가중치를 만들고 `time_weight_min`, `time_weight_max`, `time_weight_mean`, `time_weight_degenerate`를 모두 기록했다.
- 실행된 20개 체크포인트×타입 학습 전부에서 실제 가중치 범위는 1.0~2.0이었고 `time_weight_degenerate=False`였다.
- 확률 결합은 `005`와 동일하게 Fold 1/2/3에서는 1/2/3개 체크포인트 평균, 최종 Validation/Test에서는 4개 체크포인트 평균을 사용했다.
- 실행 로그는 `docs/peace/0825_peace_011_type_expert_fold_ensemble_time_weight.log`에 저장했다.

## 데이터 분할

| 구분 | 시간 비율 | 행 수 | 실제 불량 수 |
|---|---:|---:|---:|
| Train | 0~70% | 308,196 | 1,940 |
| Validation | 70~80% | 44,026 | 357 |
| Test | 80~100% | 88,052 | 2,325 |

## 시간 가중치 요약

모든 체크포인트×타입 학습에서 `sample_weight`는 train 내부 timestamp만 사용해 계산했다.

| 체크포인트 | 시간 가중치 평균 범위 | 비고 |
|---|---:|---|
| 0.30 | 1.444547 ~ 1.593579 | 5개 타입 모두 `time_weight_degenerate=False` |
| 0.40 | 1.520408 ~ 1.671896 | 5개 타입 모두 `time_weight_degenerate=False` |
| 0.50 | 1.416470 ~ 1.578101 | 5개 타입 모두 `time_weight_degenerate=False` |
| 0.70 | 1.482090 ~ 1.580274 | 5개 타입 모두 `time_weight_degenerate=False` |

## Walk-forward 결과

| 전략 | 평균 PR-AUC | 평균 Recall | 최저 Recall | Recall 99% 달성 Fold | 평균 False Call Reduction |
|---|---:|---:|---:|---:|---:|
| 고정 0.5 | 0.073065 | 0.092624 | 0.039474 | 0/3 | 0.997810 |
| 공통 임계값 | 0.073065 | 0.967330 | 0.927632 | 1/3 | 0.181664 |
| 타입별 임계값 | 0.073065 | 0.936699 | 0.822368 | 1/3 | 0.342694 |

## 최종 Test 결과

공통·타입별 임계값은 Test가 아닌 70~80% Validation에서 선택했다.

| 전략 | Threshold | PR-AUC | Recall | False Call Reduction | TP | FN | FP | TN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 고정 | 0.500000 | 0.390438 | 0.188387 | 0.997970 | 438 | 1,887 | 174 | 85,553 |
| 공통 | 0.000473 | 0.390438 | 0.939355 | 0.433119 | 2,184 | 141 | 48,597 | 37,130 |
| 타입별 | 유형별 | 0.390438 | 0.924731 | 0.511542 | 2,150 | 175 | 41,874 | 43,853 |

## 005 / 008 비교

| 실험 | 구조 | Test PR-AUC | 공통 Threshold Recall | 공통 Threshold FCR | 타입별 Threshold Recall | 타입별 Threshold FCR |
|---|---|---:|---:|---:|---:|---:|
| `005` | Fold 앙상블 | 0.382545 | 0.939355 | 0.520361 | 0.932903 | 0.476734 |
| `008` | 단일 모델 + 시간 가중치 | 0.371587 | 0.908387 | 0.497720 | 0.941935 | 0.312574 |
| `011` | Fold 앙상블 + 시간 가중치 | 0.390438 | 0.939355 | 0.433119 | 0.924731 | 0.511542 |

- `011`의 Test PR-AUC는 `005` 대비 +0.007893, `008` 대비 +0.018851 높았다.
- 공통 임계값 Test Recall은 `005`와 동일한 93.94%였지만, FCR은 `005`의 52.04%에서 `011`의 43.31%로 하락했다.
- 타입별 임계값 Test Recall은 `005`보다 0.82%p 낮아졌지만, FCR은 3.48%p 높아졌다.
- `008`과 비교하면 `011`은 공통 임계값 Recall은 3.10%p 높지만 FCR은 6.46%p 낮았고, 타입별 임계값은 Recall이 1.72%p 낮지만 FCR은 19.90%p 높았다.
- Walk-forward 공통 임계값 평균 Recall은 `005` 98.68% > `008` 97.59% > `011` 96.73% 순으로, 미래 안정성은 오히려 약해졌다.

## 실행 및 무결성 검증

- 실행 명령: `/opt/anaconda3/bin/jupyter nbconvert --to notebook --execute --inplace notebooks/0825_peace_011_type_expert_fold_ensemble_time_weight.ipynb`
- 실행 환경 로그: Python 3.12.7, pandas 2.2.2, scikit-learn 1.5.1, xgboost 3.4.1
- `dataset.csv` SHA-256: `53e8568743216d556856ed69b388f6750fbfa0b8c59ad31f970515ac9eb10e62`
- `mapping.json` SHA-256: `3b20f440b6d9ed0baefa662e1a6f03688befbe0f28341a3b54655d3058c6e486`
- 실행 전후 데이터/매핑 해시는 동일했고, 노트북 verification 출력에서도 `dataset_sha256_unchanged=True`, `mapping_sha256_unchanged=True`를 확인했다.
- 노트북 metadata의 kernel spec과 Python version은 `005`와 동일했다.
- `005`와 `011`의 셀 source hash 비교 결과, 변경된 셀은 실험 ID/시간 가중치/결론에 해당하는 0, 2, 13, 14, 20, 21번뿐이고 나머지 셀 source hash는 모두 동일했다.
- 실행된 노트북에 error output은 없었다.

## 결론 및 다음 단계

- 시간 가중치를 Fold 앙상블에 넣자 Test PR-AUC는 세 비교군(`005`, `008`, `011`) 중 가장 높아졌다.
- 그러나 공통 임계값 운영에서는 Recall 이득 없이 FP가 늘어 `005`보다 False Call Reduction이 눈에 띄게 악화됐다.
- 반대로 타입별 임계값 운영에서는 Recall을 조금 희생하는 대신 `005`보다 FCR이 높아져, 비용 절감 측면에서는 이쪽이 더 낫다.
- Test PR-AUC와 타입별 FCR만 보면 `011`이 높지만, Walk-forward 평균·최저 Recall과 공통 임계값 FCR은 `005`가 더 높다.
- 최악 미래 Recall과 공통 임계값 운영 효율을 우선하는 현재 선택 기준에 따라 **내부 Champion은 `005` Fold 앙상블로 유지**한다.

## 저장 모델

해당 없음. 이 실험은 Fold 앙상블에 시간 가중치를 추가했을 때의 성능 변화 검증용이며 모델 파일은 저장하지 않았다.

## 실행 로그

`docs/peace/0825_peace_011_type_expert_fold_ensemble_time_weight.log`

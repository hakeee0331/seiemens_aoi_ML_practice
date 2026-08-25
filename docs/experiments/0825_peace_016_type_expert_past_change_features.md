# 0825_peace_016_type_expert_past_change_features

## 연결된 노트북

`notebooks/0825_peace_016_type_expert_past_change_features.ipynb`

## 상태

완료

## 목적

`0825_peace_004_type_expert_walk_forward`의 학습 구조는 유지하고, 같은 타입의 과거 관측 대비 변화량을 정규화한 집계 피처 5개만 추가했을 때 시간 후반부 불량률 변화에 더 잘 적응하는지 확인한다.

## 주요 변경사항

- 타입별 `inspection_feat`에 아래 5개 파생 변수를 추가했다.
  - `delta_norm_mean`
  - `delta_abs_mean`
  - `delta_abs_max`
  - `delta_jump_count_2`
  - `delta_positive_ratio`
- 변화량의 중심과 scale은 각 Fold/최종 Train에서만 추정했다.
- 직전 동일 타입 관측을 사용한 causal feature로 구성해 미래 정보는 사용하지 않았다.
- `004`와 동일한 3-Fold expanding Walk-forward와 0~70% Train / 70~80% Validation 구조를 유지했다.
- 후보 비교 단계이므로 80~100% Test는 추론하지 않았다.

## Walk-forward 결과

| 전략 | 평균 PR-AUC | 평균 Recall | 최저 Recall | Recall 99% 달성 Fold | 평균 False Call Reduction |
|---|---:|---:|---:|---:|---:|
| 고정 0.5 | 0.062829 | 0.065595 | 0.019737 | 0/3 | 0.996923 |
| 공통 임계값 | 0.062829 | 0.975877 | 0.927632 | 2/3 | 0.175342 |
| 타입별 임계값 | 0.062829 | 0.937870 | 0.828947 | 1/3 | 0.305408 |

## 004 대비 비교

- Walk-forward 공통 임계값 평균 Recall: `0.969298 -> 0.975877`로 개선
- Walk-forward 공통 임계값 평균 FCR: `0.169449 -> 0.175342`로 소폭 개선
- Validation 공통 임계값 Recall: `0.991597 -> 0.991597`로 동일
- Validation 공통 임계값 FCR: `0.699398 -> 0.618310`로 크게 하락
- Validation PR-AUC: `0.449656 -> 0.456411`로 소폭 개선

## Validation 결과

| 전략 | PR-AUC | Recall | False Call Reduction | TP | FN | FP | TN |
|---|---:|---:|---:|---:|---:|---:|---:|
| 고정 0.5 | 0.456411 | 0.378151 | 0.997664 | 135 | 222 | 102 | 43,567 |
| 공통 임계값 | 0.456411 | 0.991597 | 0.618310 | 354 | 3 | 16,668 | 27,001 |
| 타입별 임계값 | 0.456411 | 0.994398 | 0.449999 | 355 | 2 | 24,018 | 19,651 |

## 결론 및 다음 단계

- 과거 변화량 피처는 Walk-forward 평균 Recall과 평균 FCR을 동시에 조금 올렸지만, Validation 공통 임계값 FCR이 크게 악화됐다.
- 즉 미래 Fold에서는 약간 좋아 보였지만, 실제 최종 Validation 운영 구간에서는 false call 감소 성능이 약해졌다.
- 현재 목표가 recall 99% 근처에서 FCR을 높이는 것이라면 이 실험은 채택하기 어렵다.
- 시간 변화량 자체는 신호가 있을 수 있으나, 지금 구현 방식으로는 후반부 운영 구간에서 안정적 이득을 주지 못했다.

## 저장 모델

해당 없음. 후보 비교 단계로 Validation까지만 평가했다.

## 실행 로그

`docs/peace/0825_peace_016_type_expert_past_change_features.log`

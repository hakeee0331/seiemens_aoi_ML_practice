# 0825_peace_017_type_expert_typewise_meta_removal

## 연결된 노트북

`notebooks/0825_peace_017_type_expert_typewise_meta_removal.ipynb`

## 상태

완료

## 목적

타입마다 `meta_feat1~4`가 실제 도움이 되는지 다를 수 있다는 가정으로, `0825_peace_004_type_expert_walk_forward`를 기준으로 타입별 `with_meta` / `without_meta`를 Walk-forward에서 비교하고 Validation까지 재검증한다.

## 주요 변경사항

- 각 타입마다 `with_meta`와 `without_meta` 두 변형을 모두 학습했다.
- 타입별 선택 기준은 Walk-forward 평균 PR-AUC를 1순위로, threshold 적용 후 Recall/FCR을 보조 기준으로 사용했다.
- 선택된 타입별 구성으로 다시 Walk-forward 요약과 최종 Validation 지표를 계산했다.
- 80~100% Test는 추론하지 않았다.

## 타입별 선택 결과

| inspection_type | 선택된 variant | Walk-forward 평균 PR-AUC | Walk-forward 평균 threshold Recall | Walk-forward 평균 threshold FCR |
|---|---|---:|---:|---:|
| 0 | with_meta | 0.011260 | 0.837143 | 0.495735 |
| 1 | without_meta | 0.192255 | 0.998208 | 0.133423 |
| 2 | without_meta | 0.266289 | 0.979167 | 0.092125 |
| 3 | without_meta | 0.258622 | 0.695652 | 0.446060 |
| 4 | with_meta | 0.005226 | 1.000000 | 0.000000 |

선택 결과는 `type 0, 4 = with_meta`, `type 1, 2, 3 = without_meta`였다.

## Walk-forward 결과

| 전략 | 평균 PR-AUC | 평균 Recall | 최저 Recall | Recall 99% 달성 Fold | 평균 False Call Reduction |
|---|---:|---:|---:|---:|---:|
| 고정 0.5 | 0.094335 | 0.218504 | 0.144737 | 0/3 | 0.995025 |
| 공통 임계값 | 0.094335 | 0.962719 | 0.888158 | 2/3 | 0.171798 |
| 타입별 임계값 | 0.094335 | 0.932314 | 0.809211 | 1/3 | 0.308326 |

## 004 대비 비교

- Walk-forward 공통 임계값 평균 Recall: `0.969298 -> 0.962719`로 하락
- Walk-forward 공통 임계값 평균 FCR: `0.169449 -> 0.171798`로 소폭 개선
- Validation 공통 임계값 Recall: `0.991597 -> 0.991597`로 동일
- Validation 공통 임계값 FCR: `0.699398 -> 0.626463`로 하락
- Validation PR-AUC: `0.449656 -> 0.471722`로 개선

## Validation 결과

| 전략 | PR-AUC | Recall | False Call Reduction | TP | FN | FP | TN |
|---|---:|---:|---:|---:|---:|---:|---:|
| 고정 0.5 | 0.471722 | 0.364146 | 0.998351 | 130 | 227 | 72 | 43,597 |
| 공통 임계값 | 0.471722 | 0.991597 | 0.626463 | 354 | 3 | 16,312 | 27,357 |
| 타입별 임계값 | 0.471722 | 0.994398 | 0.490462 | 355 | 2 | 22,251 | 21,418 |

## 결론 및 다음 단계

- 타입별 meta 제거는 세 후보 중 Validation PR-AUC가 가장 높았고, type 1/2/3에서는 meta를 빼는 편이 더 좋았다.
- 하지만 핵심 운영 지표인 공통 임계값 Validation FCR은 `004`보다 꽤 낮아졌다.
- 즉 meta 제거는 “확률 순위 품질”은 올렸지만, 99% recall 제약 아래의 false call 감소 성능은 개선하지 못했다.
- 향후 이 아이디어를 재사용한다면, 현재처럼 전면 후보로 채택하기보다는 type 1/2/3만 부분 반영한 뒤 별도 threshold 정책과 함께 재검증하는 편이 맞다.

## 저장 모델

해당 없음. 후보 비교 단계로 Validation까지만 평가했다.

## 실행 로그

`docs/peace/0825_peace_017_type_expert_typewise_meta_removal.log`

# 0825_kimjaehak_013_cost_free_model_performance

## 연결된 노트북

`notebooks/0825_kimjaehak_013_cost_free_model_performance.ipynb`

## 상태

완료

## 목적

`kimjaehak_011`에서는 재학습 방식과 Slip Rate 기반 threshold를 동시에 비교했다. 이 때문에 비용 감소가 모델 자체의 순위 개선에서 왔는지, threshold 변화에서 왔는지 분리하기 어려웠다.

이번 실험은 비용, threshold, confusion matrix를 모델 선택에서 완전히 제외하고 Fixed, Expanding, Rolling-6의 순위 성능과 확률 품질만 비교한다. 여기서 선택한 모델 구조를 다음 `kimjaehak_014`의 비용 정책 실험에 고정한다.

## 이전 실험 대비 주요 변경사항

- 중복 제거, 10개 시간 window, `mapping.json` 기반 type별 피처와 XGBoost 설정은 `kimjaehak_011`과 동일하다.
- 비용비율, threshold, TP/FP/FN/TN, Slip Rate, False Call Reduction을 모델 선택에 사용하지 않았다.
- calibration에 사용할 수 있는 직전 window는 학습에서 제외했다. 따라서 다음 `kimjaehak_014`가 완전히 같은 모델 예측을 사용할 수 있다.
- 검사유형마다 서로 다른 모델의 raw score 척도가 다를 수 있으므로 pooled PR-AUC는 보조 지표로 두었다.
- 주 지표는 각 검사유형 PR-AUC를 해당 유형의 실제 불량 수로 가중한 `positive-weighted type PR-AUC`의 W08~W10 평균이다.

## 평가 방법

| 평가 구간 | 직전 구간 | Fixed 학습 | Expanding 학습 | Rolling-6 학습 |
|---|---|---|---|---|
| W08 | W07 | W01~W06 | W01~W06 | W01~W06 |
| W09 | W08 | W01~W06 | W01~W07 | W02~W07 |
| W10 | W09 | W01~W06 | W01~W08 | W03~W08 |

- 주 지표: 평가 구간별 positive-weighted type PR-AUC의 평균
- 보조 순위 지표: macro type PR-AUC, pooled PR-AUC, ROC-AUC
- 확률 지표: Brier score, log loss
- Test 기간: 1970-10-05 10:39:05 ~ 1970-11-02 14:21:28 UTC
- 동일한 학습 window 조합을 캐시해 5개 학습 기간 조합 × 5개 type, 총 25개 모델을 학습했다.

W08은 세 방식이 모두 W01~W06을 학습하므로 예측이 완전히 같음을 확인했다.

## 주요 결과

### W08~W10 요약

| 학습 방식 | 평균 positive-weighted type PR-AUC | 평균 macro type PR-AUC | Aggregate pooled PR-AUC | Aggregate Brier | Aggregate log loss |
|---|---:|---:|---:|---:|---:|
| Fixed | 0.404530 | 0.227814 | 0.298083 | 0.020556 | 0.106902 |
| Expanding | **0.472470** | **0.264495** | **0.344535** | **0.018689** | **0.100548** |
| Rolling-6 | 0.445486 | 0.245866 | 0.320067 | 0.018792 | 0.109278 |

Expanding은 Fixed보다 주 지표가 0.067940 높았고, aggregate pooled PR-AUC도 0.046452 높았다. Brier와 log loss도 함께 개선됐다. Rolling-6도 순위는 Fixed보다 좋았지만 Expanding보다 낮았고 log loss는 세 방식 중 가장 나빴다.

### 평가 구간별 결과

| 평가 구간 | 방식 | Positive-weighted type PR-AUC | Pooled PR-AUC | Brier | Log loss |
|---|---|---:|---:|---:|---:|
| W08 | Fixed / Expanding / Rolling-6 | 0.458541 | 0.278423 | 0.009770 | 0.048659 |
| W09 | Fixed | 0.388373 | **0.314224** | 0.022200 | **0.114493** |
| W09 | Expanding | **0.451414** | 0.303211 | 0.023964 | 0.115340 |
| W09 | Rolling-6 | 0.439031 | 0.328431 | **0.021941** | 0.115323 |
| W10 | Fixed | 0.366676 | 0.353813 | 0.029695 | 0.157546 |
| W10 | Expanding | **0.507455** | **0.503099** | **0.022332** | **0.137638** |
| W10 | Rolling-6 | 0.438885 | 0.429903 | 0.024663 | 0.163846 |

Expanding은 재학습 효과가 생기는 W09와 W10 모두 주 지표에서 Fixed를 이겼다. W09에서는 type별 PR-AUC가 개선됐는데도 pooled PR-AUC가 하락했다. 이는 서로 다른 type 모델의 raw score를 한 줄로 합친 pooled 순위가 type 간 점수 스케일 변화의 영향을 받기 때문이다. W10에서는 type별 지표와 pooled 지표가 모두 크게 개선됐다.

## 결론

비용이나 threshold를 보지 않아도 Expanding이 세 방식 중 가장 좋은 모델 후보였다. 따라서 `kimjaehak_011`에서 관찰한 Expanding의 개선은 threshold 효과만이 아니라 모델의 불량 순위화 능력 개선도 포함한다.

다음 `kimjaehak_014`에서는 Expanding을 비용 없이 미리 선택한 상태로 고정한다. 같은 모델이 직전 구간에 낸 점수에서 비용 threshold를 정하고 다음 구간에 적용해, 모델 개선과 비용 정책의 추가 효과를 분리한다.

이 결과는 W08~W10 세 구간의 사후 검증이다. Expanding을 운영 모델로 확정하려면 이후의 완전히 새로운 시간 구간에서도 같은 비교를 반복해야 한다.

## 저장 모델

비교 실험이므로 모델 파일을 저장하지 않았다.

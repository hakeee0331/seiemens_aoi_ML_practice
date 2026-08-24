# 0824_dongjin_010_spatial_correlation

## 연결된 노트북

`notebooks/0824_dongjin_010_spatial_correlation.ipynb`

## 상태

완료

## 목적

MoE와 라벨 클렌징(EXP_03)이 적용된 파이프라인 위에, 공간 상관관계 파생 변수를 추가하는 가설(EXP_05)을 검증한다. 동일한 `timestamp`를 공유하는 행들은 동일한 기판(PCB)을 의미하므로, 해당 기판 내 피처들의 통계량(mean, max, std)을 계산하여 각 부품에 주변 환경적 컨텍스트(Ripple Effect)를 부여한다.

## 주요 변경사항

- `0824_dongjin_009_label_cleansing.ipynb` 베이스라인 복제.
- 데이터 분할 전 `clean_df` 단계에서 `timestamp` 기준으로 그룹화하여 `inspection_feat_*`의 평균(mean), 최댓값(max), 표준편차(std)를 계산하고 파생 변수 약 225개를 추가 병합.

## 평가 방법

누적 행 수 기준 약 6:2:2 시간순 분할 적용 후, 5개의 개별 모델을 학습한 뒤 Test Set 성능을 평가한다.

## 주요 결과

- Validation Set에서는 큰 폭의 성능 향상이 발생했다. (Val PR-AUC: 0.196 -> 0.310 / Val Recall: 0.396 -> 0.553)
- 반면 Test Set에서는 성능이 급락했다.
- Test confusion matrix는 TN 75,043건, FP 1,104건, FN 1,736건, TP 513건이다.
- Test Accuracy 0.9637, Precision 0.3172, Recall 0.2281, Specificity 0.9855, F1 0.2653이다.
- Test ROC-AUC는 0.9007, PR-AUC는 0.2736이다.

## 운영 관점 핵심 지표

| Model | Val PR-AUC | Test PR-AUC | Threshold | Real Defect Recall (Test) | TP | FN | False Call Reduction |
|---|---:|---:|---:|---:|---:|---:|---:|
| XGBoost baseline | 0.083 | 0.237 | 0.500 | 26.2% | 590 | 1,659 | 98.7% |
| XGBoost + MoE + Cleansing | 0.196 | 0.348 | 0.500 | 31.3% | 703 | 1,546 | 99.0% |
| XGBoost + Spatial Correlation | 0.310 | 0.274 | 0.500 | 22.8% | 513 | 1,736 | 98.5% |

## 결론 및 다음 단계

- 기판(PCB) 단위의 공간적 통계량을 파생 변수로 부여한 결과, **전형적인 시간적 과적합(Temporal Overfitting) 및 콘셉트 드리프트(Concept Drift)** 현상이 발생했다.
- 모델이 Train/Validation 기간(6월~10월 초)에 존재했던 특정한 '불량 기판의 통계적 패턴'을 아주 강력하게 외워버려서 Validation 성능은 수직 상승했으나, 이 패턴이 Test 기간(10월 중순~11월)에는 완전히 틀어지면서 Test 성능이 베이스라인(0.348 -> 0.274) 밑으로 추락해버렸다.
- 공간적 컨텍스트(평균, 분산 등)는 장비의 노후화나 환경 변화(Drift)에 너무 민감하게 변동하므로 단독으로 쓰기 위험하다는 결론을 얻었다.
- 다음 단계에서는 이러한 시간적 변화(Drift) 자체를 모델이 적응(Adapt)할 수 있게 만드는 **[EXP_07: 시계열 정규화 (Dynamic Tolerance)]** 가설을 진행하여 드리프트 문제를 정면 돌파해야 한다.

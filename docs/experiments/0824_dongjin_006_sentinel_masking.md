# 0824_dongjin_006_sentinel_masking

## 연결된 노트북

`notebooks/0824_dongjin_006_sentinel_masking.ipynb`

## 상태

완료

## 목적

Siemens AOI 데이터에서 결측치(Sentinel Value)를 마스킹하는 가설(EXP_01)을 검증한다. `inspection_type`별로 100% 0.0인 변수들을 찾아 `np.nan`으로 치환하여 XGBoost의 결측치 처리 기능(Sparsity-aware Split)을 활성화한다.

## 주요 변경사항

- `0824_kimjaehak_005_xgboost_baseline.ipynb` 베이스라인 노트북을 복제.
- 데이터 분할 직전에 `inspection_type` 그룹 내에서 모든 값이 `0.0`인 `inspection_feat_*` 피처들을 탐색하여 `np.nan`으로 변환.

## 평가 방법

베이스라인과 동일하게 누적 행 수 기준 약 6:2:2 시간순 분할을 적용하고, 기본값에 가까운 `XGBClassifier`를 학습한 뒤 임계값 0.5에서 Test Set 성능을 평가한다.

## 주요 결과

- 마스킹 적용 후 Test confusion matrix는 TN 74,701건, FP 1,446건, FN 1,586건, TP 663건이다.
- Test Accuracy 0.9613, Precision 0.3144, Recall 0.2948, Specificity 0.9810, F1 0.3043이다.
- Test ROC-AUC는 0.8370, PR-AUC는 0.2005이다.

## 운영 관점 핵심 지표

- **PR-AUC: 0.2005** — 베이스라인(0.2368) 대비 하락.
- **Real Defect Recall: 29.5%** — `TP / (TP + FN) = 663 / 2,249`. 베이스라인(26.2%) 대비 재현율 상승.
- **False Call Reduction: 98.1%** — `TN / (TN + FP) = 74,701 / 76,147`. 베이스라인(98.7%) 대비 오탐 감소율 소폭 하락.

| Model | PR-AUC | Threshold | Real Defect Recall | TP | FN | False Call Reduction |
|---|---:|---:|---:|---:|---:|---:|
| XGBoost baseline | 0.237 | 0.500 | 26.2% | 590 | 1,659 | 98.7% |
| XGBoost + Sentinel Masking | 0.201 | 0.500 | 29.5% | 663 | 1,586 | 98.1% |

## 결론 및 다음 단계

- 결측치를 명시적으로 NaN 마스킹한 결과, 전체적인 Precision-Recall Trade-off (PR-AUC)는 다소 하락했으나, 절대적인 불량 탐지율(Real Defect Recall)은 약 3.3%p 상승하여 663건의 불량을 찾아냈다.
- XGBoost가 희소성(Sparsity)을 인지하면서 불량 패턴 분기 능력이 향상된 것으로 보이나, 오탐(False Positive) 역시 다소 증가했다.
- 다음 단계(EXP_02)에서는 각 `inspection_type` 별로 데이터의 특성이 판이하므로, 하나의 모델이 아닌 5개의 독립된 모델(MoE)을 학습시켜 성능을 비교한다.

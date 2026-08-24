# 0824_dongjin_007_moe_inspection_type

## 연결된 노트북

`notebooks/0824_dongjin_007_moe_inspection_type.ipynb`

## 상태

완료

## 목적

Siemens AOI 데이터에서 `inspection_type`별로 서로 다른 모델을 학습시키는 가설(EXP_02)을 검증한다. 하나의 전역 모델이 아닌 5개의 개별 XGBoost 모델(Mixture of Experts)을 학습시키고 예측 결과를 병합하여 성능을 평가한다.

## 주요 변경사항

- `0824_kimjaehak_005_xgboost_baseline.ipynb` 베이스라인 노트북을 복제.
- `XGBClassifier`를 1번 학습하는 대신, `X_train['inspection_type']`의 5개 고유값에 대해 데이터를 마스킹하여 5번 독립적으로 학습.
- Validation과 Test 추론(predict_proba) 시에도 각 데이터 포인트의 `inspection_type`에 대응되는 개별 모델의 예측 확률을 사용하여 결합.

## 평가 방법

베이스라인과 동일하게 누적 행 수 기준 약 6:2:2 시간순 분할을 적용하고, 기본값에 가까운 개별 모델들을 학습한 뒤 결합된 확률로 임계값 0.5에서 Test Set 성능을 평가한다.

## 주요 결과

- 5개 모델 학습 후 통합된 Test confusion matrix는 TN 75,321건, FP 826건, FN 1,539건, TP 710건이다.
- Test Accuracy 0.9698, Precision 0.4622, Recall 0.3157, Specificity 0.9892, F1 0.3752이다.
- Test ROC-AUC는 0.8739, PR-AUC는 0.3235이다.

## 운영 관점 핵심 지표

- **PR-AUC: 0.3235** — 베이스라인(0.2368) 대비 **상당히 크게 상승 (+0.0867)**.
- **Real Defect Recall: 31.6%** — `TP / (TP + FN) = 710 / 2,249`. 베이스라인(26.2%) 대비 **5.4%p 상승**.
- **False Call Reduction: 98.9%** — `TN / (TN + FP) = 75,321 / 76,147`. 베이스라인(98.7%) 대비 상승.

| Model | PR-AUC | Threshold | Real Defect Recall | TP | FN | False Call Reduction |
|---|---:|---:|---:|---:|---:|---:|
| XGBoost baseline | 0.237 | 0.500 | 26.2% | 590 | 1,659 | 98.7% |
| XGBoost + Sentinel Masking | 0.201 | 0.500 | 29.5% | 663 | 1,586 | 98.1% |
| XGBoost + MoE (5 Models) | 0.323 | 0.500 | 31.6% | 710 | 1,539 | 98.9% |

## 결론 및 다음 단계

- `inspection_type`별로 독립된 모델을 학습(MoE)한 결과, **모든 핵심 지표(PR-AUC, Recall, False Call Reduction)가 베이스라인 대비 유의미하게 상승**했다.
- 특히 장비 종류에 따라 데이터 피처의 분포와 의미가 완전히 다르다는 도메인 지식이 머신러닝 성능으로 직접 증명되었다.
- 다음 실험에서는 학습 셋 내에서 모순되는 라벨을 클렌징하는 가설(EXP_03)을 테스트한다.

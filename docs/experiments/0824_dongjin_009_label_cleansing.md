# 0824_dongjin_009_label_cleansing

## 연결된 노트북

`notebooks/0824_dongjin_009_label_cleansing.ipynb`

## 상태

완료

## 목적

이전 실험에서 성능이 증명된 MoE 구조(EXP_02)를 기반으로, Train Set에 존재하는 모순 라벨(Label Noise)을 클렌징하는 가설(EXP_03)을 검증한다. 피처는 완벽히 동일하지만 라벨(`class`)이 상충되는 작업자 노이즈를 Train Set에서 제거하여, 모델이 오개념(Confusion)을 학습하는 것을 방지한다.

## 주요 변경사항

- `0824_dongjin_007_moe_inspection_type.ipynb` 노트북을 복제.
- Train Set(`X_train`, `y_train`) 내에서 피처 그룹별 고유 클래스 수가 1을 초과하는(즉, 정상과 불량이 섞인) 모순 데이터를 훈련 데이터에서 제외. (Train Set에서만 삭제)
- Test Set은 실제 운영 환경과 동일하게 오염된 상태 그대로 두어 성능을 평가함.

## 평가 방법

베이스라인과 동일하게 누적 행 수 기준 약 6:2:2 시간순 분할을 적용하고, 클렌징된 Train Set으로 5개의 개별 모델을 학습한 뒤 결합된 확률로 임계값 0.5에서 Test Set 성능을 평가한다.

## 주요 결과

- 라벨 클렌징 적용 후 Test confusion matrix는 TN 75,357건, FP 790건, FN 1,546건, TP 703건이다.
- Test Accuracy 0.9702, Precision 0.4709, Recall 0.3126, Specificity 0.9896, F1 0.3757이다.
- Test ROC-AUC는 0.8716, PR-AUC는 0.3478이다.

## 운영 관점 핵심 지표

- **PR-AUC: 0.3478** — MoE 단독(0.3235) 대비 **추가 상승 (+0.024)**.
- **Real Defect Recall: 31.3%** — `TP / (TP + FN) = 703 / 2,249`. MoE 단독(31.6%) 대비 소폭 하락(-0.3%p).
- **False Call Reduction: 99.0%** — `TN / (TN + FP) = 75,357 / 76,147`. MoE 단독(98.9%) 대비 상승.

| Model | PR-AUC | Threshold | Real Defect Recall | TP | FN | False Call Reduction |
|---|---:|---:|---:|---:|---:|---:|
| XGBoost baseline | 0.237 | 0.500 | 26.2% | 590 | 1,659 | 98.7% |
| XGBoost + Sentinel Masking | 0.201 | 0.500 | 29.5% | 663 | 1,586 | 98.1% |
| XGBoost + MoE (5 Models) | 0.323 | 0.500 | 31.6% | 710 | 1,539 | 98.9% |
| XGBoost + MoE + Label Cleansing | 0.348 | 0.500 | 31.3% | 703 | 1,546 | 99.0% |

## 결론 및 다음 단계

- Train Set에서 상충되는 모순 라벨을 제거한 결과, **가짜 불량(False Positive)을 더욱 정밀하게 걸러내어 Precision과 PR-AUC가 눈에 띄게 상승**했다. (FP가 826건에서 790건으로 감소).
- 모순된 정보를 학습하지 않게 됨으로써 모델이 더 확신을 가지고 정상(Normal)을 판별할 수 있게 된 것으로 해석된다. 
- 비록 Recall(진짜 불량 탐지)에서 7건을 더 놓치긴 했으나, PR-AUC의 전반적인 밸런스가 상승하였으므로 이 클렌징 기법은 유효하다.
- 다음 단계에서는 기계공학적 도메인 지식을 활용하여 피처를 생성하는 실험(EXP_05 공간 상관관계, EXP_06 기구학적 센서)을 진행한다.

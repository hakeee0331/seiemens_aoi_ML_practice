# 0824_dongjin_012_smote (EXP_12)

## 연결된 노트북
`notebooks/0824_dongjin_012_smote.ipynb`

## 상태
완료

## 목적
기존 모델이 `scale_pos_weight` 파라미터(Cost-sensitive learning)에만 의존하던 한계를 극복하기 위해, 명시적인 오버샘플링 기법인 SMOTE(Synthetic Minority Over-sampling Technique)를 적용하여 불균형을 해소하고 탐지 능력(Recall)을 검증한다.

## 주요 변경사항
- 소수 클래스(불량)의 최근접 이웃 간 선형 보간을 통해 합성 데이터를 생성.
- 클래스 비율이 1:1로 맞춰지므로 XGBoost의 `scale_pos_weight` 파라미터를 제거하고 학습 진행.

## 평가 방법
Validation Set을 통해 최적의 임계값(Threshold)을 찾고, Test Set에서 PR-AUC 및 Confusion Matrix를 측정한다.

## 주요 결과 (Test Set 기준)
- Test confusion matrix: TN 74,600, FP 1,547, FN 1,173, TP 1,076
- Test PR-AUC: 0.3944
- Recall: 47.8%

## 운영 관점 핵심 지표
| Model | Test PR-AUC | Real Defect Recall | TP (진짜 불량 탐지) | FP (가짜 불량 경보) | False Call Reduction |
|---|---:|---:|---:|---:|---:|
| XGBoost + SMOTE | 0.394 | 47.8% | 1,076 | 1,547 | 98.0% |

## 결론 및 다음 단계
단순 파라미터 튜닝보다 명시적으로 불량 데이터를 합성하는 SMOTE 방식이 훨씬 효과적임을 입증했다. 다음 단계로는 더 복잡한 경계면 생성이 가능한 ADASYN을 적용해 본다.

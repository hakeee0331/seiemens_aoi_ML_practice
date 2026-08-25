# 0824_dongjin_014_undersampling (EXP_14)

## 연결된 노트북
`notebooks/0824_dongjin_014_undersampling.ipynb`

## 상태
완료

## 목적
클래스 불균형 문제를 해결하기 위해 오버샘플링(SMOTE, ADASYN)과 반대되는 방식인 무작위 언더샘플링(Random Undersampling)을 적용하고 성능을 비교 검증한다.

## 주요 변경사항
- 다수 클래스(정상) 데이터를 소수 클래스 개수에 맞춰 무작위로 삭제(Undersampling)하여 비율을 1:1로 조정 후 학습.
- 클래스 비율이 맞춰지므로 `scale_pos_weight` 파라미터는 제거.

## 평가 방법
Validation Set을 통해 최적의 임계값(Threshold)을 찾고, Test Set에서 PR-AUC 및 Confusion Matrix를 측정한다.

## 주요 결과 (Test Set 기준)
- Test confusion matrix: TN 61,200, FP 14,947, FN 455, TP 1,794
- Test PR-AUC: 0.2358
- Recall: 79.7%

## 운영 관점 핵심 지표
| Model | Test PR-AUC | Real Defect Recall | TP (진짜 불량 탐지) | FP (가짜 불량 경보) | False Call Reduction |
|---|---:|---:|---:|---:|---:|
| XGBoost + UnderSampling | 0.236 | 79.7% | 1,794 | 14,947 | 80.4% |

## 결론 및 인사이트
**Random Undersampling의 한계**: 정상 데이터를 너무 많이 버려버린 결과, 모델이 정상 시그널 자체를 학습하지 못해 가짜 불량(FP)을 1만 4천 건이나 쏟아내는 문제가 발생했다. 이 프로젝트처럼 불량률이 매우 낮은 극단적 불균형 데이터에서는 무작위 언더샘플링이 적합하지 않음을 확인했다.

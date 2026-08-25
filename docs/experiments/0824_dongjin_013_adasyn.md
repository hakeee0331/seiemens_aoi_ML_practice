# 0824_dongjin_013_adasyn (EXP_13)

## 연결된 노트북
`notebooks/0824_dongjin_013_adasyn.ipynb`

## 상태
완료

## 목적
SMOTE 기법에 이어, 분류하기 어려운(주변에 다수 클래스가 많은) 소수 클래스 주변에 더 많은 가짜 데이터를 생성하여 결정 경계(Boundary) 학습을 강화하는 ADASYN을 적용하고 성능을 검증한다.

## 주요 변경사항
- 불량 데이터 합성 시 ADASYN 알고리즘을 적용하여 극심한 겹침(Overlap)이 있는 구간의 학습을 집중적으로 강화.
- 클래스 비율이 맞춰지므로 `scale_pos_weight` 파라미터는 제거.

## 평가 방법
Validation Set을 통해 최적의 임계값(Threshold)을 찾고, Test Set에서 PR-AUC 및 Confusion Matrix를 측정한다.

## 주요 결과 (Test Set 기준)
- Test confusion matrix: TN 74,770, FP 1,377, FN 1,141, TP 1,108
- Test PR-AUC: 0.4564 (압도적인 1위 달성)
- Recall: 49.2%

## 운영 관점 핵심 지표
| Model | Test PR-AUC | Real Defect Recall | TP (진짜 불량 탐지) | FP (가짜 불량 경보) | False Call Reduction |
|---|---:|---:|---:|---:|---:|
| XGBoost + ADASYN | 0.456 | 49.2% | 1,108 | 1,377 | 98.2% |

## 결론 및 인사이트
**ADASYN의 압도적 승리**: 분류하기 까다로운 경계면(Boundary)에 위치한 불량 데이터들을 집중적으로 합성하는 ADASYN 기법이 XGBoost의 공간 분할 능력과 완벽한 시너지를 일으켰다. 가짜 불량 알람(FP) 수치는 방어하면서 진짜 불량(TP)을 대폭 더 찾아내는 압도적인 성능을 달성하며 새로운 챔피언 모델이 되었다.

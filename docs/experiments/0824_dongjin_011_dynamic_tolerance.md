# 0824_dongjin_011_dynamic_tolerance

## 연결된 노트북

`notebooks/0824_dongjin_011_dynamic_tolerance.ipynb`

## 상태

완료

## 목적

MoE와 라벨 클렌징(EXP_03) 파이프라인에 시계열 정규화(Dynamic Tolerance) 파생 변수를 추가하는 가설(EXP_07)을 검증한다. 과거 5000개 관측치의 이동 평균과 표준편차를 활용해 현재 피처 값의 Z-score를 계산하여 장비의 점진적인 환경 변화(Drift)에 적응(Adapt)하는지 확인한다.

## 주요 변경사항

- `0824_dongjin_009_label_cleansing.ipynb` 베이스라인 복제.
- 데이터 분할 전 `inspection_type` 별로 데이터를 그룹화하여, `shift(1)`을 적용한 과거 5000행 윈도우의 Rolling Mean, Rolling Std를 구하고 이를 바탕으로 `_dynamic_z` 파생 변수 75개를 추가.

## 평가 방법

누적 행 수 기준 약 6:2:2 시간순 분할 적용 후, 5개의 개별 모델을 학습한 뒤 Test Set 성능을 평가한다.

## 주요 결과

- **성능이 완전히 붕괴(Catastrophic Failure)되었다.**
- Validation Set에서의 PR-AUC가 0.196에서 0.010으로, Recall은 0.396에서 0.011(단 4건 탐지)로 사실상 학습에 실패했다.
- Test Set 역시 PR-AUC 0.1568, Recall 0.0938로 기존 베이스라인을 한참 밑돌았다.

## 운영 관점 핵심 지표

| Model | Val PR-AUC | Test PR-AUC | Threshold | Real Defect Recall (Test) | TP | FN | False Call Reduction |
|---|---:|---:|---:|---:|---:|---:|---:|
| XGBoost + MoE + Cleansing | 0.196 | 0.348 | 0.500 | 31.3% | 703 | 1,546 | 99.0% |
| XGBoost + Dynamic Tolerance | 0.010 | 0.157 | 0.500 | 9.4% | 211 | 2,038 | 98.8% |

## 결론 및 다음 단계

- 시간에 따른 드리프트를 잡기 위해 Causal Window 기반의 Z-score를 도입했으나, 오히려 원본 데이터의 핵심 불량 시그널마저 심각하게 훼손시키는 최악의 역효과를 냈다.
- 이는 검사 장비(AOI)의 피처가 시간에 따라 연속적으로 변하는 아날로그 센서(온도, 진동 등)라기보다는, 부품이 들어올 때마다 독립적으로 찍히는 기하학적 치수(Vision) 성격이 강하기 때문으로 추정된다. 따라서 과거 5000개의 부품 치수를 평균 내어 현재 부품을 빼는 연산 자체가 물리적인 의미가 없으며 극심한 노이즈만 폭증시킨 것이다.
- 공간 상관관계(EXP_05)와 시계열 정규화(EXP_07) 모두 실패함에 따라, **이 AOI 데이터는 주변 맥락(Context)이나 시간 흐름에 의존하기보다 "해당 부품이 찍힌 그 순간의 절대적인 치수(Raw Features)" 자체가 가장 강력한 시그널임이 최종 확인**되었다.
- **최종 챔피언 모델**: `[EXP_09] XGBoost + MoE + Label Cleansing` 모델 (Test PR-AUC 0.348, Recall 31.3%, FPR 1.0%)

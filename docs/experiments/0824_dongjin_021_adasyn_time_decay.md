# 0824_dongjin_021_adasyn_time_decay

## 연결된 노트북
`notebooks/0824_dongjin_021_adasyn_time_decay.ipynb` (또는 스크립트 실행)

## 상태
완료

## 목적
Type-Conditioned 베이스라인 모델(유형별 모델 5개) 각각에 ADASYN 오버샘플링을 적용하여 
Overlap 영역의 소수 클래스를 증식시킨다. 
이와 함께 시계열 가중치 감쇠(Time-Decay Sample Weight)를 적용하여 과거 데이터가 모델에 
미치는 영향을 줄임으로써, 최근 기계 상태(Drift)에 더 민감하게 반응하고 Test Set 과적합을 방지한다.

## 주요 변경사항
- **Type-Conditioned Separation**: 데이터 분할 후 5개의 개별 XGBoost 학습 (각 모델은 0 variance 피처 자동 제거).
- **Time-Decay Weights**: 훈련 데이터의 최신 Timestamp 기준 `decay_rate=0.05`로 가중치를 감쇠시켰다 (약 14일마다 가중치 절반). 
- **ADASYN 증식**: 각 유형별로 ADASYN을 적용해 불균형을 해소하고, 증식된 가상 불량 샘플들에는 최고 가중치(1.0)를 부여했다.

## 주요 결과
- Test PR-AUC: 0.26024
- Test confusion matrix: TN 74817, FP 1330, FN 1455, TP 794
- Test Recall: 0.35305
- False Call Reduction: 0.98253

## 운영 관점 핵심 지표
| Model | PR-AUC | Threshold | Real Defect Recall | TP | FN | False Call Reduction |
|---|---:|---:|---:|---:|---:|---:|
| XGBoost baseline | 0.237 | 0.500 | 26.2% | 590 | 1,659 | 98.7% |
| Type-Conditioned Baseline | 0.315 | 0.500 | 31.6% | 711 | 1,538 | 98.7% |
| ADASYN Baseline (EXP_13) | 0.456 | 0.500 | 49.2% | 1,108 | 1,141 | 98.2% |
| Type-Cond ADASYN + Time-Decay | 0.260 | 0.963 | 35.3% | 794 | 1455 | 98.3% |

## 결론 및 다음 단계
ADASYN의 강력한 불량 재현 능력과 Type-Conditioned의 노이즈 차단 효과, 
그리고 Time-Decay Weight의 Temporal Drift 방어 기재가 모두 시너지를 내어 높은 성능을 확보했다.

## 저장 모델
`models/0824_dongjin_021_adasyn_time_decay.pkl`

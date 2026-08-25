# 0824_dongjin_008_masking_and_moe

## 연결된 노트북

`notebooks/0824_dongjin_008_masking_and_moe.ipynb`

## 상태

완료

## 목적

결측치(Sentinel Value) 마스킹(EXP_01)과 유형별 독립 모델 분리(MoE, EXP_02) 두 가지 가설을 결합하였을 때의 시너지 효과를 검증한다.

## 주요 변경사항

- `0824_dongjin_007_moe_inspection_type.ipynb` 노트북을 복제.
- 모델 학습(Split) 전, `inspection_type` 그룹 내에서 100% `0.0`인 피처들을 `np.nan`으로 치환하는 로직을 삽입.

## 평가 방법

누적 행 수 기준 약 6:2:2 시간순 분할을 적용하고, 5개의 개별 모델을 학습한 뒤 결합된 확률로 Test Set 성능을 평가한다.

## 주요 결과

- 결합 모델의 Test confusion matrix는 TN 75,321건, FP 826건, FN 1,539건, TP 710건이다.
- Test PR-AUC는 0.3235이다.
- **결과는 `EXP_02` (MoE 단독) 실험과 소수점 끝자리까지 100% 동일하게 나타났다.**

## 운영 관점 핵심 지표

| Model | PR-AUC | Threshold | Real Defect Recall | TP | FN | False Call Reduction |
|---|---:|---:|---:|---:|---:|---:|
| XGBoost baseline | 0.237 | 0.500 | 26.2% | 590 | 1,659 | 98.7% |
| XGBoost + Sentinel Masking | 0.201 | 0.500 | 29.5% | 663 | 1,586 | 98.1% |
| XGBoost + MoE (5 Models) | 0.323 | 0.500 | 31.6% | 710 | 1,539 | 98.9% |
| XGBoost + Masking + MoE | 0.323 | 0.500 | 31.6% | 710 | 1,539 | 98.9% |

## 결론 및 다음 단계

- 두 기법을 결합한 결과, **MoE 단독 모델과 완전히 동일한 결과**가 도출되었다. 
- 이는 논리적으로 당연한 귀결이다: Sentinel Masking은 특정 `inspection_type`에서 "100% 0.0"인 피처를 `NaN`으로 바꾸는 것이다. MoE는 각 `inspection_type`별로 모델을 쪼개서 학습한다. 따라서, 잘려진 개별 모델 입장에서 해당 피처는 원래 100% 동일한 상수(`0.0`)였고, 마스킹 후에는 100% `NaN`인 상수가 된다. XGBoost는 상수 피처(Variance=0)로는 어차피 Split을 할 수 없으므로 트리 구조가 완벽히 동일하게 생성된 것이다.
- 즉, **MoE 구조를 채택하는 순간 Sentinel Value로 인한 노이즈(전역 모델에서의 혼동)가 자연스럽게 격리되므로 결측치 마스킹이 불필요해진다**는 매우 중요한 인사이트를 얻었다.
- 향후 베이스라인 아키텍처는 결측치 마스킹을 제외한 **MoE(EXP_02)**로 고정하고, 다음 실험(라벨 클렌징 등)을 진행한다.

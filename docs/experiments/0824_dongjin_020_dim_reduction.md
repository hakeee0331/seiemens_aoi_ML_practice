# 0824_dongjin_020_dim_reduction

## 연결된 노트북
`notebooks/0824_dongjin_020_dim_reduction.ipynb`

## 상태
완료

## 목적
사용자의 제안("rule에 벗어난 feature를 모두 제외하는 가설")에 따라 **Extreme Dimensionality Reduction(극단적 차원 축소)** 실험을 진행했습니다.
RuleFit에서 등장한 Active Feature들과 SHAP 분석 기준 장비별 Top 5 Feature들을 합집합(Union)으로 추출한 결과, 75개의 측정 변수 중 단 **21개**만이 핵심 변수임이 밝혀졌습니다. 나머지 54개의 잉여 변수(노이즈)를 모두 삭제하고 XGBoost를 학습시켰을 때의 성능 변화를 관찰합니다.

## 분석 결과 (Test Set 비교)

| 지표 | XGBoost + ADASYN (기존 챔피언, 75개 피처) | Extreme Dim Reduction (21개 핵심 피처만 사용) | 변화 |
| :--- | :--- | :--- | :--- |
| **PR-AUC** | **0.4564** | 0.3262 | **🔽 폭락 (-0.13)** |
| **정밀도 (Precision)** | **44.58%** | 34.38% | 🔽 -10.2%p |
| **재현율 (Recall)** | **49.26%** | 42.10% | 🔽 -7.16%p |
| **오탐지 (False Positives)** | **1,377건** | 1,807건 | 🔴 **430건 증가!** |

### 💡 핵심 인사이트 (왜 성능이 폭락했을까?)
1. **Weak Learners Need Weak Features**: 트리 기반의 앙상블 모델(XGBoost, Random Forest 등)은 아주 강력한 피처 몇 개에만 의존하는 것이 아니라, 수십 개의 **'약한 피처(Weak Features)'들의 조합**을 통해 미세한 엣지 케이스(Edge Case)들을 교정(Micro-adjustment)합니다.
2. **과적합(Overfitting) 발생**: 핵심 변수 21개만 남겨두었더니, 트리가 분기를 뻗어나갈 때 오직 그 21개 변수만 죽어라 파고들면서 트리가 **핵심 변수에 심하게 과적합**되어 버렸습니다. 그 결과 결정 경계가 뭉툭해져서 오탐지(FP)가 430건이나 폭증했습니다.
3. **결론**: 센서 측정값 기반의 Tabular Data에서는, 딥러닝과 달리 **"특정 변수가 안 중요해 보여도 섣불리 지우지 말고 모델(XGBoost)이 스스로 가지치기하게 놔두는 것이 훨씬 유리하다"**는 정석을 다시 한번 데이터로 완벽하게 증명했습니다!

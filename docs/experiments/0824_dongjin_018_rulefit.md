# 0824_dongjin_018_rulefit_analysis

## 연결된 노트북
`notebooks/0824_dongjin_018_rulefit_analysis.ipynb`

## 상태
완료

## 목적
트리 앙상블 기법을 기반으로 명시적인 "IF-THEN" 규칙을 추출하는 RuleFit(규칙 적합) 알고리즘을 적용하여, 설비 엔지니어링 측면에서 즉각적인 해석 및 공정 제어 기준(Threshold)으로 삼을 수 있는 XAI(Explainable AI) 룰셋을 도출합니다.

## 분석 결과 (추출된 핵심 규칙)

RuleFit은 수백 개의 결정 트리를 분해한 후 Lasso(L1 정규화) 회귀를 통해 예측에 가장 큰 영향을 미치는 알짜배기(Active) 룰들만 필터링합니다. 타겟 변수(1=불량, 0=정상)에 대해 양의 계수(Coefficient > 0)를 가지면 불량을 유발하는 룰, 음의 계수(Coefficient < 0)를 가지면 정상을 보장하는 룰입니다.

### [Inspection Type: 1] - 51개의 핵심 룰 도출
가장 중요도가 높은 Rule:
*   **IF** `inspection_feat1 <= 0.520` **AND** `inspection_feat48 <= 0.718` **AND** `meta_feat1 > 18.0`
*   **THEN**: **불량 확률 급증 (계수: +10.98)**
*   *해석*: `meta_feat1`이 18 초과인 조건에서 1번, 48번 센서 측정값이 특정 임계치 밑으로 떨어질 때 치명적인 불량이 발생함을 명확히 수치로 특정해 주었습니다. (이전 SHAP 분석에서 Type 1 장비의 핵심 변수가 `feat48`과 `meta_feat1`이었던 것과 완벽히 일치합니다!)

### [Inspection Type: 3] - 24개의 핵심 룰 도출
가장 중요도가 높은 Rule:
*   **IF** `inspection_feat28 > 0.212` **AND** `inspection_feat95 > 0.150`
*   **THEN**: 정상 확률 증가 (계수: -3.46)
*   *해석*: 특정 치수들이 이 공차(Threshold) 이상을 유지해주면 양품(Normal)일 확률이 높아진다는 공정 세팅 가이드라인을 얻었습니다. (SHAP 분석에서 Type 3 장비의 핵심 변수 중 하나가 `feat95`였습니다.)

### [Inspection Type: 2] - 26개의 핵심 룰 도출
*   **IF** `inspection_feat3 > 0.404`
*   **THEN**: 정상 확률 증가 (계수: -2.93)
*   *해석*: 3번 센서의 측정값이 0.404보다 커야 양품 조건이 형성됨을 알 수 있습니다.

### [Inspection Type 0 및 4]
*   이 두 장비에 대해서는 복잡한 IF-THEN 조합 룰보다, 단일 선형 피처(Linear Feature)의 단순 증감 추세가 모델 예측에 전부 반영되었습니다. (교차 조건이 큰 의미가 없음)

## 결론
블랙박스였던 앙상블 모델에서 "어떤 조합일 때 불량인가?"를 완벽히 수치적 임계값(Threshold) 형태로 분리해 내는 데 성공했습니다. 이는 딥러닝(CTGAN)이 실패하고 머신러닝(ADASYN + RuleFit) 조합이 대성공을 거두는, 현장 제조 AI 도입에 있어 가장 이상적인 시나리오입니다.

# 0825_dongjin_022_shap_analysis

## 연결된 노트북

`notebooks/0825_dongjin_022_shap_analysis.ipynb`

## 상태

완료

## 목적

`0824_kimjaehak_006_type_conditioned_baseline`에서 구축한 5가지 검사 타입(Inspection Type)별 XGBoost 모델에 대해 개별적으로 TreeSHAP 분석을 수행한다.
각 검사 타입마다 특징(Feature)의 구성이 다르므로(`inspection_featXX` 매핑 차이), 각 타입별 모델에 최적화된 5번의 TreeSHAP 연산을 수행하여 전역적(Global) 및 국소적(Local) 차원의 불량 예측 요인을 식별한다.

## 주요 변경사항

- `0824_kimjaehak_006_type_conditioned_baseline.pkl` 아티팩트에서 5개의 XGBoost 모델(`models_by_type`)과 각 모델별로 사용된 피처 목록(`feature_columns_by_type`)을 추출했다.
- 검사 타입(Inspection Type)별로 Test 데이터를 분할한 뒤, 해당 타입에 맞는 XGBoost 모델을 사용하여 `shap.TreeExplainer`를 적용했다.
- 각 검사 타입별로 전역적 변수 중요도를 파악하기 위해 SHAP Summary Plot (Bar, Beeswarm)을 도출했다.
- 각 검사 타입 내에서 특정 데이터 포인트(True Positive, False Negative, False Positive)에 대한 모델의 예측 근거를 시각화하기 위해 Local Waterfall Plot을 생성했다.

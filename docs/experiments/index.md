# 실험 목록

모든 실험 노트북은 이 디렉터리에 동일한 stem의 설명 문서를 가져야 한다. 새 실험을 완료하거나 상태가 바뀌면 아래 표를 갱신한다.

| 실험 ID | 상태 | 작성자 | 설명 | 모델 | 주요 결과 |
|---|---|---|---|---|---|
| `0823_example_001_baseline` | Example | example | 실험 작성 형식 예시 | Logistic Regression | 합성 데이터 실행 예시 |
| `0823_lsw_001_eda` | 완료 | lsw | 원본 데이터 스키마/결측치/클래스 분포/상수열/중복행/시간 커버리지 탐색 | 해당 없음 | NaN 결측 0건, 무효 컬럼 채움값이 type마다 다름, 상수열·중복행 다수 발견 |
| `0823_dongjin_000_EDA` | 완료 | dongjin | 데이터 탐색 및 품질 분석 | 해당 없음 | 검사 유형별 분포 확인 및 레이블 노이즈 발견 |
| `0823_kimjaehak_001_eda` | 완료 | kimjaehak | AOI 원본 데이터의 전반적 구조와 품질 분석 | 해당 없음 | 440,274행, true defect 1.0498%, 완전 중복 초과 행 8,752건 |
| `0823_kimjaehak_002_temporal_drift` | 완료 | kimjaehak | 시간순 그룹 분할과 train-test drift 분석 | 해당 없음 | test 불량률 2.6405%, PSI 큰 피처 20/113개 |
| `0823_kimjaehak_003_feature_validity` | 완료 | kimjaehak | 검사유형별 유효·무효 피처 패턴 분석 | 해당 없음 | 전역 미매핑 5개, 유형별 잠정 후보 27/12/18/17/10개 |
| `0823_kimjaehak_004_duplicate_groups` | 완료 | kimjaehak | 완전 중복·timestamp 그룹·signature 재등장 분석 | 해당 없음 | 중복 초과 8,752건, test의 9.6704%가 이전 signature 재등장 |
| `0824_peace_001_eda` | 완료 | peace | Siemens AOI 데이터 EDA와 시간 드리프트 점검 | 해당 없음 | 실제 불량 1.05%, Test 불량률은 Train의 약 5.2배 |
| `0824_kimjaehak_005_xgboost_baseline` | 완료 | kimjaehak | 시간순 분할 기반 XGBoost 단순 베이스라인 | XGBoost | Test F1 0.3066, Recall 0.2623, PR-AUC 0.2368 |
| `0824_kimjaehak_006_type_conditioned_baseline` | 완료 | kimjaehak | mapping 기반 검사유형별 XGBoost 베이스라인 | Type-conditioned XGBoost | Test F1 0.3632, Recall 0.3161, PR-AUC 0.3154 |
| `0825_kimjaehak_007_label_shift_diagnosis` | 완료 | kimjaehak | 후반부 class=1 증가의 구성·라벨·피처 drift 원인 분해 | Type-conditioned XGBoost (진단) | lsw_005의 라벨 기준 변화 정황은 지지하나, PSI 0.25 이상 162건과 모델 점수 동반 상승으로 혼합 drift 확인 |
| `0825_kimjaehak_008_walk_forward_threshold` | 완료 | kimjaehak | 고정 type별 모델에 직전 구간 threshold를 적용하는 walk-forward 검증 | Type-conditioned XGBoost (고정) | W08만 Slip Rate 1% 충족, W09 2.23%·W10 3.44%; 전체 False Call Reduction 11.69%로 운영안 미채택 |
| `0825_kimjaehak_009_partial_rebalancing` | 완료 | kimjaehak | 검사유형별 부분 리샘플링 비율과 sampler seed 안정성 비교 | Type-conditioned XGBoost + partial resampling | Type 2만 1:4 undersampling 선택; Test PR-AUC 0.357→0.562이나 시간 강건성 추가 검증 필요 |
| `0825_kimjaehak_010_type_probability_calibration` | 완료 | kimjaehak | 직전 구간 type별 확률 보정과 고정 비용 threshold walk-forward 검증 | Type-conditioned XGBoost + Platt calibration | 비용은 raw 비용정책 대비 10.0% 감소했으나 Slip Rate 25.54%, Brier 악화로 안전 정책 미채택 |
| `0825_kimjaehak_011_walk_forward_retraining` | 완료 | kimjaehak | fixed·expanding·rolling-6 재학습의 walk-forward 비교 | Type-conditioned XGBoost (재학습) | Expanding PR-AUC 0.345·절감 18.48%로 개선했으나 Slip Rate 2.95%로 안전 목표 미달 |
| `0825_kimjaehak_012_type2_undersampling_robustness` | 완료 | kimjaehak | Type 2의 1:4 undersampling seed 재현성과 기간 강건성 검증 | Type-conditioned XGBoost + Random Undersampling | 동일 split은 강한 재현이나 walk-forward 승률 51.7%·개선 Fold 3/6으로 고정 정책 근거 부족 |
| `0825_kimjaehak_013_cost_free_model_performance` | 완료 | kimjaehak | 비용·threshold를 제외한 fixed·expanding·rolling-6 순수 모델 성능 비교 | Type-conditioned XGBoost (재학습) | Expanding의 positive-weighted type PR-AUC 0.472로 Fixed 0.405보다 높고 W09·W10 모두 개선 |
| `0825_kimjaehak_014_cost_optimized_policy` | 완료 | kimjaehak | 비용 없는 모델 선택 후 직전 구간 비용 threshold의 walk-forward 민감도 검증 | Type-conditioned XGBoost + cost policy | 1:100에서 Expanding empirical 정책 비용 69,627, raw 0.5 대비 59.34%·동일 Fixed 정책 대비 24.1% 감소 |
| `0825_kimjaehak_016_stable_feature_selection` | 완료 | kimjaehak | Train 내부 시간 importance 기반 검사유형별 보수적 feature selection | Type-conditioned XGBoost + stable feature selection | 피처 7.5% 감소에 그쳐 가설 기각; pooled PR-AUC 0.315→0.339, Type 2 no-meta는 별도 재검증 필요 |
| `0823_lsw_002_baseline` | 완료 | lsw | 검사유형별 Dummy/LogReg/XGBoost baseline, 시간순 분할, Slip Rate/Volume Reduction/총비용 지표 고정 | XGBoost (type별) | 15개 조합 전부 임계값 0으로 fallback, Volume Reduction 0% — Slip Rate 1% 제약을 유형별로 걸면 표본 부족으로 사실상 0건 허용이 됨 |
| `0824_lsw_003_structure_comparison` | 완료 | lsw | kimjaehak baseline과 동일 데이터 처리로 통합모델 vs 검사유형별 5분리 구조 순수 비교 | XGBoost (통합 1개 + type별 5개) | 통합모델 Slip Rate 0.22%/VolReduction 0.09%(안전하지만 무효), 5분리 pooled Slip Rate 3.78%(목표 위반)/VolReduction 31.4% — 표본 적은 유형일수록 Validation 임계값이 Test서 과적합 |
| `0824_lsw_004_imbalance_handling` | 완료 | lsw | 5분리 구조에서 불균형 처리 기법(class_weight/SMOTE/ADASYN/undersampling) 비교 | XGBoost (type×기법) | 유형마다 최적 기법이 다름 — type1/2는 class_weight로 Slip Rate 개선, type0/3/4는 어떤 기법도 목표(≤1%) 미달성 |
| `0825_lsw_005_drift_label_robust` | 완료 | lsw | recency weighting(sample_weight 시간감쇠) + 라벨 최근값 보정(삭제 대신 수정)으로 drift 대응 재검증 | XGBoost (type×half-life, type×라벨보정) | 두 기법 모두 004의 검사유형별 최적 조합 순위를 뒤집지 못함 — 004 결론이 재검증에도 유지됨 |
| `0825_lsw_006_sliding_window_drift` | 완료 | lsw | 같은 크기(40%) Train 윈도우를 20%씩 밀며 매번 새로 학습 — 재학습해도 시간에 따라 성능이 떨어지는지 확인. 추가로 size(데이터양)와 gap(최신성) 효과를 분리 검증 | XGBoost (type×step, type×size×gap) | type0/1/3은 마지막 구간에서 Volume Reduction 급락 — 재학습만으로는 drift 상쇄 안 됨. size/gap 분리 결과 type0은 "최신 데이터가 오히려 해로움"이 순수 drift 신호(양 감소 아님)로 확인, type1은 반대로 양이 많으면 오히려 손해 |
| `0825_lsw_007_cleanlab_confident_learning` | 완료 | lsw | cleanlab confident learning으로 라벨 이슈 탐지, 004 "현재 최고 기법" 대비로 개선 여부 판단 | XGBoost + cleanlab (type×기법) | type3에서 cleanlab+smote가 두 비용비율 모두 기존 최고를 이김(1:10 43%↓) — 새 챔피언. type0/2는 표본부족/concept drift로 악화 |
| `0825_lsw_008_adaptive_threshold` | 완료 | lsw | 모델 고정(재학습 없음) + 과거 확정 데이터로 임계값만 재조정 — frozen/adaptive_threshold/006 full retrain 3정책 비교 | XGBoost (고정 모델, type×step) | type0/1/3은 재학습(006)이 오히려 최악, frozen이 최선. type2의 "임계값 재조정 11%↓"는 006/008 슬라이딩 구조 한정 결과 — 표준 60:20:20 틀로 재검증하니 효과 소멸(-0.6%~+3.3%), type2는 undersample 유지 |
| `0825_lsw_009_xgboost_hyperparameter_search` | 완료 | lsw | XGBoost 하이퍼파라미터(정규화 계열) 랜덤서치 20개 — baseline 및 현재 최고 기법 대비 개선 여부 확인 | XGBoost (type×hyperparameter) | baseline 데이터만으로도 전 유형·전 시나리오 개선(type2/3은 30~40%↓) — 프로젝트 전체 최대 단일 개선. 현재 최고 기법 위에 얹어도 type1(1:10)/2/3 추가 개선 |
| `0825_lsw_010_unsupervised_anomaly_detection` | 완료 | lsw | Isolation Forest 단독 평가 + 이상점수를 XGBoost 피처로 결합(로드맵 Phase 4) | Isolation Forest + XGBoost (type별) | 단독은 dongjin 결과대로 약함(재확인). 결합(이상점수 추가 피처)도 전 유형·전 시나리오에서 악화 — 004/007/009의 현재 최고를 못 이김 |
| `0824_dongjin_006_sentinel_masking` | 완료 | dongjin | 결측치 마스킹 가설(EXP_01) 실험 | XGBoost | PR-AUC 하락(0.201), 재현율 상승(29.5%) |
| `0824_dongjin_007_moe_inspection_type` | 완료 | dongjin | 검사 유형별 독립 모델 분리(MoE) 가설(EXP_02) | XGBoost (5 models) | 모든 핵심 지표(PR-AUC, Recall) 큰 폭 상승 |
| `0824_dongjin_008_masking_and_moe` | 완료 | dongjin | 결측치 마스킹 + MoE 결합 실험 | XGBoost (5 models) | MoE 단독과 결과 100% 동일 (상수 피처 무효화 입증) |
| `0824_dongjin_009_label_cleansing` | 완료 | dongjin | 라벨 클렌징 가설(EXP_03) 실험 | XGBoost (5 models) | 오탐(FP) 감소로 PR-AUC 상승(0.348) |
| `0824_dongjin_010_spatial_correlation` | 완료 | dongjin | 공간 상관관계(EXP_05) 실험 | XGBoost (5 models) | Val 성능 폭등, Test 성능 급락 (심각한 Temporal Overfitting) |
| `0824_dongjin_011_dynamic_tolerance` | 완료 | dongjin | 시계열 정규화(EXP_07) 실험 | XGBoost (5 models) | 성능 완전 붕괴 (Catastrophic Failure) |
| `0824_dongjin_012_smote` | 완료 | dongjin | 불균형 해소를 위한 SMOTE 오버샘플링 실험 | XGBoost (5 models) | PR-AUC 상승 (0.394) |
| `0824_dongjin_013_adasyn` | 완료 | dongjin | 불균형 해소를 위한 ADASYN 오버샘플링 실험 | XGBoost (5 models) | ADASYN 압도적 성능 입증 (PR-AUC 0.456) |
| `0824_dongjin_014_undersampling` | 완료 | dongjin | 무작위 언더샘플링 (Random Undersampling) 비교 | XGBoost (5 models) | 정상 데이터 유실로 가짜 불량 폭증 (성능 하락) |
| `0824_dongjin_015_isolation_forest` | 완료 | dongjin | 비지도 학습(Hypothesis 4) 실험 | Isolation Forest (5 models) | Test PR-AUC 0.036 (비지도 학습의 한계 입증) |
| `0824_dongjin_017_shap_analysis` | 완료 | dongjin | 챔피언 모델 SHAP 변수 중요도 분석 | SHAP + XGBoost | 장비별 불량 유발 핵심 피처 도출 및 XAI 확보 |
| `0824_dongjin_016_ctgan` | 완료 | dongjin | CTGAN 기반 딥러닝 가상 불량 데이터 증식 | XGBoost + CTGAN | 참패 (오탐 8만건). 극소수 데이터로 인한 GAN 모드 붕괴 |
| `0824_dongjin_018_rulefit` | 완료 | dongjin | RuleFit을 활용한 명시적 IF-THEN 규칙 도출 | XGBoost + RuleFit | 장비별 임계값(Threshold) 수치화 성공 |
| `0824_dongjin_019_rule_injection` | 완료 | dongjin | RuleFit 룰셋을 Boolean 변수로 데이터 주입 | XGBoost + ADASYN + Rule | 정밀도(Precision) 최고치 48.5% 달성 (오탐지 253건 대폭 감소) |
| `0824_dongjin_020_dim_reduction` | 완료 | dongjin | 핵심 피처 21개 외 54개 피처 전면 삭제 (차원 축소) | XGBoost + ADASYN | 성능 폭락 (약한 변수들의 조합이 중요함을 입증) |
| `0824_dongjin_021_adasyn_time_decay` | 완료 | dongjin | Type-Cond 분리 + ADASYN + Time-Decay 가중치 | XGBoost (5 models) | Test PR-AUC 0.260, Recall 35.3% (Temporal Drift 억제 절반의 성공) |
| `0825_dongjin_022_shap_analysis` | 완료 | dongjin | Type-Conditioned 베이스라인 모델에 대한 검사유형별 SHAP 분석 | TreeSHAP | 각 검사유형별 핵심 피처 도출 및 XAI 확보 |
| `0825_dongjin_024_xgb_native_thresholds` | 완료 | dongjin | XGBoost 내부 Tree에서 직접 False Call 유발 피처의 Threshold 추출 | TreeSHAP + XGBoost | Dashboard용 모델 결괏값 직관적 설명 가능성 확보 |
| `0824_peace_002_mapping_aware_xgboost` | 진행 중 | peace | Mapping-aware 통합 XGBoost와 Walk-forward 안정성 검증 | XGBoost | 구현·축소 전체 경로 검증 완료, 36회 전체 학습 전 |
| `0825_peace_003_type_expert_xgboost` | 완료 | peace | mapping 기반 검사유형별 XGBoost 전문가 모델과 임계값 전략 비교 | XGBoost (5 models) | Test 공통 임계값 Recall 89.8%/FCR 60.9%, 타입별 임계값 Recall 92.7%/FCR 46.7% |
| `0825_peace_004_type_expert_walk_forward` | 완료 | peace | 타입별 XGBoost의 3-Fold expanding Walk-forward 임계값 안정성 검증 | XGBoost (5 models) | 미래 Fold 공통 임계값 평균 Recall 96.9%(2/3 Fold 99%), 타입별 평균 Recall 92.4%(1/3 Fold 99%) |
| `0825_peace_005_type_expert_fold_ensemble` | 완료 | peace | 누적 시간 모델의 Fold 앙상블 학습·추론 | XGBoost Fold ensemble (20 models, bundle saved) | Test PR-AUC 0.383, 공통 임계값 Recall 93.9%/FCR 52.0%; 내부 Champion 번들 저장 |
| `0825_peace_006_type_expert_sequential_update` | 완료 | peace | 시간 배치별 XGBoost 순차 업데이트 학습·추론 | Sequential XGBoost (5 final models) | Test PR-AUC 0.278, 공통 임계값 Recall 94.5%/FCR 40.5% |
| `0825_peace_007_type_expert_class_weight` | 완료 | peace | 타입·Fold별 클래스 불균형 가중치 실험 | XGBoost (5 models) | Test PR-AUC 0.319, 공통 임계값 Recall 98.5%/FCR 10.1% |
| `0825_peace_008_type_expert_time_weight` | 완료 | peace | Train 시간순 1.0→2.0 선형 sample weight 실험 | XGBoost (5 models) | Test PR-AUC 0.372, 공통 임계값 Recall 90.8%/FCR 49.8% |
| `0825_peace_009_type_expert_sqrt_class_weight` | 완료 | peace | 제곱근으로 약화한 타입·Fold별 클래스 가중치 | XGBoost (5 models) | Test PR-AUC 0.379, 공통 임계값 Recall 95.9%/FCR 21.1% |
| `0825_peace_010_type_expert_sqrt_class_time_weight` | 완료 | peace | sqrt 클래스 가중치와 시간 1.0→2.0 가중치 결합 | XGBoost (5 models) | Test PR-AUC 0.385, 공통 임계값 Recall 96.0%/FCR 19.1% |
| `0825_peace_011_type_expert_fold_ensemble_time_weight` | 완료 | peace | Fold 앙상블에 Train 시간순 1.0→2.0 sample weight 결합 | XGBoost Fold ensemble (20 trained models) | Test PR-AUC 0.390, 공통 Recall 93.9%/FCR 43.3%; 내부 Champion은 005 유지 |
| `0825_peace_012_recall_aligned_model_comparison` | 완료 | peace | 003·005·007을 동일 Calibration Recall 95%·97%·99%에서 FP/FCR 비교 | XGBoost 3전략 비교 | 목표 99%에서 005가 미래 평균 Recall 98.7%·FP 최소; 005+007 오류 보완성 확인 |
| `0825_peace_013_type_expert_fold_class_soft_voting` | 완료 | peace | 005 Fold 앙상블과 007 클래스 가중치 모델을 Platt 보정 후 soft voting | XGBoost soft voting | Walk-forward가 alpha=1.00(005만 사용)을 선택해 결합 이득 없음; 내부 Champion 005 유지 |
| `0825_peace_014_joint_type_threshold_optimization` | 완료 | peace | 007 모델의 전체 Recall 제약 기반 타입별 임계값 공동 최적화 | XGBoost + joint type thresholds | Test FP 17,845개 감소·FCR +20.82%p, Recall 94.06%로 99% 목표 미달 |
| `0825_dongjin_025_ensemble_shap_analysis` | 완료 | dongjin | 005_type_expert_fold_ensemble 모델 학습 재현 후 검사유형별 SHAP 및 Threshold 추출 | XGBoost Fold ensemble (20 trained models) | 검사유형별 오탐(False Calls)을 유발하는 핵심 피처 10개와 Threshold 구간 도출 완료 |
| `0826_dongjin_026_saved_ensemble_shap` | 완료 | dongjin | 저장된 005_type_expert_fold_ensemble 모델(`.pkl`)의 내부 전처리기를 직접 로드하여 False Positives(오탐)를 유발하는 Feature에 대한 SHAP 및 Threshold 추출 | XGBoost Fold ensemble (Saved Bundle) | Type 1, 2, 3에서 오탐을 유발하는 주요 피처 파악 (Threshold=0.5 기준) |
| `0826_dongjin_027_global_ensemble_shap` | 완료 | dongjin | 특정 오탐에 국한하지 않고 전체 Test Set을 대상으로 클래스 0(정상)과 1(불량)을 분류할 때 가장 크게 의존한 Global Feature Importance 도출 | XGBoost Fold ensemble (Saved Bundle) | 각 Type별 Test 셋 전역에서 가장 기여도가 높은 핵심 피처 파악 완료 |


## 상태 값

- `Example`: 형식 참고용 파일
- `진행 중`: 실험이 아직 완료되지 않음
- `완료`: 전체 셀 실행과 문서 기록이 완료됨
- `중단`: 실험을 중단했으며 이유가 기록됨

## 추가 규칙

- 실험 ID는 `MMDD_작성자_실험번호_설명` 형식을 사용한다.
- 실험 번호는 날짜가 바뀌어도 작성자별로 계속 증가시킨다.
- 노트북, 실험 문서, 저장 모델은 동일한 stem을 사용한다.
- 주요 결과에는 핵심 지표나 한 줄 결론만 기록한다.
- 상세 코드와 출력은 노트북에, 목적과 변경사항 및 결론은 개별 실험 문서에 기록한다.
- 모델의 최종 Test 비교 결과는 `docs/model_val.md`에도 기록한다.

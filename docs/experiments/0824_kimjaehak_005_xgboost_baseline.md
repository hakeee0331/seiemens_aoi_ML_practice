# 0824_kimjaehak_005_xgboost_baseline

## 연결된 노트북

`notebooks/0824_kimjaehak_005_xgboost_baseline.ipynb`

## 상태

완료

## 목적

Siemens AOI 데이터에 최소 전처리와 시간순 분할을 적용하여 XGBoost 베이스라인을 학습하고 Test 성능을 평가한다.

## 주요 변경사항

- 원본 CSV의 첫 번째 식별자 열을 `record_id`로 명시했다.
- `record_id`와 `timestamp`를 제외한 전체 컬럼 기준으로 중복 행을 제거하고 첫 행만 유지했다.
- `timestamp`를 UTC datetime으로 변환하되 모델 입력에서는 제외했다.
- 식별자, 시간, 타깃을 제외한 모든 수치 피처를 별도 변환 없이 입력으로 유지했다.
- 누적 행 수 기준 약 6:2:2로 시간순 분할하되 동일 timestamp 그룹의 경계를 보존했다.
- 기본값에 가까운 `XGBClassifier`를 학습하고 threshold 0.5에서 Validation과 Test를 평가했다.

## 평가 방법

중복 제거 전후 행 수, 준비된 피처 수, 결측값과 무한값 여부, 시간순 분할의 행 비율과 구간 비중첩 여부를 검증한다. 모델은 threshold 0.5에서 confusion matrix, Accuracy, Precision, Recall, Specificity, F1, ROC-AUC, PR-AUC로 평가한다.

## 주요 결과

- 원본 440,274행에서 `record_id`와 `timestamp`를 제외한 중복 행 48,282건을 제거했다.
- 전처리 후 391,992행과 수치 피처 75개를 준비했다.
- 모델 입력의 결측 셀과 무한값은 모두 0건이다.
- Train은 1970-06-23 03:58:55부터 1970-09-28 05:48:26까지 235,222행(60.007%)이다.
- Validation은 1970-09-28 05:49:10부터 1970-10-13 13:14:26까지 78,374행(19.994%)이다.
- Test는 1970-10-13 13:14:58부터 1970-11-02 14:21:28까지 78,396행(19.999%)이다.
- Test confusion matrix는 TN 75,137건, FP 1,010건, FN 1,659건, TP 590건이다.
- Test Accuracy 0.965955, Precision 0.368750, Recall 0.262339, Specificity 0.986736, F1 0.306573이다.
- Test ROC-AUC는 0.846314, PR-AUC는 0.236803이다.

## 운영 관점 핵심 지표

- **PR-AUC: 0.236803** — 모든 임계값에 걸쳐 실제 불량(`class=1`) 탐지의 Precision-Recall 성능을 평가한다.
- **Real Defect Recall: 0.262339** — threshold 0.5에서 `TP / (TP + FN) = 590 / 2,249`로 계산한다.
- **False Call Reduction: 0.986736** — `TN / (TN + FP) = 75,137 / 76,147`로 계산한다.

| Model | PR-AUC | Threshold | Real Defect Recall | TP | FN | False Call Reduction |
|---|---:|---:|---:|---:|---:|---:|
| XGBoost baseline | 0.237 | 0.500 | 26.2% | 590 | 1,659 | 98.7% |

## 결론 및 다음 단계

- 요청한 최소 전처리와 시간 차이를 무시한 중복 제거를 완료했다.
- timestamp 그룹 경계를 보존한 시간순 Train/Validation/Test 분할을 완료했다.
- 기본 XGBoost는 Accuracy가 높지만 실제 불량 2,249건 중 1,659건을 놓쳐 Recall이 0.262339에 그쳤다.
- 다음 단계에서 추가 커스텀 평가 지표와 임계값 정책을 적용한다.

## 저장 모델

`models/0824_kimjaehak_005_xgboost_baseline.pkl`

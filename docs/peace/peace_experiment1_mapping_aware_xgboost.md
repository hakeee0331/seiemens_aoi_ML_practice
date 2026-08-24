# peace_experiment1_mapping_aware_xgboost

## 연결된 노트북

`notebooks/peace_experiment1_mapping_aware_xgboost.ipynb`

## 상태

구현 완료 · 전체 학습/최종 평가 전

## 1. 실험 목적

Siemens AOI 데이터의 5개 `inspection_type`을 하나의 XGBoost 모델로 학습하되, `mapping.json`을 이용해 검사유형별로 유효하지 않은 `inspection_feat` 값을 구조적 결측치로 처리한다.

모델은 시간순 분할, Train 전용 전처리, 클래스 불균형 보정, Early Stopping을 사용해 학습한다. 앞의 70%에서 Walk-forward로 학습 방식을 선택하고, Final Validation/Calibration 10%에서 Real Defect Recall 97% 이상을 만족하는 임계값 중 False Call Reduction이 가장 높은 값을 선택한다. 고정된 모델과 임계값으로 마지막 Test 20%의 Recall 95% 달성 여부를 검증한다.

## 2. 핵심 가설

- `inspection_type`과 `meta_feat1`∼`meta_feat4`를 범주형으로 명시하고, 유형별 미사용 검사 피처를 `NaN`으로 마스킹하면 피처 의미가 섞이는 문제를 줄일 수 있다.
- 통합 모델은 Type 0·4처럼 positive 표본이 적은 유형의 분산을 줄이면서도 `inspection_type`과 측정값의 상호작용을 트리 분기로 학습할 수 있다.
- 시간적 분포 변화가 크므로 한 번의 Validation 성능보다 Walk-forward Evaluation의 안정성이 운영 재현성을 더 잘 대변한다.

## 3. 고정 용어와 지표

- Positive class: `class == 1` (Real Defect)
- Negative class: `class == 0` (False Call)
- `PR-AUC`: `average_precision_score(y_true, probability)`
- `Real Defect Recall`: `TP / (TP + FN)`
- `False Call Reduction`: `TN / (TN + FP)`
- 판정 규칙: `probability >= threshold`이면 `class=1`, 그렇지 않으면 `class=0`
- Final Validation/Calibration 임계값 조건: `Real Defect Recall >= 0.97`
- 최종 Test 최소 목표: `Real Defect Recall >= 0.95`
- 랜덤 시드: `42`

Accuracy는 보조 지표로만 출력하고 모델, 임계값 또는 실험 전략 선택에 사용하지 않는다.

## 4. 입력 파일과 스키마

### 4.1 파일

- 표준 원본 데이터: `data/raw/dataset.csv`
- 표준 검사유형 매핑: `data/raw/mapping.json`
- Jupyter 커널의 현재 작업 디렉터리가 저장소 루트인지 `notebooks/`인지에 의존하지 않도록 `Path.cwd()`부터 다음 순서로 존재 여부를 검사한다: `data/raw/`, `../data/raw/`, `./`, `../`, `../../`.
- 각 디렉터리에서 `dataset.csv`와 `mapping.json` 두 파일이 모두 존재할 때만 유효한 후보로 인정한다.
- 여러 후보가 나오면 `data/raw/` 표준 경로를 우선하고, 선택된 파일의 SHA-256가 다른 복사본이 있으면 실행을 중단한다.
- 실제로 사용한 절대경로와 SHA-256을 최종 산출물에 기록한다.

### 4.2 컬럼 역할

- 식별자: 첫 번째 `Unnamed:*` 컬럼을 `record_id`로 변경
- 시간: `timestamp`, UTC datetime으로 변환
- 타깃: `class`, `{0, 1}`만 허용
- 범주형: `inspection_type`, `meta_feat1`, `meta_feat2`, `meta_feat3`, `meta_feat4`
- 연속형: `inspection_feat*`
- 모델 입력 제외: `record_id`, `timestamp`, `class`

원본 파일은 수정·덮어쓰기·저장하지 않는다.

## 5. 필수 데이터 검증

노트북은 학습 전에 다음 assert를 모두 통과해야 한다.

1. 행 수 `440,274`
2. `record_id` 고유값 수가 행 수와 일치
3. `class` 값은 `{0, 1}`
4. `class=1` 행 `4,622`, `class=0` 행 `435,652`
5. `inspection_type` 값은 `{0, 1, 2, 3, 4}`
6. `mapping.json` 키를 정수로 변환했을 때 `{0, 1, 2, 3, 4}`
7. 매핑이 참조하는 모든 피처가 CSV에 존재
8. `timestamp` 파싱 실패 0건
9. 수치형 입력의 무한값 0건
10. 전체 검사 피처 70개, 적어도 한 Type에 매핑된 피처 65개

검증 실패 시 경고만 출력하고 계속하지 말고 실행을 중단한다.

## 6. 최종 시간순 분할

### 6.1 분할 원칙

- 중복을 제거하기 전에 원본 전체 데이터를 `timestamp`, `record_id` 순으로 stable sort한다.
- 경계는 전체 행의 누적 비율에 가장 가까운 `timestamp` 그룹의 끝으로 정한다.
- 같은 `timestamp` 그룹을 두 split으로 나누지 않는다.
- 행 단위 무작위 분할을 사용하지 않는다.

### 6.2 최종 holdout

| 구간 | 누적 행 비율 | 용도 |
|---|---:|---|
| Walk-forward 개발 / Final Train | 0∼70% | Walk-forward 후보 비교 후 최종 모델 학습·전처리 fit |
| Final Validation/Calibration | 70∼80% | 최종 Early Stopping·임계값 선택 |
| Final Test | 80∼100% | 모든 결정 고정 후 1회 평가 |

분할 후 각 구간의 행 수, timestamp 그룹 수, positive 수/비율, 시작·종료 시간을 표로 출력한다. 분할 경계가 겹치지 않고 합계 행 수가 전체 행 수와 같음을 assert한다.

## 7. Walk-forward 검증

Final Validation/Calibration 10%와 Final Test 20%는 Walk-forward 후보 비교가 완료될 때까지 사용하지 않는다. 앞의 개발 구간 70% 안에서만 다음 3개 expanding-window Fold를 구성한다.

| Fold | Train | Calibration | Evaluation |
|---:|---:|---:|---:|
| 1 | 0∼30% | 30∼40% | 40∼50% |
| 2 | 0∼40% | 40∼50% | 50∼60% |
| 3 | 0∼50% | 50∼60% | 60∼70% |

모든 분할 경계는 6절과 동일하게 누적 행 비율과 `timestamp` 그룹 경계를 사용한다.

각 Fold에서:

1. 전처리기와 피처 선택기를 Fold Train에만 fit한다.
2. Fold Train으로 XGBoost를 학습하고 Calibration을 Early Stopping에 사용한다.
3. Calibration 예측 확률로 Recall 97% 조건의 임계값을 선택한다.
4. 모델과 임계값을 고정하고 바로 다음 Evaluation 구간을 평가한다.
5. Calibration과 Evaluation의 PR-AUC, threshold, Recall, TP, FN, FP, TN, False Call Reduction을 모두 기록한다.

Evaluation은 해당 Fold의 모델 fit, Early Stopping, threshold 선택에 사용하지 않는다. 다만 모든 Fold가 완료된 후 12절의 후보 조합 비교에는 Evaluation 성능을 사용한다. 이전 Fold의 Evaluation 구간이 다음 Fold의 Calibration 또는 Train에 포함되는 것은 expanding-window 개발 절차의 의도된 동작이다.

## 8. Mapping-aware 통합 전처리

### 8.1 구조적 결측 마스킹

1. CSV의 모든 `inspection_feat*`를 찾는다.
2. `mapping.json`의 5개 목록의 합집에 없는 5개 피처는 전역 제외한다.
3. 각 행의 `inspection_type=t`에 대해 `mapping[str(t)]`에 없는 검사 피처를 `np.nan`으로 변경한다.
4. 마스킹은 외부에서 제공된 스키마 규칙이므로 split별로 동일하게 적용하되, 데이터 통계량을 사용하지 않는다.

0, 특정 상수, 값 범위로 미사용 피처를 추정하지 않는다. 유효성의 유일한 기준은 `mapping.json`이다.

### 8.2 범주형 인코딩

- `inspection_type`, `meta_feat1`∼`meta_feat4`는 숫자 크기의 순서 의미를 가지지 않는 범주형이다.
- `OneHotEncoder(handle_unknown="ignore", dtype=np.float32, sparse_output=False)`를 사용한다. 설치된 scikit-learn이 구버전이면 동일한 동작의 `sparse=False`를 사용한다.
- 인코더는 각 Fold Train 또는 Final Train에만 fit한다.
- Calibration, Evaluation, Validation, Test의 알 수 없는 범주는 모두 0인 벡터로 변환된다.
- 65개 mapping 대상 검사 피처는 스케일링·결측값 대체 없이 passthrough한다. XGBoost가 `NaN`의 기본 분기 방향을 학습한다.

밀집 `float32` 출력을 고정해 One-hot의 0이 sparse matrix의 구조적 결측으로 해석될 여지를 없앤다. 메모리 사용량을 출력하고 Fold 종료 후 대용량 임시 배열과 모델 참조를 제거한다.

### 8.3 Train 기준 피처 제거

- 전역 미매핑 5개 검사 피처는 항상 제거한다.
- 마스킹 후 Fold/Final Train에서 비결측 고유값이 1개 이하인 연속형 피처만 상수열로 제거한다.
- 준상수·저분산 제거는 이 실험에서 적용하지 않는다. 임의 기준으로 희소한 positive 신호를 제거하는 것을 방지하기 위함이다.
- 제거 목록은 학습 구간에서 확정한 후 미래 구간에 그대로 적용한다.

## 9. Train 전용 중복 처리 비교

Validation, Calibration, Evaluation, Test의 행은 제거하거나 가중치를 변경하지 않고 실제 빈도를 유지한다. 각 학습 구간에서만 다음 3개 전략을 비교한다.

### A. `keep`

- Train의 모든 행을 그대로 사용한다.
- 기본 비교 기준이다.

### B. `exact_dedup`

- `record_id`를 제외한 모든 원본 컬럼, 즉 `timestamp`, `class`, 메타 피처, 검사 피처가 모두 같은 Train 행만 완전 중복으로 정의한다.
- stable time sort의 첫 행을 남기고 초과 행을 Train에서만 제거한다.
- `timestamp`가 다른 반복 생산 행은 제거하지 않는다.

### C. `signature_weight`

- signature 컬럼은 `record_id`, `timestamp`, `class`를 제외한 모든 원본 입력 컬럼이다.
- Train 내 각 signature 그룹 크기를 `n_g`라 할 때 각 행의 중복 가중치를 `1 / n_g`로 설정한다.
- 행을 제거하지 않으므로 label-conflict signature의 라벨 비율을 그대로 보존한다.
- pandas 64-bit hash로 signature를 계산하되, 해시는 학습 가중치 계산에만 사용하고 영구 식별자로 저장하지 않는다.

`signature_weight`와 클래스 가중치를 함께 사용할 때는 XGBoost에 전달되는 최종 행 가중치를 별도 표로 검증한다. `scale_pos_weight`는 positive gradient에 추가로 곱해지므로 중복 가중치와 중복 적용되는 것이 의도된 조합인지 결과 표에 명시한다.

## 10. XGBoost 학습

### 10.1 공통 파라미터

```python
XGBClassifier(
    objective="binary:logistic",
    eval_metric="aucpr",
    tree_method="hist",
    n_estimators=3000,
    learning_rate=0.03,
    max_depth=5,
    min_child_weight=10,
    subsample=0.8,
    colsample_bytree=0.8,
    gamma=0.0,
    reg_alpha=0.1,
    reg_lambda=5.0,
    max_delta_step=1.0,
    early_stopping_rounds=100,
    random_state=42,
    n_jobs=-1,
)
```

- `eval_set` 순서는 `[(X_calibration, y_calibration)]` 또는 최종 학습에서 `[(X_validation, y_validation)]`로 고정한다.
- Early Stopping이 선택한 `best_iteration`/트리 수와 최적 Calibration/Validation `aucpr`를 저장한다.
- 스케일링, SMOTE, 랜덤 over/under-sampling은 이 실험에서 사용하지 않는다.

### 10.2 클래스 가중치 후보

각 Fold/Final Train의 `negative_count / positive_count`를 `R`로 계산하고 다음 후보를 비교한다.

```text
scale_pos_weight ∈ {1.0, 25.0, 50.0, R}
```

`R`은 각 학습 구간에서만 계산하며 미래 구간의 라벨 비율을 사용하지 않는다. 모든 후보는 같은 Fold, 전처리, 중복 전략에서 비교한다.

### 10.3 실험 조합

- 중복 전략 3개 × `scale_pos_weight` 4개 = Fold당 12개 후보
- 3개 Walk-forward Fold에서 같은 12개 후보를 모두 평가
- 총 36개 Walk-forward 학습
- 하이퍼파라미터 그리드 탐색은 이 실험의 범위에 포함하지 않는다. 목표 미달 시 후속 실험으로 분리한다.

## 11. 임계값 선택 알고리즘

고정 간격 그리드를 사용하지 않고 Fold Calibration과 Final Validation/Calibration의 모든 예측 확률 고유값 전체를 threshold 후보로 사용한다.

```python
def select_threshold(y_true, probability, min_recall=0.97):
    candidates = np.sort(np.unique(probability))[::-1]
    rows = []
    for threshold in candidates:
        prediction = probability >= threshold
        tn, fp, fn, tp = confusion_matrix(
            y_true, prediction, labels=[0, 1]
        ).ravel()
        recall = tp / (tp + fn)
        false_call_reduction = tn / (tn + fp)
        if recall >= min_recall:
            rows.append((threshold, recall, false_call_reduction, tn, fp, fn, tp))

    if not rows:
        raise RuntimeError("Recall 97% condition is infeasible")

    # FCR 최대 → Recall 최대 → threshold 최대
    return max(rows, key=lambda row: (row[2], row[1], row[0]))
```

실제 구현은 모든 임계값마다 전체 배열을 반복 생성하지 않고, 확률 내림차순 정렬과 누적 TP/FP로 동일한 결과를 계산해도 된다. 최적화 구현은 위 참조 구현과 작은 합성 배열에서 결과가 일치함을 우선 검증한다.

임계값 선택 시 동일한 False Call Reduction이면 Recall이 더 높은 값을, 그것도 같으면 더 높은 threshold를 선택한다. 선택된 threshold는 Evaluation/Test 확률을 보고 변경하지 않는다.

## 12. Walk-forward 모델 선택 규칙

각 `duplicate_strategy × scale_pos_weight`에 대해 3개 Fold 결과를 합친다.

1. **안전성 gate:** 3개 Evaluation 모두 Recall 95% 이상인 후보만 최종 후보로 인정한다.
2. **기본 모델 선택 지표:** gate를 통과한 후보 중 3개 Evaluation의 평균 PR-AUC가 가장 높은 조합을 선택한다.
3. **1차 tie-break:** 평균 False Call Reduction이 더 높은 조합
4. **2차 tie-break:** 최저 Evaluation Recall이 더 높은 조합
5. **3차 tie-break:** 더 단순한 전략(`keep` → `exact_dedup` → `signature_weight`), 그런 다음 더 작은 `scale_pos_weight`

각 Evaluation에서 Recall 97% 달성 여부도 별도로 기록한다. 97%는 시간 안정성의 선호 목표이고, 95%는 모델 후보 탈락을 결정하는 안전성 하한이다.

모든 후보가 gate를 통과하지 못하면 최종 Test를 열지 않는다. 그 실험은 목표 미달로 기록하고 피처, 불균형 보정, 파라미터, 데이터·라벨 품질 개선을 후속 실험으로 수행한다.

## 13. 최종 학습과 임계값 고정

Walk-forward에서 선택된 `duplicate_strategy` 및 `scale_pos_weight` 규칙을 다음과 같이 한 번 더 적용한다.

1. Final Train 0∼70%에만 전처리기와 피처 제거 규칙을 fit한다.
2. 선택된 Train 중복 전략을 Final Train에만 적용한다.
3. `scale_pos_weight=R`이 선택된 경우 Final Train에서 `R`을 다시 계산한다. 고정 숫자가 선택되었다면 그 숫자를 사용한다.
4. Final Validation/Calibration 70∼80%를 `eval_set`으로 사용해 Early Stopping을 적용한다.
5. Final Validation/Calibration의 모든 고유 예측 확률 중 Recall 97% 이상을 만족하면서 False Call Reduction이 최대인 threshold를 선택한다.
6. 모델, 전처리, 피처 목록, threshold 및 모든 선택 정보를 고정한다.

XGBoost의 트리 분기와 가중치는 Final Train으로만 학습한다. Final Validation/Calibration 라벨은 gradient 업데이트에 사용하지 않고, 트리가 추가될 때마다 미래 구간의 PR-AUC를 계산해 `best_iteration`을 선택하는 데 사용한다. Train 성능은 트리를 계속 추가할수록 좋아질 수 있으므로, 이 미래 구간을 확인해 과적합 전에 학습을 멈춘다.

Early Stopping으로 트리 수가 고정되면 같은 Final Validation/Calibration의 예측 확률을 이용해 Recall 97% 안전 조건을 만족하는 판정 threshold를 선택한다. Train에서 threshold를 선택하면 모델이 이미 본 데이터에 맞은 낙관적인 값이 될 수 있어 별도의 미래 구간을 사용한다.

Final Validation/Calibration은 Early Stopping과 threshold 선택에 사용되므로 독립적인 최종 성능으로 보고하지 않는다. 독립적인 일반화 성능은 Final Test에서만 보고한다.

## 14. Final Test 실행 게이트

Final Test 예측 셀은 다음 내용이 노트북 출력으로 확정된 후에만 실행한다.

- 선택된 중복 전략
- 선택된 `scale_pos_weight`
- 선택된 XGBoost `best_iteration`
- 최종 피처 목록과 인코딩 컬럼
- Final Validation/Calibration에서 선택된 threshold
- threshold 선택 시의 Final Validation/Calibration confusion matrix
- Final Test 코드가 threshold를 재계산하지 않음을 확인하는 assert

Final Test를 실행한 후 결과를 보고 threshold, 피처, 가중치, 모델 파라미터를 변경하지 않는다. 변경이 필요하면 현 Test를 이미 사용한 실험으로 완결하고, 새로운 미사용 시간 구간을 준비한 별도 실험으로 진행한다.

## 15. Final Test 평가

### 15.1 전체 지표

| Model | PR-AUC | Threshold | Real Defect Recall | TP | FN | FP | TN | False Call Reduction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Mapping-aware integrated XGBoost | 실행 후 기록 | 실행 후 기록 | 실행 후 기록 | 실행 후 기록 | 실행 후 기록 | 실행 후 기록 | 실행 후 기록 | 실행 후 기록 |

### 15.2 필수 하위그룹 평가

- `inspection_type` 0∼4별 행 수, positive 수, PR-AUC, Recall, TP, FN, FP, TN, False Call Reduction
- Test 주차별 동일 지표
- Train/Validation에서 이전에 본 input signature와 처음 보는 signature별 동일 지표
- label-conflict signature와 비충돌 signature별 동일 지표

하위그룹에 positive 샘플이 없으면 PR-AUC와 Recall을 `NaN`/정의 불가로 표시하고 0으로 대체하지 않는다.

### 15.3 판정 순서

1. Test Recall이 95% 이상인가?
2. FN 개수가 운영적으로 허용 가능한가?
3. False Call Reduction이 수동검사를 의미 있게 줄이는가?
4. FP, 즉 여전히 수동검사가 필요한 false call이 몇 건인가?
5. PR-AUC가 기존 XGBoost baseline 0.236803보다 개선됐는가?

Test Recall이 95% 미만이면 목표 미달로 기록한다. Test 결과를 보고 임계값을 낮추거나 다른 모델을 선택하지 않는다.

## 16. 오류 분석

- False Negative를 `inspection_type`, `meta_feat1`∼`meta_feat4`, 주차, seen/unseen signature, label-conflict 여부로 집계한다.
- 특정 Type의 Recall이 전체 Recall보다 크게 낮은지 확인한다.
- 반복 signature가 전체 성능을 과도하게 높이는지 seen/unseen 성능으로 확인한다.
- XGBoost gain importance를 출력하되 인과적 영향으로 해석하지 않는다.
- SHAP은 현재 의존성에 없으므로 이 실험의 필수 산출물에 포함하지 않는다.

## 17. 저장 산출물

모델 파일:

`models/peace_experiment1_mapping_aware_xgboost.pkl`

`joblib.dump` 대상은 다음 키를 포함한 하나의 dictionary로 고정한다.

```text
experiment_id
model
preprocessor
mapping
mapping_sha256
data_sha256
raw_feature_columns
final_feature_names
globally_unmapped_features
train_constant_features
duplicate_strategy
scale_pos_weight_rule
scale_pos_weight_value
decision_threshold
threshold_selection_rule
random_state
train_start_time
train_end_time
validation_start_time
validation_end_time
test_start_time
test_end_time
best_iteration
library_versions
walk_forward_summary
```

모델 파일은 Test 평가 전에 일단 저장하고, Test 성능은 모델 선택에 반영하지 않는 메타데이터로만 추가한다. Test 결과를 추가한 후 모델 가중치, 전처리기, threshold가 이전과 동일함을 체크섬 또는 직렬화 전·후 검증으로 확인한다.

## 18. 노트북 셀 구성

1. 실험 설명과 사전 등록된 규칙
2. 라이브러리 import, 버전, 시드, 경로
3. CSV·mapping 로드와 SHA-256
4. 스키마·데이터 품질 assert
5. stable time sort와 30/40/50/60/70/80% timestamp 경계 생성
6. Final Validation/Calibration·Final Test 조기 접근 금지 안내
7. mapping-aware masking 함수
8. Train-only 상수열 선택·One-hot 전처리기
9. Train-only 중복 전략·signature weight 함수
10. 임계값 선택·평가 함수 및 작은 합성 테스트
11. 3-Fold Walk-forward 12개 후보 실행
12. Fold별·후보별 성능 표와 선택 규칙 적용
13. Final Train 70%로 최종 모델 학습·Final Validation/Calibration 10%로 Early Stopping
14. Final Validation/Calibration에서 threshold 선택·고정
15. 고정된 모델 산출물 저장·reload 추론 일치 검증
16. Final Test 실행 게이트 체크리스트
17. Final Test 1회 추론·전체 지표
18. Type·주차·seen/unseen·label-conflict 하위그룹 평가
19. False Negative 오류 분석
20. 결론, 목표 달성 여부, 다음 실험

## 19. 필수 구현 검증

- [ ] 노트북을 커널 재시작 후 첫 셀부터 끝까지 순서대로 실행했다.
- [ ] 원본 파일의 크기·SHA-256가 실행 전후 같다.
- [ ] 동일 timestamp 그룹이 서로 다른 split/Fold 구간에 없다.
- [ ] 전처리기, 피처 제거, 중복 통계, `R`은 학습 구간에서만 fit/계산됐다.
- [ ] Fold Calibration/Evaluation, Final Validation/Calibration, Final Test 행은 중복 제거·역빈도 가중치의 대상이 아니다.
- [ ] 전역 미매핑 피처 5개가 제거됐다.
- [ ] Type별 미사용 검사 피처가 `mapping.json` 기준으로만 `NaN` 처리됐다.
- [ ] 범주형 인코더가 학습 구간에서만 fit됐다.
- [ ] 임계값 후보는 Fold Calibration과 Final Validation/Calibration의 모든 예측 확률 고유값 전체이다.
- [ ] 임계값 선택 결과가 Recall 97% 조건과 tie-break 규칙을 만족한다.
- [ ] Walk-forward Evaluation 확률과 라벨은 해당 Fold의 fit·Early Stopping·threshold 선택에 사용되지 않았고, Fold 완료 후 후보 조합 비교에만 사용됐다.
- [ ] Final Test threshold는 Final Validation/Calibration에서 고정된 값과 정확히 같다.
- [ ] Test 결과를 본 후 threshold를 재선택하지 않았다.
- [ ] 저장 전·후의 예측 확률과 판정이 일치한다.
- [ ] 저장된 모델 artifact에 피처, 전처리, 임계값, 학습·검증 기간, 선택 규칙이 포함됐다.
- [ ] 최종 Test 지표가 노트북, 본 문서, `docs/model_val.md`에서 일치한다.

## 20. 목표 미달 시 처리

- Fold Calibration 또는 Final Validation/Calibration에서 Recall 97%를 만족하려면 threshold가 매우 낮고 False Call Reduction이 거의 0이라면 모델의 구분 능력 부족으로 해석한다.
- Recall을 포기하고 threshold를 임의로 높이지 않는다.
- Walk-forward 안전성 gate를 통과하지 못하면 Final Test를 사용하지 않는다.
- Final Validation/Calibration 97%를 만족해도 Test Recall이 95% 미만이면 실험을 목표 미달로 기록한다.
- 피처, 불균형 보정, 파라미터, 데이터·라벨 품질 개선은 새 실험 ID에서 수행한다.

## 21. 실험 완료 후 문서 갱신

노트북을 전체 실행한 뒤 다음을 갱신한다.

1. 본 문서의 상태를 `완료` 또는 `목표 미달`로 변경
2. Walk-forward 후보별 요약, 선택 조합, Final Validation/Calibration 임계값, Final Test 결과 기록
3. `docs/experiments/index.md`에 실험 행 추가
4. Final Test를 수행했다면 `docs/model_val.md`에 비교 행 추가
5. 노트북·문서·모델의 stem이 일치하는지 확인

## 22. 저장 모델

구현 전이므로 현재 저장된 모델은 없다.

노트북 실행 후 다음 경로에 저장한다.

`models/peace_experiment1_mapping_aware_xgboost.pkl`

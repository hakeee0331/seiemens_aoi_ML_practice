# 0825_kimjaehak_017_dongjin_026_threshold_fix

## 연결된 노트북

`notebooks/0825_kimjaehak_017_dongjin_026_threshold_fix.ipynb`

## 상태

완료

## 목적

`0826_dongjin_026_saved_ensemble_shap`이 고정 Threshold `0.5`에서 발생한 False Call만 분석했다는 점을 확인하고, 동일한 `peace_005` 저장 모델에서 Validation 선택 공통 Threshold를 적용했을 때 실제 SHAP 분석 대상과 중요 피처 순위가 어떻게 달라지는지 검증한다.

원본 `dongjin_026` 노트북은 수정하지 않고 별도 후속 실험으로 수행한다.

## 주요 변경사항

- `models/0825_peace_005_type_expert_fold_ensemble.pkl`을 `joblib`으로 로드했다.
- 저장 artifact의 schema 1·2를 모두 지원하도록, `validation_end_time`이 없으면 원본 timestamp group의 80% 경계를 동일 규칙으로 재계산했다.
- 모델 번들의 dataset 및 mapping SHA256과 현재 원본 파일이 일치하는지 확인했다.
- 고정 `0.5`와 모델 번들에 저장된 Validation 공통 Threshold `0.0007097449`를 같은 Test 확률에 적용했다.
- 두 정책의 confusion matrix를 `peace_005` 기준 결과와 assertion으로 대조했다.
- 각 정책에서 `class=0`, `prediction=1`인 False Call만 분리해 검사유형별 SHAP를 계산했다.
- 네 체크포인트 XGBoost 구성원의 raw-margin `mean(abs(SHAP))`를 동일 가중 평균했다.
- 실행 환경에 없던 `shap==0.52.0`을 프로젝트 의존성에 추가했다.

## 평가 방법

- 데이터 처리: 중복 제거하지 않은 원본 데이터
- Test: 시간순 마지막 20%, 88,052행
- Test 기간: 1970-10-13 16:54:52 UTC ~ 1970-11-02 14:21:28 UTC
- 실제 불량: 2,325건
- Fixed 정책: Threshold `0.5`
- Global 정책: 70~80% Validation에서 선택해 모델 번들에 저장된 Threshold `0.0007097449`
- Test는 Threshold 선택에 사용하지 않았다.

## Threshold별 Test 결과

| 정책 | Threshold | PR-AUC | Recall | False Call Reduction | False Call Rate | TP | FN | FP | TN |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Fixed | 0.5000000000 | 0.382545 | 17.55% | 99.81% | 0.19% | 408 | 1,917 | 159 | 85,568 |
| Validation Global | 0.0007097449 | 0.382545 | 93.94% | 52.04% | 47.96% | 2,184 | 141 | 41,118 | 44,609 |

두 confusion matrix 모두 기존 `peace_005` 최종 Test 결과와 정확히 일치했다. 반면 `dongjin_026` 출력은 고정 `0.5`에서 FP 166건을 사용했으므로, 실행에 사용한 저장 모델 artifact가 기준 결과와 달랐던 것으로 판단한다.

## 검사유형별 False Call 변화

| Inspection Type | Fixed 0.5 FP | Global FP | Global False Call Rate |
|---:|---:|---:|---:|
| 0 | 0 | 8,282 | 42.92% |
| 1 | 70 | 7,863 | 67.92% |
| 2 | 7 | 11,067 | 55.86% |
| 3 | 82 | 13,191 | 38.43% |
| 4 | 0 | 715 | 100.00% |

고정 `0.5`에서는 Type 1~3의 FP 159건만 설명하지만, 공통 Threshold에서는 모든 유형에 걸친 FP 41,118건을 설명해야 한다.

## Threshold별 SHAP 상위 피처

표의 피처 순서는 각 검사유형 내부 `member mean |SHAP|` 상위 5개다.

| Type | Fixed 0.5 Top 5 | Validation Global Top 5 | Top 5 Jaccard |
|---:|---|---|---:|
| 0 | 해당 없음(FP 0건) | `inspection_feat41`, `meta_feat2=1`, `inspection_feat24`, `meta_feat1=10`, `meta_feat4=0` | 0.000 |
| 1 | `inspection_feat24`, `inspection_feat48`, `inspection_feat8`, `meta_feat4=28`, `meta_feat1=22` | `inspection_feat48`, `inspection_feat24`, `meta_feat1=22`, `meta_feat4=28`, `inspection_feat4` | 0.667 |
| 2 | `inspection_feat96`, `meta_feat1=27`, `meta_feat4=3`, `inspection_feat22`, `meta_feat4=41` | `meta_feat1=27`, `inspection_feat96`, `inspection_feat12`, `inspection_feat22`, `inspection_feat95` | 0.429 |
| 3 | `inspection_feat22`, `inspection_feat95`, `meta_feat4=7`, `inspection_feat12`, `meta_feat1=27` | `inspection_feat12`, `meta_feat4=7`, `meta_feat1=27`, `inspection_feat96`, `inspection_feat95` | 0.667 |
| 4 | 해당 없음(FP 0건) | 모든 피처의 SHAP가 0 | 0.000 |

## 해석

- Threshold가 `0.5`에서 `0.0007097449`로 낮아지면서 SHAP 분석 대상이 159건에서 41,118건으로 약 259배 증가했다.
- Type 1과 Type 3은 일부 핵심 피처를 공유했지만 Top 5가 완전히 같지는 않았다.
- Type 2의 Fixed 결과는 FP가 7건뿐이라 일반화하기 어렵고, 공통 Threshold에서는 더 넓은 정상 데이터 영역을 설명한다.
- Type 0과 Type 4는 Fixed 분석 대상이 없지만 공통 Threshold에서는 각각 8,282건과 715건의 FP가 발생한다.
- Type 4는 공통 Threshold에서 정상 715건 전체를 불량으로 판정하며 모든 구성 모델의 SHAP가 0이다. 모델이 유형 내부 순위를 만들지 못하는 상수 출력에 가깝기 때문에 별도 Threshold 또는 별도 fallback 정책이 필요하다.

## 결론 및 다음 단계

- `dongjin_026`의 고정 `0.5` SHAP는 고확률 FP 사례를 설명하는 분석으로는 의미가 있다.
- 하지만 이를 `peace_005`의 Recall 중심 공통 Threshold 정책에서 발생하는 False Call 원인으로 일반화할 수 없다.
- 운영 정책을 설명하려면 실제 적용 Threshold별로 SHAP 분석 집단을 다시 정의해야 한다.
- 다음 검증에서는 공통 Threshold FP와 TN의 signed SHAP 차이를 비교하고, 실제 FP·FN 비용을 적용해 Threshold 정책을 선택해야 한다.

## 한계

- 네 모델의 raw-margin SHAP 중요도를 평균한 결과이며, 확률 평균 앙상블 출력의 정확한 additive SHAP는 아니다.
- FP 집단 내부에서 영향이 컸던 피처 순위이므로 오판의 인과 원인으로 해석할 수 없다.
- Test SHAP 결과를 후속 피처 선택에 사용한다면 새로운 미래 Holdout에서 다시 평가해야 한다.

## 저장 모델

새 모델은 저장하지 않았다. 다음 기존 모델을 읽기 전용으로 사용했다.

`models/0825_peace_005_type_expert_fold_ensemble.pkl`

## 모델 평가 목록

새 모델이나 새로운 Test 정책을 제안한 실험이 아니라 기존 두 Threshold의 해석 대상을 검증한 진단 실험이므로 `docs/model_val.md`에는 추가하지 않았다.

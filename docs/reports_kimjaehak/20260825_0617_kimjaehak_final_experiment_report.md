# Kimjaehak Sandbox 실험 최종 보고서

## 보고서 정보

- 작성자: `kimjaehak`
- 작성 일시: 2026-08-25 06:17 KST
- 작업 브랜치: `sandbox/kimjaehak/multi-experiments`
- 실험 범위: `kimjaehak_007` ~ `kimjaehak_014`, `kimjaehak_016`
- 기준 모델: `kimjaehak_006` mapping 기반 inspection type별 XGBoost

이 문서는 이번 sandbox에서 직접 진행한 `kimjaehak` 실험만 정리한다. 팀원이 `dev`에 추가한 실험이나 프로젝트 전체 성과는 포함하지 않는다.

여기서 말하는 최종 모델은 저장된 운영 모델 파일이 아니라, 오늘 실험 결과를 통해 남은 **champion 모델 구조와 의사결정 정책 후보**를 뜻한다.

---

## 1. 최종 요약

오늘 실험의 출발점은 다음 질문이었다.

> 시간이 뒤로 갈수록 `class=1`이 증가하는데, 기존 고정 모델을 그대로 사용해도 되는가?

실험 결과는 다음과 같이 정리된다.

1. 후반부 `class=1` 증가는 inspection type 구성 변화만으로 설명되지 않았다.
2. 동일 입력이 후반에 `0→1`로 판정되는 정황과 입력 피처 분포 변화가 동시에 발견됐다.
3. 따라서 현재 문제는 단순한 label drift가 아니라 **라벨·개념 변화와 피처 drift가 함께 존재하는 혼합 drift**로 보는 것이 타당하다.
4. 고정 모델에서 threshold나 calibration만 갱신하는 방법은 일부 지표를 개선했지만 시간에 따라 안정적으로 작동하지 않았다.
5. 최근 데이터를 누적해 다시 학습하는 **Expanding 재학습**은 비용이나 threshold를 제외하고도 Fixed 모델보다 순위 성능이 좋았다.
6. Expanding 모델에 직전 구간 비용 threshold를 적용하면 1:50~1:100 비용 가정에서 추가적인 비용 감소가 확인됐다.

현재까지의 최종 후보 구조는 다음과 같다.

```text
전체 데이터 로드 및 중복 제거
            ↓
mapping.json 기반 inspection type별 유효 피처
            ↓
inspection type별 XGBoost 5개
            ↓
최근 데이터를 누적하는 Expanding 재학습
            ↓
inspection type별 비용 threshold
            ↓
표본이 부족한 type은 수동 재검사 fallback
```

### 핵심 성능 개선

| 비교 항목 | 기존 Fixed | 최종 Expanding 후보 | 변화 |
|---|---:|---:|---:|
| W08~W10 aggregate pooled PR-AUC | 0.298083 | **0.344535** | +0.046452, 약 +15.6% |
| 평균 positive-weighted type PR-AUC | 0.404530 | **0.472470** | +0.067940, 약 +16.8% |
| Aggregate Brier score | 0.020556 | **0.018689** | 개선 |
| Aggregate log loss | 0.106902 | **0.100548** | 개선 |

비용비율을 FP:FN = 1:100으로 가정하면 다음과 같다.

| 모델 및 정책 | 총비용 | Recall | False Call Reduction | FN |
|---|---:|---:|---:|---:|
| Expanding + raw threshold 0.5 | 171,225 | 33.89% | 99.20% | 1,703 |
| Fixed + raw empirical 비용 threshold | 91,747 | 72.52% | 81.79% | 708 |
| **Expanding + raw empirical 비용 threshold** | **69,627** | **79.43%** | **85.54%** | **530** |
| 전량 수동 재검사 | 115,014 | 100.00% | 0.00% | 0 |

Expanding + raw empirical 비용 정책은 다음과 같이 개선됐다.

- Expanding raw threshold 0.5 대비 비용 **59.34% 감소**
- 동일한 raw empirical 정책의 Fixed 모델 대비 비용 **24.1% 감소**
- 전량 재검사 대비 비용 **45,387 감소**
- W08~W10 세 구간 모두 raw threshold 0.5보다 비용이 낮았음

다만 이 정책에서도 실제 불량 530건을 놓쳤다. 비용 최적화가 안전성을 자동으로 보장하는 것은 아니다.

---

## 2. 실험을 시작한 배경

기준 모델인 `kimjaehak_006`은 다음 구조였다.

- baseline과 동일한 중복 제거
- 시간순 Train/Validation/Test 분할
- `mapping.json`에 정의된 inspection type별 유효 피처 사용
- inspection type별 XGBoost 5개 학습
- 기존 Test pooled PR-AUC: 0.315411
- threshold 0.5 Recall: 31.61%

그러나 시간 후반으로 갈수록 `class=1` 비율이 커졌다. 고정된 과거 모델의 확률과 threshold가 미래에도 같은 의미를 갖는지 확인할 필요가 있었다.

오늘 실험은 크게 네 방향으로 진행됐다.

1. drift의 종류 진단
2. threshold와 calibration을 이용한 의사결정 대응
3. 재학습을 이용한 모델 적응
4. 리샘플링과 피처 축소의 추가 개선 가능성 검증

---

## 3. 최종 모델까지 진행된 과정

## 3.1 `kimjaehak_007`: 후반 라벨 증가 원인 진단

### 질문

후반부 `class=1` 증가는 inspection type 구성 변화, 라벨 판정 기준 변화, 입력 피처 변화 중 무엇 때문인가?

### 주요 결과

- W01 `class=1` 비율: 0.186177%
- W10 `class=1` 비율: 3.336820%
- 전체 증가: +3.150643%p
- inspection type 구성 효과: -0.270803%p
- 유형 내부 라벨률 효과: +3.421446%p

검사유형 구성이 바뀌어서 전체 불량률이 증가한 것이 아니었다. 같은 inspection type 내부에서 `class=1`이 증가한 효과가 지배적이었다.

동일 측정 signature에서 서로 다른 라벨이 등장한 70개 그룹을 확인한 결과는 다음과 같다.

- 최초 라벨 등장 순서 `0→1`: 57개
- 최초 라벨 등장 순서 `1→0`: 13개
- exact binomial p-value: `1.029e-07`

후반부에 동일한 입력이 `1`로 처음 판정되는 방향의 비대칭이 강했다.

그러나 피처 분포도 함께 변했다.

- mapping 유효 피처의 미래 PSI 비교: 452개
- PSI 0.25 이상: 162개
- Type 4와 Type 3에서 특히 큰 변화 확인

### 결론

라벨 기준이 후반에 엄격해졌을 가능성은 있지만, 입력 `X` 분포도 함께 변했다. 따라서 문제를 순수 label drift로 보지 않고 **혼합 drift**로 정의했다.

이 결론 때문에 단순히 최근 라벨을 정답으로 덮어쓰거나 시간가중치만 주는 대신, 시간순 walk-forward 검증으로 대응 방법을 확인하게 됐다.

관련 파일:

- [실험 보고서](../experiments/0825_kimjaehak_007_label_shift_diagnosis.md)
- [노트북](../../notebooks/0825_kimjaehak_007_label_shift_diagnosis.ipynb)

---

## 3.2 `kimjaehak_008`: 직전 구간 threshold 갱신

### 질문

모델은 고정하고, 직전 구간에서 Slip Rate 1%를 만족하는 type별 threshold를 선택하면 다음 구간에서도 안전할까?

### 주요 결과

| 정책 | Slip Rate | Recall | False Call Reduction | FN |
|---|---:|---:|---:|---:|
| 고정 threshold 0.5 | 66.2655% | 33.7345% | 98.9167% | 1,707 |
| Walk-forward type threshold | **2.6398%** | **97.3602%** | 11.6925% | **68** |

미검출은 크게 감소했지만 정상 건을 자동 통과시키는 효과도 대부분 사라졌다.

기간별 Slip Rate는 다음과 같았다.

- W08: 0.6116%
- W09: 2.2317%
- W10: 3.4404%

### 결론

직전 기간에서 Slip Rate 1%를 만족한 threshold도 다음 기간에서 동일한 안전성을 보장하지 못했다. 안전성을 높이기 위해 재검사 절감 대부분을 포기했는데도 목표를 유지하지 못했으므로 운영 정책으로 채택하지 않았다.

이 결과로 raw score threshold 자체의 시간 불안정성을 확인했고, 다음 단계에서 확률 calibration을 검토했다.

관련 파일:

- [실험 보고서](../experiments/0825_kimjaehak_008_walk_forward_threshold.md)
- [노트북](../../notebooks/0825_kimjaehak_008_walk_forward_threshold.ipynb)

---

## 3.3 `kimjaehak_010`: type별 확률 calibration

### 질문

직전 기간의 raw score를 확률로 보정하면 하나의 비용 threshold를 사용할 수 있을까?

### 주요 결과

FP:FN 비용을 1:100으로 가정했다.

| 정책 | 총비용 | Slip Rate | False Call Reduction | FN |
|---|---:|---:|---:|---:|
| Raw score threshold 0.5 | 171,946 | 66.2655% | 98.9167% | 1,707 |
| Raw score 비용 threshold | 98,508 | 35.1320% | 93.0374% | 905 |
| Platt calibrated 비용 threshold | **88,644** | **25.5435%** | 80.1381% | **658** |

같은 수치의 비용 threshold에서 calibration은 raw 정책보다 비용을 9,864 줄였다.

확률 품질은 일관되지 않았다.

- 전체 log loss: 0.106902 → 0.095347로 개선
- 전체 Brier score: 0.020556 → 0.022032로 악화
- W08 Brier는 개선
- W09와 W10 Brier는 악화

### 결론

Calibration은 비용 관점의 가능성을 보여줬지만 시간에 따라 확률 품질이 흔들렸다. 또한 이 실험의 raw 정책은 raw score에서 직접 비용을 최소화한 threshold가 아니라 calibrated probability와 동일한 수치 threshold를 사용한 비교였다.

따라서 calibration을 최종 채택하지 않고, 고정 모델 자체가 drift에 적응하지 못한다는 가정을 다음 실험에서 검증했다.

관련 파일:

- [실험 보고서](../experiments/0825_kimjaehak_010_type_probability_calibration.md)
- [노트북](../../notebooks/0825_kimjaehak_010_type_probability_calibration.ipynb)

---

## 3.4 `kimjaehak_011`: Fixed, Expanding, Rolling-6 재학습 비교

### 질문

Threshold만 바꾸는 대신 모델을 최근 데이터로 다시 학습하면 drift 대응이 개선될까?

### 비교 방법

- Fixed: 모든 fold에서 W01~W06 학습
- Expanding: calibration 직전까지의 모든 데이터를 누적 학습
- Rolling-6: calibration 직전의 최근 6개 window만 학습
- 직전 구간에서 safety threshold 선택 후 다음 구간 적용

### 주요 결과

| 학습 방식 | PR-AUC | Slip Rate | False Call Reduction | FN | 비용 1:100 |
|---|---:|---:|---:|---:|---:|
| Fixed | 0.298083 | **2.6398%** | 11.6925% | **68** | 108,366 |
| Expanding | **0.344535** | 2.9503% | **18.4804%** | 76 | **101,359** |
| Rolling-6 | 0.320067 | 3.4550% | 15.6833% | 89 | 105,876 |

Expanding은 Fixed보다 다음과 같이 개선됐다.

- PR-AUC: +0.046452
- TN: +7,807
- 비용: -7,007

하지만 FN은 8건 증가했고 기간별 결과도 일관적이지 않았다.

- W09: Expanding의 FN이 Fixed보다 18건 많음
- W10: Expanding의 FN이 Fixed보다 10건 적음

### 결론

Expanding은 모델 적응 관점에서 가장 유망했지만, 당시에는 safety threshold 효과와 모델 자체의 성능 개선이 섞여 있었다. 따라서 최종 선택 전에 비용과 threshold를 완전히 제거한 별도 비교가 필요했다.

관련 파일:

- [실험 보고서](../experiments/0825_kimjaehak_011_walk_forward_retraining.md)
- [노트북](../../notebooks/0825_kimjaehak_011_walk_forward_retraining.ipynb)

---

## 3.5 `kimjaehak_013`: 비용을 제외한 순수 모델 성능 비교

### 질문

Expanding의 개선은 threshold 선택 덕분인가, 아니면 모델 자체가 더 좋아진 것인가?

### 비교 원칙

- 비용 사용 안 함
- threshold 사용 안 함
- confusion matrix를 모델 선택에 사용하지 않음
- type별 PR-AUC를 실제 불량 수로 가중한 지표를 주 지표로 사용
- 다음 비용 실험이 같은 모델 예측을 사용하도록 직전 calibration window를 학습에서 제외

### 전체 결과

| 학습 방식 | 평균 positive-weighted type PR-AUC | Aggregate pooled PR-AUC | Brier | Log loss |
|---|---:|---:|---:|---:|
| Fixed | 0.404530 | 0.298083 | 0.020556 | 0.106902 |
| Expanding | **0.472470** | **0.344535** | **0.018689** | **0.100548** |
| Rolling-6 | 0.445486 | 0.320067 | 0.018792 | 0.109278 |

기간별 positive-weighted type PR-AUC는 다음과 같았다.

| 평가 구간 | Fixed | Expanding | Rolling-6 |
|---|---:|---:|---:|
| W08 | 0.458541 | 0.458541 | 0.458541 |
| W09 | 0.388373 | **0.451414** | 0.439031 |
| W10 | 0.366676 | **0.507455** | 0.438885 |

W08에서는 세 방식의 학습 데이터가 같아 결과가 동일했다. 재학습 효과가 생기는 W09와 W10에서는 Expanding이 모두 Fixed보다 높았다.

### 결론

비용과 threshold를 사용하지 않아도 Expanding이 가장 좋은 모델이었다. 따라서 `kimjaehak_011`에서 확인한 개선은 단순 threshold 효과가 아니라 모델의 불량 순위화 능력이 실제로 개선된 결과다.

이 결과에 따라 최종 모델 후보를 **Expanding type-conditioned XGBoost**로 고정하고 비용 의사결정을 별도 실험으로 분리했다.

관련 파일:

- [실험 보고서](../experiments/0825_kimjaehak_013_cost_free_model_performance.md)
- [노트북](../../notebooks/0825_kimjaehak_013_cost_free_model_performance.ipynb)

---

## 3.6 `kimjaehak_014`: 최종 후보의 비용 최적화

### 질문

비용 없이 선택한 Expanding 모델에 비용 기반 threshold를 추가하면 다음 기간의 총비용이 감소할까?

### 비교 정책

- Raw threshold 0.5
- 직전 구간에서 실제 비용을 최소화한 raw empirical threshold
- 희소 type을 전량 재검사하는 guarded threshold
- Platt calibration 후 이론적 비용 threshold
- 전량 수동 재검사

비용비율은 FP 비용을 1로 두고 FN 비용을 10, 25, 50, 100, 200으로 바꿔 확인했다.

### 비용비율 1:100 결과

| 모델 | 정책 | 총비용 | FP | FN | Recall | False Call Reduction |
|---|---|---:|---:|---:|---:|---:|
| Fixed | Raw 0.5 | 171,946 | 1,246 | 1,707 | 33.73% | 98.92% |
| Fixed | Raw empirical | 91,747 | 20,947 | 708 | 72.52% | 81.79% |
| Fixed | Platt analytic | **88,666** | 22,766 | 659 | 74.42% | 80.21% |
| Expanding | Raw 0.5 | 171,225 | 925 | 1,703 | 33.89% | 99.20% |
| **Expanding** | **Raw empirical** | **69,627** | **16,627** | **530** | **79.43%** | **85.54%** |
| Expanding | Platt analytic | 81,747 | 17,747 | 640 | 75.16% | 84.57% |
| All manual | 전량 재검사 | 115,014 | 115,014 | 0 | 100.00% | 0.00% |

### 비용비율 민감도

| 비용비율 | Expanding의 관측상 최저 정책 | 총비용 | Raw 0.5 대비 절감 | Raw 0.5보다 낮은 구간 |
|---|---|---:|---:|---:|
| 1:10 | Platt analytic | 17,729 | 1.26% | 1/3 |
| 1:25 | Raw empirical | 29,097 | 33.11% | 2/3 |
| 1:50 | Raw empirical | 46,200 | 46.33% | 3/3 |
| 1:100 | Raw empirical | 69,627 | 59.34% | 3/3 |
| 1:200 | Platt analytic | 108,172 | 68.33% | 3/3 |

### 결론

비용 관점의 개선은 확인됐다. 특히 1:50~1:100에서는 raw empirical 정책이 모든 평가 구간에서 raw threshold 0.5보다 낮은 비용을 기록했다.

1:100에서 비용 감소는 두 부분으로 나뉜다.

1. 동일한 raw empirical 정책에서 Fixed 91,747 → Expanding 69,627: 모델 개선 효과 약 24.1%
2. Expanding raw threshold 0.5 171,225 → raw empirical 69,627: threshold 정책을 포함한 전체 개선 59.34%

그러나 비용 정책 세 개 중 가장 낮은 정책은 평가 결과를 본 뒤 비교한 사후 결과다. 실제 현장 비용과 정책 하나를 먼저 고정한 독립 미래 검증이 필요하다.

관련 파일:

- [실험 보고서](../experiments/0825_kimjaehak_014_cost_optimized_policy.md)
- [노트북](../../notebooks/0825_kimjaehak_014_cost_optimized_policy.ipynb)

---

## 4. 별도로 진행한 개선 실험

## 4.1 `kimjaehak_009`: 부분 리샘플링 탐색

### 주요 결과

검사유형별로 부분 SMOTE, ADASYN, Random Undersampling 비율과 sampler seed 안정성을 비교했다.

Type 2에서만 1:4 Random Undersampling이 선택됐다.

| Type 2 Test | Baseline | Undersampling 1:4 |
|---|---:|---:|
| PR-AUC | 0.356827 | **0.561603** |
| Recall | 34.57% | **59.89%** |
| F1 | 0.413265 | **0.470917** |
| FN | 460 | **282** |
| FP | 230 | 664 |

Pooled PR-AUC도 0.315411에서 0.383311로 상승했다.

단일 split에서는 매우 유망했지만 Validation seed 표준편차가 0.110551로 컸기 때문에 기간 강건성 검증으로 이어졌다.

관련 파일:

- [실험 보고서](../experiments/0825_kimjaehak_009_partial_rebalancing.md)
- [노트북](../../notebooks/0825_kimjaehak_009_partial_rebalancing.ipynb)

## 4.2 `kimjaehak_012`: Type 2 undersampling 강건성 검증

### 주요 결과

동일한 60/20/20 split에서는 seed가 달라도 강하게 재현됐다.

- Validation baseline 승리 seed 비율: 90%
- Test baseline 승리 seed 비율: 100%

그러나 6개 expanding 시간 Fold에서는 결과가 달랐다.

- median ΔPR-AUC 양수 Fold: 3/6
- 전체 seed×Fold 승률: 51.7%
- W09와 W10에서는 baseline보다 낮음

### 결론

`kimjaehak_009`의 결과가 seed 42의 단순 우연은 아니지만, 기간에 독립적으로 일반화되는 개선도 아니었다. 따라서 Type 2 1:4 undersampling을 최종 모델에 고정 적용하지 않았다.

관련 파일:

- [실험 보고서](../experiments/0825_kimjaehak_012_type2_undersampling_robustness.md)
- [노트북](../../notebooks/0825_kimjaehak_012_type2_undersampling_robustness.ipynb)

## 4.3 `kimjaehak_016`: 시간 안정적 피처 축소

### 주요 결과

Train 내부 시간 Fold의 permutation importance를 이용해 mapping 피처를 보수적으로 줄였다.

- 전체 피처 수: 267개 → 247개
- 감소율: 7.5%
- 사전 목표: 25% 이상 감소
- Pooled Test PR-AUC: 0.315411 → 0.339216
- Recall: 31.61% → 27.70%
- FN: 1,538 → 1,626

Type 2에서 meta 피처를 제외했을 때 PR-AUC가 0.356827에서 0.617585로 크게 증가했다. 그러나 threshold 0.5 Recall은 12.52%p 감소하고 FN은 88건 증가했다.

### 결론

전체 피처 축소 목표를 달성하지 못했고 Type 0에서는 미래 PR-AUC가 악화했다. 따라서 전역 feature selection은 최종 모델에 적용하지 않았다.

Type 2의 no-meta 결과는 별도의 후속 가설로는 유망하지만 이미 Test 결과를 확인했으므로 새로운 시간 구간에서 다시 검증해야 한다.

관련 파일:

- [실험 보고서](../experiments/0825_kimjaehak_016_stable_feature_selection.md)
- [노트북](../../notebooks/0825_kimjaehak_016_stable_feature_selection.ipynb)

---

## 5. 실험별 최종 판정

| 실험 | 최종 판정 | 최종 모델 반영 여부 |
|---|---|---|
| `kimjaehak_007` | 혼합 drift 진단 | Expanding 재학습 필요성의 근거로 반영 |
| `kimjaehak_008` | 직전 safety threshold의 시간 전이 실패 | 미반영 |
| `kimjaehak_009` | Type 2 undersampling 단일 split 개선 | `kimjaehak_012` 검증 전 보류 |
| `kimjaehak_010` | Calibration 비용 신호, 확률 품질 불안정 | 일괄 적용하지 않음 |
| `kimjaehak_011` | Expanding 재학습 유망 | `kimjaehak_013`에서 순수 모델 성능 재검증 |
| `kimjaehak_012` | Type 2 undersampling 기간 강건성 부족 | 미반영 |
| `kimjaehak_013` | Expanding 모델 자체 성능 개선 확인 | **최종 모델 구조에 반영** |
| `kimjaehak_014` | 비용 threshold 추가 이득 확인 | **운영 정책 후보로 반영** |
| `kimjaehak_016` | 전역 피처 축소 목표 실패 | 미반영, Type 2 no-meta만 후속 후보 |

---

## 6. 현재 최종 모델 후보

### 6.1 비용을 고려하지 않은 Champion 모델

비용을 고려하지 않은 모델 자체의 champion은 다음과 같다.

```text
Expanding type-conditioned XGBoost

- inspection type별 모델 5개
- mapping.json 기반 type별 유효 피처
- 최근 데이터를 누적하는 Expanding 재학습
- 리샘플링과 전역 피처 축소는 적용하지 않음
- 비용비율과 threshold는 모델 선택에 사용하지 않음
```

이 모델은 `kimjaehak_013`에서 비용, threshold, confusion matrix를 완전히 제외하고 선택했다. 주 선택 지표는 검사유형별 PR-AUC를 해당 유형의 실제 불량 수로 가중한 positive-weighted type PR-AUC다.

| W08~W10 threshold-free 모델 성능 | Fixed | **비용 미고려 Champion: Expanding** | 변화 |
|---|---:|---:|---:|
| Aggregate pooled PR-AUC | 0.298083 | **0.344535** | +0.046452, 약 +15.6% |
| 평균 positive-weighted type PR-AUC | 0.404530 | **0.472470** | +0.067940, 약 +16.8% |
| 평균 macro type PR-AUC | 0.227814 | **0.264495** | +0.036681 |
| Aggregate Brier score | 0.020556 | **0.018689** | -0.001867 |
| Aggregate log loss | 0.106902 | **0.100548** | -0.006354 |

기간별 주 지표도 재학습 효과가 발생한 W09와 W10에서 모두 Fixed보다 높았다.

| 평가 구간 | Fixed | Expanding Champion | 판정 |
|---|---:|---:|---|
| W08 | 0.458541 | 0.458541 | 학습 데이터가 같아 동일 |
| W09 | 0.388373 | **0.451414** | Expanding 우세 |
| W10 | 0.366676 | **0.507455** | Expanding 우세 |

비용을 사용하지 않은 결론은 다음과 같다.

> Expanding은 특정 비용비율이나 threshold의 도움 없이도 Fixed보다 실제 불량을 위쪽에 더 잘 정렬했다. 따라서 비용 정책과 무관한 최종 모델 champion은 Expanding type-conditioned XGBoost다.

참고로 threshold 0.5를 적용하면 Expanding의 Recall은 33.89%, FN은 1,703건, False Call Reduction은 99.20%다. 이 값은 모델 선택 기준이 아니라 고정 threshold에서의 보조 운영 지표다.

#### 비용 미고려 Champion의 참고 Confusion Matrix

비용 미고려 Champion은 threshold-free 지표로 선택했기 때문에 원래는 하나의 confusion matrix를 갖지 않는다. 아래 결과는 모델의 raw score에 관례적인 threshold 0.5를 적용한 참고값이다.

| 실제값 \ 예측값 | 정상 예측 `0` | 불량 예측 `1` | 합계 |
|---|---:|---:|---:|
| 실제 정상 `0` | TN **114,089** | FP **925** | 115,014 |
| 실제 불량 `1` | FN **1,703** | TP **873** | 2,576 |
| 합계 | 115,792 | 1,798 | 117,590 |

```text
                     예측 정상(0)   예측 불량(1)
실제 정상(0)          TN 114,089      FP 925
실제 불량(1)          FN   1,703      TP 873
```

- Recall: 33.89%
- False Call Reduction: 99.20%
- Precision: 약 48.55%
- Slip Rate: 66.11%

Threshold 0.5에서는 정상 자동 통과 비율은 높지만 실제 불량 1,703건을 놓쳤다. 이 confusion matrix가 비용 미고려 Champion의 모델 순위 성능을 부정하는 것은 아니며, 모델 score를 실제 판정으로 바꾸는 threshold가 별도로 필요하다는 뜻이다.

### 6.2 비용을 고려한 Champion 정책 후보

비용을 고려한 결과는 모델 champion에 의사결정 정책을 추가한 별도 후보로 구분한다.

```text
비용 미고려 Champion: Expanding type-conditioned XGBoost
+
직전 구간에서 선택한 inspection type별 raw empirical 비용 threshold
+
희소 type 수동 재검사 fallback 후보
```

FP:FN 비용비율을 1:100으로 가정했을 때의 운영 성능은 다음과 같다.

| 모델 및 정책 | PR-AUC | Recall | TP | FN | False Call Reduction | TN | FP | 총비용 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Fixed + raw empirical | 0.298083 | 72.52% | 1,868 | 708 | 81.79% | 94,067 | 20,947 | 91,747 |
| Expanding + raw threshold 0.5 | 0.344535 | 33.89% | 873 | 1,703 | 99.20% | 114,089 | 925 | 171,225 |
| **비용 고려 Champion 후보: Expanding + raw empirical** | **0.344535** | **79.43%** | **2,046** | **530** | **85.54%** | **98,387** | **16,627** | **69,627** |
| 전량 수동 재검사 | 해당 없음 | 100.00% | 2,576 | 0 | 0.00% | 0 | 115,014 | 115,014 |

비용 고려 Champion 후보의 개선 폭은 다음과 같다.

- 동일한 raw empirical 정책의 Fixed 모델 대비 총비용 **24.1% 감소**
- 동일한 raw empirical 정책의 Fixed 모델 대비 FN **178건 감소**
- 동일한 raw empirical 정책의 Fixed 모델 대비 Recall **6.91%p 증가**
- 동일한 raw empirical 정책의 Fixed 모델 대비 False Call Reduction **3.76%p 증가**
- Expanding raw threshold 0.5 대비 총비용 **59.34% 감소**
- 전량 수동 재검사 대비 총비용 **45,387 감소**

PR-AUC, Brier score, log loss는 모델 자체를 평가하는 threshold-free 지표다. Recall, FN, False Call Reduction과 총비용은 1:100 비용 가정과 raw empirical threshold가 적용된 운영 지표다.

비용 고려 정책의 Slip Rate는 20.57%다. 비용 최적화가 안전한 미검출 수준을 보장하지는 않으므로 실제 운영에서는 비용비율과 별도의 FN 또는 Slip Rate 상한이 필요하다.

#### 비용 고려 Champion 후보의 Confusion Matrix

다음은 FP:FN = 1:100을 가정하고 inspection type별 raw empirical threshold를 적용한 결과다.

| 실제값 \ 예측값 | 정상 예측 `0` | 불량 예측 `1` | 합계 |
|---|---:|---:|---:|
| 실제 정상 `0` | TN **98,387** | FP **16,627** | 115,014 |
| 실제 불량 `1` | FN **530** | TP **2,046** | 2,576 |
| 합계 | 98,917 | 18,673 | 117,590 |

```text
                     예측 정상(0)   예측 불량(1)
실제 정상(0)          TN 98,387       FP 16,627
실제 불량(1)          FN    530       TP  2,046
```

- Recall: 79.43%
- False Call Reduction: 85.54%
- Precision: 약 10.96%
- Slip Rate: 20.57%
- 총비용: `16,627 × 1 + 530 × 100 = 69,627`

Threshold 0.5와 비교하면 FN은 1,703건에서 530건으로 1,173건 감소했지만, FP는 925건에서 16,627건으로 증가했다. 즉 비용 정책은 더 많은 정상 건을 재검사하는 대신 불량 미검출을 줄이는 방향으로 판정점을 이동시켰다.

### 6.3 `model_val.md`에서 확인할 행

비용을 고려하지 않은 모델 champion은 [`docs/model_val.md`의 `kimjaehak_013` Expanding 순위 성능 평가 행](../model_val.md)에서 확인한다. 현재 파일 기준 36번째 줄이다.

```text
비용 미고려 Champion
Model: Expanding type-conditioned XGBoost
PR-AUC: 0.345
Threshold: 해당 없음
```

비용을 고려한 정책 champion 후보는 현재 파일 기준 38번째 줄의 `kimjaehak_014` Expanding + empirical cost 1:100 행에서 확인한다.

```text
PR-AUC 0.345
Recall 79.4%
TP 2,046
FN 530
False Call Reduction 85.5%
```

비교할 행은 다음과 같다.

- 현재 파일 36번째 줄: `kimjaehak_013` Expanding 순위 성능 평가. Threshold 없이 PR-AUC 0.345를 확인하는 행
- 현재 파일 37번째 줄: `kimjaehak_014` Fixed + empirical cost 1:100. Champion과 같은 비용 정책의 Fixed 비교군
- 현재 파일 38번째 줄: `kimjaehak_014` Expanding + empirical cost 1:100. **Champion 운영 성능 행**

`model_val.md`에는 비용 컬럼이 없으므로 총비용 69,627은 `kimjaehak_014` 실험 보고서와 노트북에서 확인해야 한다.

### 6.4 모델 계층

- inspection type별 XGBoost 5개
- 공통 `meta_feat`와 `mapping.json`에 정의된 type별 유효 피처 사용
- 중복 제거와 timestamp-group 시간 분할 유지
- 최근 데이터를 계속 추가하는 Expanding 방식으로 재학습
- 현재 단계에서는 리샘플링과 전역 피처 축소를 적용하지 않음

### 6.5 의사결정 계층

- 모델 선택은 PR-AUC 등 threshold-free 지표로 수행
- 최종 판정은 모델과 분리된 inspection type별 threshold에서 수행
- 실제 비용이 FP:FN = 1:50~1:100에 가깝다면 직전 구간 raw empirical threshold가 현재 가장 유망
- 표본이 부족한 type은 수동 재검사 fallback 검토
- 비용 최적화와 별도로 허용 가능한 FN 또는 Slip Rate 상한 설정 필요

### 6.6 운영 시 예상 흐름

```text
새 데이터 도착
    ↓
데이터 품질·중복·inspection type 확인
    ↓
기존 데이터에 새 기간을 추가하여 Expanding 재학습
    ↓
직전 기간에서 type별 score와 비용 threshold 계산
    ↓
다음 기간에 모델과 threshold를 고정 적용
    ↓
type별 PR-AUC·FN·FCR·비용·score drift 모니터링
```

---

## 7. 현재 결과에서 부족한 점

### 7.1 실제 비용이 정의되지 않음

현재 1:10, 1:25, 1:50, 1:100, 1:200을 가정해 민감도를 분석했다. 실제 현장에서 FN 1건이 FP 몇 건과 같은 비용인지 정해지지 않았으므로 하나의 threshold를 최종 선택할 수 없다.

### 7.2 비용 최소화와 안전성은 다름

1:100 Expanding + raw empirical 정책은 비용이 가장 낮았지만 FN 530건, Slip Rate 20.57%였다. 안전상 허용 가능한 미검출 상한이 있다면 비용식과 별도의 하드 제약으로 둬야 한다.

### 7.3 핵심 평가 구간이 세 개뿐임

최종 모델과 비용 정책의 핵심 평가는 W08~W10 세 구간이다. 평균적으로 개선됐더라도 더 많은 미래 구간에서 동일한 방향이 유지되는지 알 수 없다.

### 7.4 평가 데이터를 반복적으로 확인함

오늘 여러 실험에서 후반 기간 결과를 반복해서 확인했다. 따라서 현재 결과는 독립적인 최종 Test라기보다 회고적 모델 개발 결과에 가깝다.

### 7.5 희소 inspection type의 불확실성

일부 type과 기간에는 양성이 매우 적거나 음성 표본 자체가 적었다. 이런 구간에서 threshold, calibration, PR-AUC의 변동성이 크다.

### 7.6 drift의 실제 원인을 확정할 정보가 없음

작업자 ID, AOI 프로그램 변경, 공정 변경, 재검수 ground truth가 없다. 라벨 기준 변화와 실제 불량 증가를 인과적으로 구분할 수 없다.

### 7.7 아직 모델 파일을 저장하지 않음

현재 실험은 비교 목적이므로 모델 바이너리를 저장하지 않았다. 운영용 모델을 만들려면 재학습 시점, 저장 형식, 피처 스키마, threshold 설정을 하나의 재현 가능한 파이프라인으로 고정해야 한다.

---

## 8. 필요한 후속 실험

우선순위는 다음과 같다.

### 1순위: 실제 비용과 FN 상한 합의

- FP 1건의 비용
- FN 1건의 비용
- 비용과 별개로 허용 가능한 FN 또는 Slip Rate 상한
- 수동 재검사 가능한 최대 물량

이 값이 정해져야 최종 threshold를 선택할 수 있다.

### 2순위: 정책을 동결한 미래 검증

다음 항목을 결과를 보기 전에 고정한다.

- Expanding type-conditioned XGBoost
- 재학습 주기
- 비용비율
- raw empirical 또는 다른 하나의 threshold 정책
- 희소 type fallback 규칙
- 안전 제약

그 후 아직 보지 않은 새로운 시간 구간에 단 한 번 적용한다.

### 3순위: 시간 안정성과 불확실성 평가

- 더 많은 walk-forward Fold 확보
- 기간별 비용과 FN의 confidence interval 계산
- block bootstrap 또는 시간 블록 기반 변동성 평가
- Expanding 학습 기간이 너무 길어졌을 때의 성능 확인

### 4순위: 희소 type 위험 제어

- 전량 재검사 fallback
- upper confidence bound 기반 threshold
- conformal risk control
- 최소 양성·음성 표본 조건 재검증

### 5순위: Type 2 no-meta 독립 검증

`kimjaehak_016`에서 발견한 Type 2 no-meta 효과를 새로운 시간 Fold에서 검증한다. 이때 undersampling과 동시에 적용하지 말고 각각의 효과를 분리해야 한다.

---

## 9. 최종 결론

오늘 실험으로 확인한 가장 중요한 결과는 다음과 같다.

> 현재 데이터 변화에는 고정 모델의 threshold만 조절하는 것보다, inspection type별 모델을 최근 데이터로 누적 재학습하는 Expanding 방식이 더 적절하다.

Expanding은 비용이나 threshold를 제외하고도 Fixed보다 PR-AUC, Brier score, log loss가 개선됐다. 따라서 모델 자체의 성능 개선이 확인됐다.

또한 비용 기반 threshold를 추가하면 1:50~1:100 가정에서 raw threshold 0.5보다 비용이 반복적으로 감소했다. 1:100에서는 Expanding + raw empirical 정책의 비용이 69,627로, Expanding raw 0.5보다 59.34%, 동일 정책의 Fixed보다 24.1% 낮았다.

따라서 오늘 실험의 결과는 두 가지 champion으로 구분한다.

### 비용을 고려하지 않은 모델 Champion

```text
Expanding type-conditioned XGBoost
```

- W08~W10 aggregate pooled PR-AUC: 0.344535
- 평균 positive-weighted type PR-AUC: 0.472470
- Aggregate Brier score: 0.018689
- Aggregate log loss: 0.100548
- `model_val.md` 확인 위치: `kimjaehak_013` Expanding 순위 성능 평가 행

이 모델은 비용과 threshold를 전혀 사용하지 않고 Fixed·Expanding·Rolling-6 중 선택한 최종 모델 champion이다.

### 비용을 고려한 운영 정책 Champion 후보

```text
Expanding type-conditioned XGBoost
+
inspection type별 비용 threshold
+
희소 type 수동 재검사 fallback
```

1:100 raw empirical 비용 정책에서 Recall 79.43%, False Call Reduction 85.54%, FN 530건, 총비용 69,627을 기록했다. `model_val.md`에서는 `kimjaehak_014` Expanding + empirical cost 1:100 행에 해당한다.

그러나 이것은 아직 최종 운영 모델이 아니다. 실제 비용과 안전 제약을 확정하고, 정책을 고정한 뒤 새로운 미래 데이터에서 검증해야 최종 채택 여부를 결정할 수 있다.

---

## 10. 관련 산출물

- [HTML 요약 보고서](20260825_0607_kimjaehak_sandbox_experiment_report.html)
- [실험 목록](../experiments/index.md)
- [모델 평가 목록](../model_val.md)

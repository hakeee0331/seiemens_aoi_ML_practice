# 0825_kimjaehak_012_type2_undersampling_robustness

## 연결된 노트북

`notebooks/0825_kimjaehak_012_type2_undersampling_robustness.ipynb`

## 상태

완료 — 노트북 전체 실행과 결과 검증 완료

## 목적

`0825_kimjaehak_009_partial_rebalancing`에서 `inspection_type=2`에 선택된 `RandomUnderSampler(sampling_strategy=0.25)`가 특정 sampler seed와 단일 시간 분할에 우연히 맞은 결과인지 검증한다.

검증은 다음 두 단계를 순차적으로 수행했다.

1. 009와 동일한 60/20/20 Train/Validation/Test split에서 sampler seed 재현성 확인
2. 설정을 고정한 expanding walk-forward에서 기간 강건성 확인

이 실험은 1:4 undersampling의 사후 강건성 검증이다. 새로운 비율, 리샘플링 기법, inspection type 또는 threshold를 탐색하지 않는다.

## 이전 실험 대비 주요 변경사항

- 대상은 009에서 유일하게 리샘플링이 선택된 `inspection_type=2`로 제한했다.
- 비교 대상은 baseline과 고정된 1:4 Random Undersampling뿐이다.
- XGBoost seed는 `42`로 고정하고 sampler seed만 `42~51`로 변경했다.
- 009와 같은 split 재현 뒤, 10개 timestamp window를 사용하는 6개 expanding Fold를 추가했다.
- PR-AUC를 주지표로 사용하고 threshold `0.5` 지표는 보조 결과로만 기록했다.
- Validation F1 threshold 선택이나 운영 threshold 최적화는 수행하지 않았다.

중복 제거, 전체 데이터 기준 시간 경계, `mapping.json` 기반 type별 피처와 XGBoost 설정은 006·009와 동일하다.

## 데이터와 실행 검증

- 원본 440,274행에서 baseline 기준 중복 48,282행 제거
- 최종 데이터 391,992행
- Type 2 Train 74,910행 / Validation 15,897행 / Test 19,153행
- Type 2 양성 수: Train 579 / Validation 32 / Test 703
- 코드 셀 9개 전체 실행, 오류 0건
- 1단계 11회, 2단계 66회로 총 77개 XGBoost 모델 학습
- 모델 파일은 저장하지 않음

## 평가 방법

### 1단계: 동일 split seed 재현성

- Train/Validation/Test 경계는 009와 동일하다.
- Baseline은 한 번 학습한다.
- 1:4 undersampling은 sampler seed `42~51`로 10회 반복한다.
- Validation과 Test 각각에서 baseline 대비 PR-AUC 승률과 PR-AUC 분포를 계산한다.
- 009에서 이미 Test를 확인했으므로 이 결과는 새로운 독립 Test가 아니라 회고적 재현성 검증으로 해석한다.

사전 판정 기준은 다음과 같다.

- 강한 재현: Validation과 Test 모두 median ΔPR-AUC가 양수이고 seed 승률이 각각 80% 이상
- 부분 재현: 두 split 모두 median ΔPR-AUC가 양수이고 seed 승률이 각각 60% 이상
- 그 외: 재현 실패

### 2단계: expanding walk-forward 기간 강건성

| 평가 Fold | 학습 window | 평가 window |
|---:|---|---|
| 1 | W01~W04 | W05 |
| 2 | W01~W05 | W06 |
| 3 | W01~W06 | W07 |
| 4 | W01~W07 | W08 |
| 5 | W01~W08 | W09 |
| 6 | W01~W09 | W10 |

각 Fold에서 baseline 1회와 undersampling 10개 seed를 비교했다. 같은 평가 라벨을 10개 seed가 공유하므로 60개 실행을 독립 표본처럼 간주하지 않고, Fold별 median과 전체 seed×Fold 승률을 함께 사용했다.

사전 판정 기준은 다음과 같다.

- 강한 재현: 6개 Fold 중 5개 이상에서 median ΔPR-AUC가 양수이고 전체 승률 80% 이상
- 부분 재현: 3개 이상 Fold에서 median ΔPR-AUC가 양수이고 전체 승률 60% 이상
- 그 외: 재현 실패

## 주요 결과

### 1단계: 동일 split에서는 강하게 재현

| 평가 split | Baseline PR-AUC | Undersampling PR-AUC 평균 | 표준편차 | 범위 | median ΔPR-AUC | Baseline 승리 seed 비율 |
|---|---:|---:|---:|---:|---:|---:|
| Validation | 0.050334 | 0.215149 | 0.110551 | 0.040080~0.372506 | +0.165984 | 90% |
| Test | 0.356827 | 0.559174 | 0.037551 | 0.499294~0.608625 | +0.207170 | 100% |

Validation은 seed 변동성이 컸지만 10개 중 9개 seed에서 baseline을 이겼다. Test에서는 10개 seed가 모두 baseline보다 높았고 표준편차도 Validation보다 작았다. 사전 기준에 따라 1단계는 **강한 재현**으로 판정했다.

009와 직접 대응하는 seed 42의 Test 결과도 일치했다.

| 모델 | PR-AUC | ROC-AUC | Precision | Recall | F1 | TN | FP | FN | TP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 0.356827 | 0.887697 | 0.513742 | 0.345661 | 0.413265 | 18,220 | 230 | 460 | 243 |
| Undersampling 0.25, seed 42 | 0.561603 | 0.911834 | 0.388018 | 0.598862 | 0.470917 | 17,786 | 664 | 282 | 421 |

### 2단계: 기간 강건성은 재현되지 않음

| 평가 window | 양성 수 | Baseline PR-AUC | Undersampling 평균 ± 표준편차 | median ΔPR-AUC | seed 승률 |
|---|---:|---:|---:|---:|---:|
| W05 | 48 | 0.483620 | 0.273582 ± 0.045598 | -0.216143 | 0% |
| W06 | 31 | 0.014874 | 0.053373 ± 0.019686 | +0.043357 | 100% |
| W07 | 7 | 0.011002 | 0.025347 ± 0.017577 | +0.008703 | 100% |
| W08 | 25 | 0.104442 | 0.254758 ± 0.155875 | +0.109373 | 90% |
| W09 | 407 | 0.864725 | 0.813483 ± 0.059281 | -0.033625 | 10% |
| W10 | 296 | 0.306292 | 0.276470 ± 0.032281 | -0.022360 | 10% |

- median ΔPR-AUC가 양수인 Fold: 3/6
- 전체 seed×Fold 승률: 51.7%
- 전체 median ΔPR-AUC: +0.001135
- ΔPR-AUC 하위 25% 지점: -0.056259

W06~W08에서는 효과가 반복됐지만 W05, W09, W10에서는 baseline이 우세했다. 특히 양성률이 크게 높아지는 후반 W09·W10에서 undersampling의 평균 PR-AUC가 baseline보다 낮았다. 사전 기준의 최소 승률 60%에 미달하여 2단계는 **재현 실패**로 판정했다.

Threshold 0.5에서는 모든 Fold의 대부분 seed에서 Recall이 증가하고 FN이 감소했지만 TN도 일관되게 감소했다. 이는 undersampling이 raw probability scale과 판정 비율을 바꾸는 효과가 섞여 있으므로 PR-AUC 개선의 증거로 사용하지 않는다.

## 결론

- Type 2의 1:4 undersampling은 009와 동일한 split 안에서는 sampler seed에 대해 강하게 재현됐다.
- 그러나 시간 구간을 바꾸면 개선 방향이 일관되지 않았고, expanding walk-forward의 전체 승률은 사실상 절반인 51.7%였다.
- 따라서 009의 성능 개선은 단순히 seed 42의 우연이라고 보기는 어렵지만, **기간에 독립적으로 일반화되는 안정적인 개선이라고도 볼 수 없다.**
- 종합 판정은 `not_supported`다. 이는 동일 split 결과가 틀렸다는 뜻이 아니라, 1:4 undersampling을 Type 2의 고정 운영 정책으로 채택할 근거가 부족하다는 뜻이다.
- W07은 양성이 7개뿐이어서 PR-AUC 불확실성이 특히 크며, Fold별 양성률 변화도 성능 변동에 영향을 줬을 가능성이 있다.

다음 실험에서는 비율을 다시 탐색하기 전에, Type 2에서 기간별 양성률·피처 drift·baseline score 분포와 undersampling 효과의 관계를 진단하는 것이 우선이다. 운영 threshold 검증은 별도 실험으로 분리해야 한다.

## 모델 평가 목록 반영 여부

이번 실험은 이미 사용한 Test와 회고적 walk-forward 구간을 반복 평가한 강건성 검증이며 새로운 최종 모델을 선택하지 않았다. 따라서 `docs/model_val.md`에는 새 행을 추가하지 않는다.

## 저장 모델

비교 실험이므로 모델 파일을 저장하지 않았다.

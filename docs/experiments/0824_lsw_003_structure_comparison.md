# 0824_lsw_003_structure_comparison

## 연결된 노트북

`notebooks/0824_lsw_003_structure_comparison.ipynb`

## 상태

완료

## 목적

통합모델(전체 검사유형 하나로 학습) vs 검사유형별 5분리 모델 중 어느 구조가
나은지 순수하게 비교한다. 데이터 전처리(중복 제거, 시간순 6:2:2 분할)는
`main`의 `0824_kimjaehak_005_xgboost_baseline`과 동일하게 맞춰서, 구조 외
다른 변수가 섞이지 않게 했다.

## 이전 실험 대비 주요 변경사항

- `0824_kimjaehak_005_xgboost_baseline`의 데이터 처리(넓은 기준 중복 제거,
  timestamp 그룹 경계를 보존하는 6:2:2 분할)를 그대로 재사용했다 — 우리
  baseline(`0823_lsw_002`)의 전처리(좁은 기준 중복 제거, 유형별 독립 분할)는
  이번엔 쓰지 않았다.
- Train/Val/Test 시간 경계는 **전체 데이터 기준으로 한 번만** 계산하고, 두
  구조 모두 같은 경계를 공유한다.
- `mapping.json` 기반 피처 마스킹은 적용하지 않았다(구조와 독립적인 변수라
  다음 feature selection 단계로 미룸). 대신 학습 데이터 기준 상수열만 제거했다.
- 임계값 탐색을 `0823_lsw_002`의 `0.01` 간격 grid 대신, 실제 관측된 예측확률
  값을 후보로 쓰는 exact search로 교체했다(grid 해상도 문제 수정).
- 총비용은 `docs/lsw/project/scope_and_roadmap.md`의 두 시나리오(1:10, 1:100)를
  함께 계산했다.

## 평가 방법과 주요 결과

Test는 학습·모델 선택에 사용하지 않고 최종 평가에만 사용했다.

전체(pooled):

| 구조 | Slip Rate | Volume Reduction | 총비용(1:10) | 총비용(1:100) |
|---|---:|---:|---:|---:|
| 통합모델 | 0.22% | 0.09% | 76,132 | 76,582 |
| 5분리모델(pooled) | 3.78% | 31.4% | 53,079 | 60,729 |

검사유형별 (통합모델의 예측을 유형별로 다시 쪼개 계산):

| inspection_type | 통합 Slip Rate | 통합 Volume Reduction | 5분리 Slip Rate | 5분리 Volume Reduction |
|---|---:|---:|---:|---:|
| 0 | 0.00% | 0.00% | 16.54% | 53.19% |
| 1 | 0.64% | 0.63% | 1.02% | 18.10% |
| 2 | 0.00% | 0.00% | 1.71% | 18.93% |
| 3 | 0.00% | 0.00% | 7.13% | 32.35% |
| 4 | 0.00% | 0.00% | 0.00% | 0.00% |

- **통합모델은 "안전해서 좋은 게" 아니라 "모든 유형에서 똑같이 무효해서"
  안전하다.** 유형별로 쪼개보면 5개 유형 전부에서 Volume Reduction이
  0%에 가깝다(최댓값 type1의 0.63%) — 특정 유형에서 똑똑하게 걸러내는 게
  아니라 전 유형에 걸쳐 임계값이 똑같이 바닥까지 눌린 것이다. test negative
  총량(76,147)이 kimjaehak baseline과 정확히 일치해 재현성을 확인했다.
- **5분리모델은 4개 유형에서 실제로 의미 있는 신호를 찾아낸다**(Volume
  Reduction 18~53%). 다만 표본이 적은 유형(0, 2, 3)에서 Slip Rate가
  목표(1%)를 초과한다 — type0(Val 불량 8건) 16.5%, type2(32건) 1.7%,
  type3(24건) 7.1%. 표본이 가장 많은 type1(239건)만 목표에 근접(1.02%)하며
  Volume Reduction 18.1%도 확보했다.

## 결론과 다음 단계

- 상세 결론은 노트북 12절 참고.
- **구조를 5분리로 가는 방향 자체는 맞다** — 통합모델은 어느 유형에서도
  쓸모가 없다(모든 유형 Volume Reduction ≈0%). 문제는 유형별로 임계값을
  각각 고르는 방식이 표본이 적은 유형에서 신뢰할 수 없다는 것이다.
- 다음 단계(불균형 처리) 전에 임계값 선택 방식을 유형별이 아니라 전체
  데이터 합산 Validation 기준으로 바꿔보는 실험이 먼저 필요하다.
- 그래도 type0처럼 표본이 극히 적은 유형은 별도 안전 마진 규칙이 필요할 수
  있다.
- 이번 실험은 `mapping.json` 마스킹 없이 진행했다 — 다음 feature selection
  단계에서 마스킹 적용 시 유형별 Test 안정성이 개선되는지 확인할 예정이다.

## 저장된 모델 경로

- `models/0824_lsw_003_structure_comparison_unified.pkl`
- `models/0824_lsw_003_structure_comparison_type0.pkl`
- `models/0824_lsw_003_structure_comparison_type1.pkl`
- `models/0824_lsw_003_structure_comparison_type2.pkl`
- `models/0824_lsw_003_structure_comparison_type3.pkl`
- `models/0824_lsw_003_structure_comparison_type4.pkl`

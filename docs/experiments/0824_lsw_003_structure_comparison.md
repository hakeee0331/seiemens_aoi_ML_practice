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

| 구조 | Slip Rate | Volume Reduction | 총비용(1:10) | 총비용(1:100) |
|---|---:|---:|---:|---:|
| 통합모델 | 0.22% | 0.09% | 76,132 | 76,582 |
| 5분리모델(pooled) | 3.78% | 31.4% | 53,079 | 60,729 |

- **통합모델**: Slip Rate 목표(≤1%)는 만족하지만 임계값이 사실상 0까지
  밀려 Volume Reduction이 0.09%에 그친다 — 사실상 자동화 효과가 없다.
  test negative 총량(76,147)이 kimjaehak baseline과 정확히 일치해 재현성을
  확인했다.
- **5분리모델**: Volume Reduction 31.4%로 크게 개선됐지만, pooled Slip Rate가
  3.78%로 목표를 위반한다. 유형별로 보면 Validation 불량 표본이 적은 유형일수록
  Test에서 무너진다 — type0(Val 불량 8건) Test Slip Rate 16.5%, type2(32건)
  1.7%, type3(24건) 7.1%인 반면, 표본이 가장 많은 type1(239건)은 1.02%로
  목표에 가장 근접했다.

## 결론과 다음 단계

- 상세 결론은 노트북 11절 참고.
- 5분리 구조가 자동화 효과는 훨씬 크지만, 표본이 적은 유형(0/2/3)에서 유형별
  임계값 선택이 Validation에 과적합돼 Test에서 안전기준을 위반한다.
- 다음 단계(불균형 처리) 전에 임계값 선택 방식을 유형별이 아니라 전체 데이터
  합산 Validation 기준으로 바꿔보는 실험이 먼저 필요해 보인다.
- 이번 실험은 `mapping.json` 마스킹 없이 진행했다 — 다음 feature selection
  단계에서 마스킹 적용 시 유형별 Test 안정성이 개선되는지 확인할 예정이다.

## 저장된 모델 경로

- `models/0824_lsw_003_structure_comparison_unified.pkl`
- `models/0824_lsw_003_structure_comparison_type0.pkl`
- `models/0824_lsw_003_structure_comparison_type1.pkl`
- `models/0824_lsw_003_structure_comparison_type2.pkl`
- `models/0824_lsw_003_structure_comparison_type3.pkl`
- `models/0824_lsw_003_structure_comparison_type4.pkl`

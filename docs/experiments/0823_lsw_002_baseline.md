# 0823_lsw_002_baseline

## 연결된 노트북

`notebooks/0823_lsw_002_baseline.ipynb`

## 상태

완료

## 목적

Phase 0 baseline 재현: `inspection_type`별로 데이터를 분리하고 시간순으로
Train/Val/Test를 나눈 뒤 Dummy / Logistic Regression / XGBoost를 학습하고,
Validation에서 Slip Rate ≤ 1% 제약을 만족하는 운영 임계값을 고른 다음 Test로
평가한다. Slip Rate / Volume Reduction / 총비용 3개 지표를 이후 모든 실험이
재사용할 수 있도록 함수로 고정한다.

## 이전 실험 대비 주요 변경사항

- 최초 baseline 실험. `0823_lsw_001_eda`의 EDA 결과를 반영해 다음을 적용했다.
  - `mapping.json` 기준 유효 컬럼만 사용하고, Train 데이터 기준 상수열을 제거했다.
  - `inspection_type`별로 시간순 정렬 후 행 개수 기준 60/20/20으로 분할했다
    (일별 데이터 편차가 커서 달력일 기준 분할은 피함).
  - 클래스 불균형에 대한 명시적 리샘플링/가중치 조정은 적용하지 않았다
    (Phase 1에서 다룸). 대신 Validation에서 선택한 임계값으로만 대응했다.
  - 총비용 계산에 `COST_FN=100`, `COST_FP=1`(잠정값, 팀 미확정)을 사용했다.
- 랜덤 시드 42를 사용했다.

## 평가 방법과 주요 결과

- 5개 `inspection_type` x 3개 모델(Dummy/Logistic Regression/XGBoost) = 15개
  조합에 대해 Test에서 Slip Rate, Volume Reduction, 총비용을 계산했다.
- **15개 조합 전부 선택된 임계값이 0.0으로 떨어졌다** — Validation에서
  Slip Rate ≤ 1%를 만족하는 임계값이 "모든 행을 수동검사로 보낸다(0.0)"밖에
  없었다. 결과적으로 Test Slip Rate는 15개 전부 0%지만, **Volume Reduction도
  전부 0%**다. 즉 baseline이 현재 운영(AOI 불량 판정 전부 수동검사)과 동일한
  수준이며 자동화 효과가 없다.
- 원인을 type3(XGBoost)로 직접 진단: Validation AUC는 0.915로 모델 자체는
  양호했다. 문제는 (a) type별 Validation 불량 표본이 적어(type3 기준 53건)
  Slip Rate ≤ 1% 제약이 사실상 "0건 허용"으로 작동하고, (b) 그중 일부
  (type3에서 15/53건)가 모델 예측 확률 0.01 미만(최저 0.0000115)이라
  이를 잡으려면 임계값을 거의 0까지 낮춰야 했다는 점이다.
- 목표 지표(Slip Rate ≤ 1%, Volume Reduction ≥ 40%) 중 Slip Rate는
  자명하게 달성했으나 Volume Reduction은 전혀 달성하지 못했다.

## 결론과 다음 단계

- 상세 결론은 노트북 10절("결론 및 다음 단계") 참고.
- 다음 실험 전 팀과 확인 필요: Slip Rate ≤ 1% 제약을 `inspection_type`별로
  각각 적용할지, 전체 데이터 합산으로 적용할지. 표본이 작은 type일수록
  유형별 제약이 지나치게 엄격해진다.
- 임계값이 0에 가깝게 몰리게 만든 "극단적으로 낮게 예측된 실제 불량"
  샘플은 라벨 노이즈(로드맵 Phase 3) 여부를 확인할 후보다.
- `COST_FN`/`COST_FP` 잠정값(100:1)은 팀 확정 필요.

## 저장된 모델 경로

검사유형별 XGBoost 모델(피처 목록·임계값 포함)을 아래 경로에 저장했다.
모델 파일은 Git에서 제외된다.

- `models/0823_lsw_002_baseline_type0.pkl`
- `models/0823_lsw_002_baseline_type1.pkl`
- `models/0823_lsw_002_baseline_type2.pkl`
- `models/0823_lsw_002_baseline_type3.pkl`
- `models/0823_lsw_002_baseline_type4.pkl`

# AOI 수동 검사 대시보드

CSV Test 구간을 시간순으로 한 행씩 읽고 그때마다 모델 추론을 수행한다. 모델 정상
건은 자동 기록하고, 모델 불량 건만 작업자에게 표시해 정상/실제 불량 판정을 받는
Streamlit 데모다. 데이터베이스를 사용하지 않으므로 앱 세션이 초기화되면 판정
기록도 사라진다.

## 화면 기준

- 고정 목표 해상도: `1280 × 720` (`16:9`)
- 데스크톱 공장 모니터 전용
- 모바일 및 반응형 레이아웃은 지원하지 않는다.

## 실행

저장소 루트에서 의존성을 설치하고 실행한다.

```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

기본 데이터와 모델 위치는 다음과 같다.

- 데이터: `data/raw/dataset.csv`
- 모델: `models/0825_peace_005_type_expert_fold_ensemble.pkl`

모델 artifact에 저장된 Validation 종료 시각 이후를 Test 구간으로 사용한다. 데이터의
중복 제거 여부도 artifact의 학습 정책을 따른다. 현재 peace 005 모델은 원본 행을
제거하지 않으며 Test 88,052건을 시간순으로 정렬한다. 앱은 별도의 사전 수동 검사
큐를 만들지 않는다. 다음 행이 들어올 때 단건 추론하고, 공통 threshold
`0.0007097449` 미만이면 `모델판정 정상`으로 기록한 뒤 다음 행으로 진행한다.
threshold 이상이면 진행을 멈추고 해당 행을 작업자에게 노출한다.

모델 파일은 Git에 포함되지 않는다. 모델이 없거나 scikit-learn 버전이 맞지 않으면
`notebooks/0825_peace_005_type_expert_fold_ensemble.ipynb`를 현재 대시보드 환경에서
실행해 artifact를 다시 생성한다. `dashboard/requirements.txt`는 모델을 생성한 버전을
고정한다.

## 샘플 이미지

`dashboard/assets/sample_images/`에 아래 규칙으로 이미지 10장을 넣는다.

```text
inspection_001.jpg
inspection_002.jpg
...
inspection_010.jpg
```

샘플 이미지는 `.jpg` 형식을 사용한다. 파일은 이름순으로 읽으며 CSV 행과 관계없이
끝까지 사용한 뒤 첫 이미지부터 반복한다.

## 현재 데모 범위

- 불량 확률은 Inspection Type별 4개 checkpoint XGBoost 모델의 확률 평균으로
  계산한다.
- Test 행을 시간순으로 하나씩 단건 추론하며 미래 행을 미리 판정하지 않는다.
- 모델 정상 행은 즉시 `모델판정 정상`으로 히스토리에 기록하고 다음 행으로 진행한다.
- 모델 불량 행에서는 스트림 진행을 멈추고 작업자 판정이 끝난 뒤 다음 행을 추론한다.
- Dongjin 027 Global SHAP 분석의 Inspection Type별 `mean(|SHAP|)` 상위 6개를
  `2 × 3` 신호 그리드에 정적으로 표시한다.
- 각 셀에는 Global SHAP 순위, 중요도, 현재 값과 Total Cover가 가장 큰 대표 tree
  split을 표시한다.
- 연속형 feature는 현재 값이 대표 `< split` 조건을 만족하는지 비교하고, 범주형
  feature는 원본 meta 값이 분석 category와 같은지 비교한다.
- 대표 조건 일치는 주황색, 불일치는 밝은 회색, 값 없음은 진한 회색으로 표시한다.
  이는 불량 방향이 아니라 tree split 조건 일치 여부다.
- 작업자에게 노출되는 행은 artifact의 공통 threshold `0.0007097449` 이상이므로
  확률 영역을 빨간색으로 표시한다.
- Type 4는 모든 Global SHAP 값이 0이므로 유효한 설명 신호가 없다고 표시한다.
- CSV의 실제 라벨 `class`는 작업자 판정 전에 화면에 표시하지 않는다.
- 히스토리에는 `모델판정 정상`, `작업자판정 정상`, `작업자판정 실제 불량`을 시간순으로
  함께 표시한다.
- 모델 판정, 작업자 판정과 직전 검사 결과는 `st.session_state`에만 저장한다.

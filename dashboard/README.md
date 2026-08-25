# AOI 수동 검사 대시보드

CSV Test 구간을 시간순으로 한 행씩 표시하고 작업자의 정상/실제 불량 판정을
세션 히스토리에 저장하는 Streamlit 데모다. 데이터베이스를 사용하지 않으므로 앱
세션이 초기화되면 판정 기록도 사라진다.

## 화면 기준

- 고정 목표 해상도: `1280 × 720` (`16:9`)
- 데스크톱 공장 모니터 전용
- 모바일 및 반응형 레이아웃은 지원하지 않는다.

## 실행

저장소 루트에서 의존성을 설치하고 실행한다.

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

기본 데이터와 모델 위치는 다음과 같다.

- 데이터: `data/raw/dataset.csv`
- 모델: `models/0824_kimjaehak_006_type_conditioned_baseline.pkl`

모델 artifact에 저장된 Validation 종료 시각 이후를 Test 큐로 사용한다. 원본
데이터는 모델 학습 노트북과 동일하게 `record_id`와 `timestamp`를 제외한 완전
중복 행을 제거한 뒤 시간순으로 정렬한다.

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

- 불량 확률은 저장된 Inspection Type별 XGBoost 모델에서 계산한다.
- 시계열 그래프 대신 해당 Inspection Type 모델의 전역 중요도 상위 6개 feature를
  `2 × 3` 신호 그리드로 표시한다.
- 신호 그리드는 현재 feature 값과 화면 검증용 임시 상태색을 표시한다. 상태색은
  SHAP 결과가 아니며 모든 항목에 `DEMO`로 명시한다.
- feature 신호 공급자는 별도 인터페이스로 분리되어 있어 향후 팀의 SHAP 계산
  로직으로 교체할 수 있다.
- 원인 feature는 SHAP 연동 전 임시값이며 화면에도 데모 값으로 표시한다.
- CSV의 실제 라벨 `class`는 작업자 판정 전에 화면에 표시하지 않는다.
- 작업자 판정, 직전 검사 결과와 히스토리는 `st.session_state`에만 저장한다.

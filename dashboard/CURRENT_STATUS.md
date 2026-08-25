# AOI 대시보드 현재 작업 현황

이 문서는 AOI 수동 검사 대시보드의 인수인계를 위한 현재 구현 상태를 기록한다.
일반적인 실행 방법은 `dashboard/README.md`를 참고하고, 이 문서에서는 특정 커밋을
기준으로 실제로 구현된 범위와 남은 임시 구현을 다룬다.

## 기록 기준

- 기록일: 2026-08-25 (KST)
- 통합 브랜치: `26-dashboard`
- 병합한 레이아웃 브랜치의 마지막 기능 커밋: `75b1c0d`
- 최초 대시보드 기능 커밋: `fa13519`
- 실행 문서 커밋: `835334e`

`27-layout`의 변경사항은 `26-dashboard`로 통합했다. 현재 대시보드 범위에는 Streamlit
코드, peace 005 앙상블 추론, 샘플 JPG 10장과 실행 문서가 포함되어 있다. 저장소의
별도 미추적 `docs` PDF와 `src/` 파일은 대시보드 작업에 포함하지 않았다.

## 구현 완료 범위

### 검사 큐

- `data/raw/dataset.csv`의 Test 구간을 시간순으로 한 행씩 읽는다.
- 모델 artifact의 Validation 종료 시각 이후 데이터만 Test 구간으로 사용한다.
- 중복 제거 여부는 모델 artifact의 학습 정책을 따른다.
- 현재 peace 005 모델은 중복 행을 제거하지 않는다.
- Test 행은 시간순으로 정렬한다.
- Streamlit fragment tick에 따라 0.3초마다 다음 행 하나만 단건 추론하며 전체 Test를
  미리 판정하거나 별도 수동 검사 큐를 만들지 않는다.
- 공통 threshold 미만이면 현재 검사 영역에 0.3초 동안 `MODEL NORMAL`로 표시하고 다음
  tick에 `모델판정 정상`으로 기록한다.
- 공통 threshold 이상이면 `MANUAL REVIEW` 상태로 스트림 진행을 멈추고 작업자에게
  해당 행을 노출한다.
- 현재 Test 스트림은 88,052건이다. 수동 검사 총건수는 미래 행을 미리 추론하지
  않으므로 화면에서 사전에 표시하지 않는다.
- CSV의 실제 정답인 `class`는 내부에 유지하지만 작업자 판정 전에는 노출하지 않는다.

### 모델 추론

- 모델: `models/0825_peace_005_type_expert_fold_ensemble.pkl`
- 30%, 40%, 50%, 70% 누적 checkpoint에서 학습한 Inspection Type별 XGBoost
  모델 네 개의 확률을 동일 가중 평균한다.
- 각 checkpoint의 Type별 전처리기와 모델을 함께 artifact에서 불러온다.
- 현재 행의 Inspection Type에 맞는 입력 feature만 추론에 전달한다.
- Validation에서 선택한 공통 threshold `0.0007097449`를 artifact에서 읽어 수동 검사
  대상 여부를 행마다 즉시 결정한다. threshold 이상인 모델 불량 판정만 작업자에게
  노출하며, 작업자는 노출된 건의 실제 정상/불량을 최종 판정한다.

### Feature 신호 그리드

- 시계열 그래프 대신 `2 × 3` feature 신호 그리드를 제공한다.
- Dongjin 027의 Test 전체 Global SHAP 분석에서 계산한 Type별 `mean(|SHAP|)` 상위
  6개를 고정 위치에 표시한다.
- 각 셀에는 Global SHAP 순위, 중요도, 현재 값과 대표 tree split을 표시한다.
- 대표 split은 네 checkpoint 모델의 같은 feature split 중 Total Cover가 가장 큰
  값이다.
- 대표 조건 일치는 주황색, 불일치는 밝은 회색, 값 없음은 진한 회색으로 표시한다.
- 색상은 tree split 조건 일치 여부이며 불량 확률을 높이는 방향을 뜻하지 않는다.
- Type 4는 전체 feature의 Global SHAP가 0이므로 유효한 신호가 없다고 표시한다.
- UI는 `FeatureSignalProvider` 규격을 유지하므로 향후 Local SHAP 공급자로 교체할 수
  있다.

### 작업자 판정

- `NORMAL / 정상 판정`과 `DEFECT / 실제 불량 판정` 버튼을 제공한다.
- 판정 시 현재 항목을 직전 검사 결과로 옮기고 Test 스트림의 다음 행을 즉시 추론해
  화면을 교체한다. 이후 자동 스트림은 다시 0.3초 간격으로 진행한다.
- 판정 시각, Record ID, Inspection Type, 모델 불량 확률과 작업자 판정을 히스토리에
  기록한다.
- 단건 추론에서 자동 통과한 행도 즉시 `모델판정 정상`으로 같은 히스토리에 기록한다.
  수동 검사 건은 `작업자판정 정상` 또는 `작업자판정 실제 불량`으로 구분한다.
- 모델 판정, 작업자 판정과 직전 검사 결과는 `st.session_state`에 저장한다.
- 데이터베이스나 파일에는 기록하지 않으므로 앱 세션이 초기화되면 판정도 사라진다.

### 샘플 이미지

- `dashboard/assets/sample_images/`의 JPG 10장을 이름순으로 읽는다.
- 파일 확장자의 대소문자는 구분하지 않는다.
- CSV 행과 이미지는 아직 연결되어 있지 않다.
- 수동 검사 노출 순번을 기준으로 10장을 반복해 화면에 표시한다.

## 현재 UI 기준

- 고정 화면: `1280 × 720`, 16:9
- 공장 내 데스크톱 모니터 전용
- 모바일 및 반응형 레이아웃 미지원
- 화면 전체를 카드 모음이 아닌 2열 고정 그리드로 구성
- 좌측: 현재 검사, feature 신호 6개, 판정 버튼
- 우측: 직전 검사 결과, 모델·작업자 통합 처리 히스토리
- 헤더: `RUNNING`, `MANUAL REVIEW`, `FINISHED` 상태와 현재 스트림·수동 검사 순번
- 전체 페이지 스크롤 없이 한 화면에 표시
- 히스토리가 길어지면 히스토리 셀 내부에서만 스크롤
- 회색조 배경과 각진 실선 구획 사용
- 불량 판정 버튼만 빨간색 유지
- 이모지와 장식성 요소는 사용하지 않음

## 임시 구현 및 제한사항

### Global SHAP 해석 범위

현재 화면은 미리 계산한 전역 `mean(|SHAP|)`와 대표 tree split을 사용한다. 현재 검사
한 건의 Local SHAP를 계산하지 않으므로, 표시된 feature와 조건을 해당 건의 불량
원인이나 불량 방향으로 해석하면 안 된다. 범주형 feature의 대표 split은 작업자용
수치 threshold 대신 원본 category 일치 조건으로 변환해 표시한다.

### 아직 없는 기능

- 판정 결과의 영구 저장 및 감사 로그
- 여러 작업자 또는 여러 브라우저 세션 간 상태 공유
- 실제 검사 이미지와 CSV Record ID 연결
- 검사 건별 Local SHAP 계산과 불량 방향 판정
- 큐 중간 재시작을 위한 체크포인트
- 모델 정상 판정 전체를 검색하는 별도 조회 화면과 영구 추론 감사 로그
- 작업자 인증 및 권한 관리

## 파일별 역할

- `dashboard/app.py`: Streamlit 화면, 세션 상태와 판정 상호작용
- `dashboard/data_source.py`: CSV 전처리와 시간순 Test 스트림 제공
- `dashboard/explanation.py`: Dongjin 027 기반 정적 Global SHAP 규칙과 신호 공급자
- `dashboard/inference.py`: Type별 모델 로딩, 확률 추론과 중요 feature 조회
- `dashboard/config.py`: 데이터·모델·이미지 경로와 실행 설정
- `dashboard/requirements.txt`: 저장 모델과 호환되는 Python 패키지 버전
- `dashboard/assets/sample_images/`: CSV와 독립적으로 반복하는 샘플 이미지
- `dashboard/README.md`: 설치 및 실행 방법

모델이 변경될 때는 `inference.py`의 추론 인터페이스를 유지하면 UI 변경 범위를 줄일
수 있다.

## 검증된 내용

- `python -m py_compile dashboard/*.py` 통과
- Test 행이 0.3초마다 한 건씩 단건 추론되고 정상 행이 메인 화면에 표시된 뒤 자동
  진행되는 것 확인
- 모델 불량 행에서 자동 갱신이 멈추고 작업자 판정 직후 다음 행으로 즉시 교체되는 것 확인
- Streamlit AppTest에서 앱 초기화, feature 신호 6개, 정상 판정과 다음 큐 이동 확인
- 정적 Global SHAP 규칙의 연속형·범주형 대표 조건 비교 확인
- 공통 probability threshold 초과 시 빨간색 경고 표시 확인
- Type 4의 Global SHAP 빈 상태 표시 확인
- peace 005 artifact 저장 후 reload 예측 일치 검사 통과
- 1280 × 720 브라우저에서 전체 페이지 스크롤이 생기지 않는 것 확인
- 실제 브라우저에서 `RUNNING → MANUAL REVIEW → RUNNING` 상태 전환 확인
- 정상 판정 후 직전 검사 결과와 히스토리가 갱신되는 것 확인
- 모델 정상 판정과 작업자 판정이 처리 순서대로 같은 히스토리에 표시되는 것 확인
- 직전 검사 결과 텍스트와 히스토리 헤더가 겹치지 않는 것 확인
- 카드 간 외부 간격 없이 그리드 경계가 연결되는 것 확인

## 실행 명령

저장소 루트에서 실행한다.

```bash
source .venv/bin/activate
streamlit run dashboard/app.py
```

기본 접속 주소는 `http://localhost:8501`이다.

## 다음 작업 후보

1. 검사 건별 Local SHAP 결과와 불량 방향 반환 규격을 합의한다.
2. 작업자 판정 결과를 저장하거나 외부로 내보내는 인터페이스를 정의한다.
3. 실제 검사 이미지 식별자와 Record ID 연결 규칙을 정한다.
4. 현장 작업자 피드백을 받아 글자 크기, 경고 기준과 버튼 동작을 확정한다.

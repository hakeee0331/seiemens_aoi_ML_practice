# AOI 대시보드 현재 작업 현황

이 문서는 AOI 수동 검사 대시보드의 인수인계를 위한 현재 구현 상태를 기록한다.
일반적인 실행 방법은 `dashboard/README.md`를 참고하고, 이 문서에서는 특정 커밋을
기준으로 실제로 구현된 범위와 남은 임시 구현을 다룬다.

## 기록 기준

- 기록일: 2026-08-25 (KST)
- 브랜치: `27-layout`
- 기준 HEAD: `835334e`
- 기능 커밋: `fa13519 feat: add Streamlit manual inspection dashboard`
- 문서 커밋: `835334e docs: document dashboard setup and usage`

이 문서를 작성한 시점의 기준 커밋에는 대시보드 코드, Streamlit 의존성, 샘플 JPG
10장과 실행 문서가 포함되어 있다. 저장소의 별도 미추적 `docs` PDF와 `src/` 파일은
대시보드 작업 및 위 커밋에 포함하지 않았다.

## 구현 완료 범위

### 검사 큐

- `data/raw/dataset.csv`를 읽어 한 행씩 검사 대상으로 제공한다.
- 모델 artifact의 Validation 종료 시각 이후 데이터만 Test 큐로 사용한다.
- `record_id`와 `timestamp`를 제외한 컬럼이 모두 같은 행은 중복으로 제거한다.
- 검사 큐는 시간순으로 정렬한다.
- 현재 데이터와 모델을 기준으로 Test 큐는 78,396건이다.
- CSV의 실제 정답인 `class`는 내부에 유지하지만 작업자 판정 전에는 노출하지 않는다.

### 모델 추론

- 모델: `models/0824_kimjaehak_006_type_conditioned_baseline.pkl`
- Inspection Type별 XGBoost 모델을 사용해 불량 확률을 계산한다.
- 현재 행의 Inspection Type에 맞는 입력 feature만 추론에 전달한다.
- 모델의 decision threshold는 artifact에서 읽을 수 있지만, 현재 화면에서는 작업자의
  수동 판정을 대신하지 않는다.

### Feature 시계열

- 시계열 그래프 2개를 제공한다.
- 각 그래프는 현재 Inspection Type과 같은 과거 데이터만 사용한다.
- 미래 데이터는 포함하지 않고 현재 검사 시점까지 최근 80건을 표시한다.
- 각 Type 모델의 `feature_importances_` 상위 2개를 최초 기본값으로 사용한다.
- 작업자가 선택기를 변경하면 해당 Type의 선택은 현재 Streamlit 세션에서 유지된다.

현재 모델의 기본 feature는 다음과 같다.

| Inspection Type | Trend 1 | Trend 2 |
|---|---|---|
| 0 | `inspection_feat56` | `inspection_feat44` |
| 1 | `inspection_feat48` | `meta_feat1` |
| 2 | `inspection_feat95` | `inspection_feat94` |
| 3 | `inspection_feat96` | `inspection_feat12` |
| 4 | `inspection_feat2` | `meta_feat4` |

### 작업자 판정

- `NORMAL / 정상 판정`과 `DEFECT / 실제 불량 판정` 버튼을 제공한다.
- 판정 시 현재 항목을 직전 검사 결과로 옮기고 큐의 다음 행으로 진행한다.
- 판정 시각, Record ID, Inspection Type, 모델 불량 확률과 작업자 판정을 히스토리에
  기록한다.
- 직전 검사 결과와 판정 히스토리는 `st.session_state`에만 저장한다.
- 데이터베이스나 파일에는 기록하지 않으므로 앱 세션이 초기화되면 판정도 사라진다.

### 샘플 이미지

- `dashboard/assets/sample_images/`의 JPG 10장을 이름순으로 읽는다.
- 파일 확장자의 대소문자는 구분하지 않는다.
- CSV 행과 이미지는 아직 연결되어 있지 않다.
- 큐 위치를 기준으로 10장을 반복해 화면에 표시한다.

## 현재 UI 기준

- 고정 화면: `1280 × 720`, 16:9
- 공장 내 데스크톱 모니터 전용
- 모바일 및 반응형 레이아웃 미지원
- 화면 전체를 카드 모음이 아닌 2열 고정 그리드로 구성
- 좌측: 현재 검사, feature 시계열 2개, 판정 버튼
- 우측: 직전 검사 결과, 작업자 판정 히스토리
- 전체 페이지 스크롤 없이 한 화면에 표시
- 히스토리가 길어지면 히스토리 셀 내부에서만 스크롤
- 회색조 배경과 각진 실선 구획 사용
- 불량 판정 버튼만 빨간색 유지
- 이모지와 장식성 요소는 사용하지 않음

## 임시 구현 및 제한사항

### SHAP 원인 feature

SHAP 연동은 아직 구현되지 않았다. 현재 원인 feature는 UI와 인터페이스 확인을 위한
Type별 고정 데모 값이다.

| Inspection Type | 임시 원인 feature |
|---|---|
| 0 | `inspection_feat24` |
| 1 | `inspection_feat48` |
| 2 | `inspection_feat96` |
| 3 | `inspection_feat95` |
| 4 | `inspection_feat34` |

화면에서도 `DEMO`와 `SHAP 연동 준비 중`으로 명시한다. 이 값은 모델의 실제 개별
예측 기여도나 시계열 그래프 기본값과 연동되지 않는다.

### 아직 없는 기능

- 판정 결과의 영구 저장 및 감사 로그
- 여러 작업자 또는 여러 브라우저 세션 간 상태 공유
- 실제 검사 이미지와 CSV Record ID 연결
- 실제 SHAP 계산과 원인 feature 자동 선택
- 큐 중간 재시작을 위한 체크포인트
- 작업자 인증 및 권한 관리

## 파일별 역할

- `dashboard/app.py`: Streamlit 화면, 세션 상태와 판정 상호작용
- `dashboard/data_source.py`: CSV 전처리, Test 큐와 시계열 데이터 제공
- `dashboard/inference.py`: Type별 모델 로딩, 확률 추론과 중요 feature 조회
- `dashboard/config.py`: 데이터·모델·이미지 경로와 데모 설정
- `dashboard/assets/sample_images/`: CSV와 독립적으로 반복하는 샘플 이미지
- `dashboard/README.md`: 설치 및 실행 방법

모델이 변경될 때는 `inference.py`의 추론 인터페이스를 유지하면 UI 변경 범위를 줄일
수 있다.

## 검증된 내용

- `python -m py_compile dashboard/*.py` 통과
- Streamlit AppTest에서 앱 초기화, selector 2개, 정상 판정과 다음 큐 이동 확인
- 1280 × 720 브라우저에서 전체 페이지 스크롤이 생기지 않는 것 확인
- 정상 판정 후 직전 검사 결과와 히스토리가 갱신되는 것 확인
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

1. 팀원이 준비하는 SHAP 결과 형식과 `inference.py`의 반환 규격을 합의한다.
2. 작업자 판정 결과를 저장하거나 외부로 내보내는 인터페이스를 정의한다.
3. 실제 검사 이미지 식별자와 Record ID 연결 규칙을 정한다.
4. 현장 작업자 피드백을 받아 글자 크기, 경고 기준과 버튼 동작을 확정한다.

# 실험 목록

모든 실험 노트북은 이 디렉터리에 동일한 stem의 설명 문서를 가져야 한다. 새 실험을 완료하거나 상태가 바뀌면 아래 표를 갱신한다.

| 실험 ID | 상태 | 작성자 | 설명 | 모델 | 주요 결과 |
|---|---|---|---|---|---|
| `0823_example_001_baseline` | Example | example | 실험 작성 형식 예시 | Logistic Regression | 합성 데이터 실행 예시 |
| `0823_lsw_001_eda` | 완료 | lsw | 원본 데이터 스키마/결측치/클래스 분포/상수열/중복행/시간 커버리지 탐색 | 해당 없음 | NaN 결측 0건, 무효 컬럼 채움값이 type마다 다름, 상수열·중복행 다수 발견 |
| `0823_dongjin_000_EDA` | 완료 | dongjin | 데이터 탐색 및 품질 분석 | 해당 없음 | 검사 유형별 분포 확인 및 레이블 노이즈 발견 |
| `0823_kimjaehak_001_eda` | 완료 | kimjaehak | AOI 원본 데이터의 전반적 구조와 품질 분석 | 해당 없음 | 440,274행, true defect 1.0498%, 완전 중복 초과 행 8,752건 |
| `0823_kimjaehak_002_temporal_drift` | 완료 | kimjaehak | 시간순 그룹 분할과 train-test drift 분석 | 해당 없음 | test 불량률 2.6405%, PSI 큰 피처 20/113개 |
| `0823_kimjaehak_003_feature_validity` | 완료 | kimjaehak | 검사유형별 유효·무효 피처 패턴 분석 | 해당 없음 | 전역 미매핑 5개, 유형별 잠정 후보 27/12/18/17/10개 |
| `0823_kimjaehak_004_duplicate_groups` | 완료 | kimjaehak | 완전 중복·timestamp 그룹·signature 재등장 분석 | 해당 없음 | 중복 초과 8,752건, test의 9.6704%가 이전 signature 재등장 |
| `0824_peace_001_eda` | 완료 | peace | Siemens AOI 데이터 EDA와 시간 드리프트 점검 | 해당 없음 | 실제 불량 1.05%, Test 불량률은 Train의 약 5.2배 |
| `0824_kimjaehak_005_xgboost_baseline` | 완료 | kimjaehak | 시간순 분할 기반 XGBoost 단순 베이스라인 | XGBoost | Test F1 0.3066, Recall 0.2623, PR-AUC 0.2368 |

## 상태 값

- `Example`: 형식 참고용 파일
- `진행 중`: 실험이 아직 완료되지 않음
- `완료`: 전체 셀 실행과 문서 기록이 완료됨
- `중단`: 실험을 중단했으며 이유가 기록됨

## 추가 규칙

- 실험 ID는 `MMDD_작성자_실험번호_설명` 형식을 사용한다.
- 실험 번호는 날짜가 바뀌어도 작성자별로 계속 증가시킨다.
- 노트북, 실험 문서, 저장 모델은 동일한 stem을 사용한다.
- 주요 결과에는 핵심 지표나 한 줄 결론만 기록한다.
- 상세 코드와 출력은 노트북에, 목적과 변경사항 및 결론은 개별 실험 문서에 기록한다.
- 모델의 최종 Test 비교 결과는 `docs/model_val.md`에도 기록한다.

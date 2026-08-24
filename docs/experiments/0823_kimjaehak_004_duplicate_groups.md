# 0823_kimjaehak_004_duplicate_groups

## 연결된 노트북

`notebooks/0823_kimjaehak_004_duplicate_groups.ipynb`

## 상태

완료

## 목적

EDA 001에서 확인한 `record_id` 제외 완전 중복과 timestamp 그룹을 심층 분석하고, 시간·타깃 제외 입력 signature의 반복 및 label conflict가 데이터 분할과 평가에 미치는 영향을 정량화한다.

## 이전 실험 대비 주요 변경사항

- 완전 중복 그룹의 크기, 검사유형, 라벨, 월별 분포를 집계한다.
- 같은 timestamp 내부 입력 반복과 여러 timestamp에 걸친 입력 signature 재등장을 구분한다.
- timestamp 그룹의 크기, 포함 검사유형 수, mixed-label 구조를 분석한다.
- timestamp 그룹 경계를 보존하는 시간순 60/20/20 분할을 구성하고 split 사이 입력 signature 중복을 측정한다.
- pandas 64-bit 행 해시를 사용해 75~77개 컬럼의 그룹화를 메모리 안전하게 수행하고 해시 충돌 한계를 명시한다.

## 평가 방법과 주요 결과

- 기존 `.venv`의 Python 3.12 및 `requirements.txt` 패키지만 사용해 노트북을 위에서 아래로 전체 실행했다.
- 완전 중복은 4,250개 그룹, 13,002행이며 초과 행은 8,752건(전체의 1.99%)이다. 중복 그룹 크기의 중앙값은 2행, 95백분위는 9행, 최댓값은 17행이다.
- 검사유형별 완전 중복 초과 행은 type 0이 6,295건, type 1이 8건, type 2가 2,085건, type 3이 364건이며 type 4는 0건이다. 각 유형 내 초과 비율은 각각 6.4861%, 0.0139%, 1.6267%, 0.2396%, 0%다.
- 완전 중복 초과 행의 62.69%인 5,487건이 1970년 8월에 나타났고, 해당 월 내부 초과 비율은 5.0632%로 가장 높다.
- 시간·타깃 제외 입력 signature는 391,922개이고, 이 중 반복 signature는 10,458개 그룹, 58,810행이다. 10,175개 반복 그룹은 둘 이상의 timestamp에 걸쳐 재등장하며, 한 timestamp에만 존재하는 반복 그룹은 283개다.
- 동일 timestamp 내부에서 반복된 입력 signature는 4,259개 그룹, 13,025행이고 초과 행은 8,766건이다. 이 중 14개 그룹은 입력이 같지만 label이 섞여 있다.
- 전체 입력 signature 중 label conflict는 70개 그룹, 관련 행은 14,037건이다. signature당 최대 행 수는 5,546행, 최대 timestamp 수는 1,638개로 일부 반복 signature의 영향이 매우 크다.
- timestamp 그룹은 39,742개이며 중앙값 6행, 95백분위 36.95행, 최댓값 557행이다. 여러 행을 가진 그룹은 33,902개, 여러 검사유형을 가진 그룹은 27,322개, mixed-label 그룹은 715개이며 mixed-label 그룹에 포함된 행은 11,588건이다.
- timestamp 경계를 유지한 시간순 분할은 train 264,343행(26,063그룹), validation 87,879행(6,586그룹), test 88,052행(7,093그룹)이다. 어느 timestamp도 split 사이에 나뉘지 않는다.
- split 두 곳 이상에 등장한 입력 signature는 2,948개(전체 고유 signature의 0.7522%)이고 관련 행은 30,455건이다. validation에서 train에 이미 등장한 signature 행은 4,268건(4.8567%), test에서 train 또는 validation에 등장한 signature 행은 8,515건(9.6704%)이다. validation/test를 합치면 과거에 본 signature 행은 12,783건(7.2659%)이다.
- cross-split signature 중 label conflict가 있는 그룹은 43개다.
- 완전 중복 해시 집계는 77개 실제 컬럼의 `DataFrame.duplicated` 결과와 일치했다. 입력 signature는 64-bit 해시 기반이므로 이론적인 충돌 가능성이 남으며 운영 식별자나 삭제 키로 사용할 수 없다.

## 결론과 다음 단계

- 기본 평가 분할은 timestamp 그룹 경계를 보존한 시간순 split으로 구성하고 행 단위 무작위 분할은 사용하지 않는다.
- 완전 중복은 중복 로깅인지 실제 반복 납땜 지점인지 확인되지 않았으므로 원본에서 임의로 삭제하지 않는다. 학습 데이터에서만 `중복 유지`, `그룹별 1행`, `그룹 역빈도 sample weight`를 비교하고 validation/test는 현실 빈도를 보존한다.
- 입력 signature 재등장은 실제 운영 반복일 수도 있으므로 전체 성능 외에 `과거에 본 signature`와 `처음 보는 signature`의 성능을 분리해 보고하고, 재등장 signature를 제거한 보조 평가를 제시한다.
- label-conflict signature는 강제 다수결로 덮어쓰지 않고 오류 분석 플래그로 관리한다.
- timestamp와 입력 signature는 PCB 고유 ID가 아니다. 비식별 PCB 그룹 ID를 확보할 수 있다면 timestamp보다 우선 사용한다.
- 다음 모델링 실험에서는 시간순 timestamp-group split을 공통 프로토콜로 확정하고, 중복 처리 세 전략과 seen/unseen signature 성능을 비교한다.

## 저장된 모델 경로

해당 없음. EDA 실험이므로 모델을 생성하지 않는다.

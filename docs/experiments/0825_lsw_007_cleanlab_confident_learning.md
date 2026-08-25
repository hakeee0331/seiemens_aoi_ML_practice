# 0825_lsw_007_cleanlab_confident_learning

## 연결된 노트북

`notebooks/0825_lsw_007_cleanlab_confident_learning.ipynb`

## 상태

완료

## 목적

004의 라벨 클렌징(피처 완전 동일+라벨만 다른 행 제거)과 005의 라벨 보정은 아주 좁은 정의의
모순만 잡았다. cleanlab의 confident learning(로드맵 Phase 3-1)으로 "모델이 강하게 반대하는
라벨"을 통계적으로 넓게 찾아내고, **baseline이 아니라 004에서 확정된 검사유형별 현재 최고
기법 대비**로 개선 여부를 판단한다("현재 최고 유지 + 개선분 탐색" 방식으로 전환).

## 방법

- 검사유형별 Train에 대해 StratifiedKFold(최대 5-fold) out-of-fold 예측 확률을 구하고
  `cleanlab.filter.find_label_issues`로 이슈 행을 찾는다.
- 이슈 행을 제거한 Train 위에서 기존 6가지 옵션(baseline/class_weight/smote/adasyn/
  undersample/label_cleansing)을 전부 다시 적용해보고, 비용비율(1:10, 1:100)마다 따로 최고를
  골라 004의 "현재 최고"와 비교한다.
- Validation/Test는 원본 그대로 유지(클렌징은 Train에만 적용).

## 주요 결과

### 현재 최고 기법 대비

| type | 비용비율 | 기존 최고 | 비용 | cleanlab+최고 조합 | 비용 | 개선 |
|---|---|---|---:|---|---:|---:|
| 0 | 1:10 | label_cleansing | 5,678 | +adasyn | 7,621 | -1,943 악화 |
| 0 | 1:100 | label_cleansing | 9,818 | +smote | 9,916 | -98 악화 |
| 1 | 1:10 | undersample | 6,209 | +undersample | 5,961 | +248 개선 |
| 1 | 1:100 | undersample | 7,289 | +smote | 8,355 | -1,066 악화 |
| 2 | 1:10 | undersample | 10,541 | +undersample | 12,053 | -1,512 악화 |
| 2 | 1:100 | undersample | 14,411 | +undersample | 14,753 | -342 악화 |
| **3** | **1:10** | adasyn | 17,515 | **+smote** | **10,058** | **+7,457 개선(43%↓)** |
| **3** | **1:100** | smote | 22,456 | **+smote** | **22,298** | **+158 개선** |
| 4 | 1:10/1:100 | undersample | 715 | +undersample | 715 | 변화 없음 |

**type3에서 cleanlab+smote가 두 비용비율 모두 확실히 기존 최고를 이긴다**(1:10에서 43% 비용
절감). type1은 1:10에서만 소폭 개선. type0/2/4는 기존 최고가 여전히 낫다.

### type0/2가 나빠진 이유

- type0(Train 양성 57건, baseline PR-AUC 0.067): out-of-fold 확률 추정 자체가 5-fold 기준
  fold당 양성 10여건으로 불안정하다. 실제로 양성 52/57건이 flagged됐는데, 이는 노이즈 제거가
  아니라 약한 신호를 가진 진짜 양성까지 통계적으로 이상해 보여 지워졌을 가능성이 크다(baseline
  대비 TN이 8,857→779로 폭락 — 모델이 훨씬 공격적으로 바뀜).
- type2(Train 양성 579건, PR-AUC 0.357로 나쁘지 않음)도 나빠져서 표본 크기만의 문제는 아니다.
  notes.md에서 확인한 type2 특유의 concept drift(판정기준 변화)가 cleanlab에게도 "일관성 없는
  라벨"로 잡혀, 지우면 안 되는 정당한 최근 신호까지 같이 제거됐을 가능성 — 004/005에서 type2의
  모순 라벨을 건드리면(삭제든 보정이든) 항상 손해였던 것과 같은 패턴.
- type3(양성 620건, PR-AUC 0.270)은 표본도 충분하고 type2 같은 강한 concept drift 신호도 없어
  cleanlab이 진짜 노이즈만 상대적으로 깨끗하게 골라낸 것으로 보인다.

## 검사유형별 최적 조합 갱신 (003~007 종합)

| type | 1:10 최적 | 1:100 최적 | 비고 |
|---|---|---|---|
| 0 | label_cleansing | label_cleansing | cleanlab 악화 — 표본 부족으로 신뢰 불가 |
| 1 | undersample | undersample | cleanlab은 1:10만 근소 개선, 굳이 바꿀 실익 적음 |
| 2 | undersample | undersample | cleanlab 악화 — concept drift와 충돌 추정 |
| **3** | **cleanlab + smote** | **cleanlab + smote** | **새 챔피언** |
| 4 | undersample | undersample | 표본 부족 |

## 결론 및 다음 단계

- "라벨 노이즈/drift 관련 성능 개선 방법이 없다"는 것은 사실이 아니다 — type3에서 cleanlab이
  뚜렷한 개선을 냈다. 다만 표본이 작거나(type0) concept drift가 강한(type2) 유형에는 confident
  learning류 기법을 무분별하게 적용하면 안 된다는 게 핵심 교훈이다.
- 다음: 사용자가 제안한 "치팅 아닌" 임계값 재조정(과거 확정 구간의 관측 불량률로 다음 구간
  임계값을 조정) 실험.

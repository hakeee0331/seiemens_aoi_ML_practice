# siemens_aoi_v2 — 데이터셋 노트

## 출처

- 논문: "Data of automated optical inspection of surface-mounted technology electronic
  production" — *Data in Brief* (Elsevier, 2024)
  - ScienceDirect: https://www.sciencedirect.com/science/article/pii/S2352340924000830
  - PMC 전문: https://pmc.ncbi.nlm.nih.gov/articles/PMC10847760/
- 원본 데이터: Mendeley Data, DOI 10.17632/99jzmh9658
  https://data.mendeley.com/datasets/99jzmh9658/2
- 저자/소속: Korbinian Pfab, Roman Eichler, Adarsh Mallandur, Marcel Rothering
  (Helsinki University 컴퓨터공학과 + Siemens AG)

## 파일 구성 (로컬)

- `siemens_aoi_v2/Publication data Data of automated optical inspection of surface-mounted
  technology electronic production/dataset.csv` — 약 334MB, 440,274행 × 77열
- 같은 폴더의 `mapping.json` — `inspection_type`(0~4) 별로 실제 유효한
  `inspection_feat*` 컬럼 목록을 정의. 검사유형마다 쓰이는 피처 집합이 다르므로,
  분석 전에 반드시 이 매핑을 참고해서 무의미한 0값(해당 없음)과 실제 측정값 0을
  구분해야 함.

## 데이터가 다루는 문제

SMT(표면실장) PCB가 납땜 후 AOI(자동광학검사)를 거치는데, AOI는 종종 정상 기판을
불량으로 오판(**false call**)한다. 이로 인해 수동검사소(MIS, Manual Inspection
Station)에서 불필요한 재검수 인력이 낭비됨. 이 데이터셋은 **AOI가 불량으로 판정한
것만** 모아, MIS 작업자가 실제로 true defect인지 false call인지 재판정한 결과를
라벨로 붙인 것. → 목적은 이 라벨을 예측해 false call을 자동으로 걸러내는 모델을
만드는 것 (false call reduction).

- 수집 기간: 132일, 실제 생산 라인 그대로 (실험 설계 변경 없음)
- 수집처: Siemens AG 독일 공장, 생산라인 1개

## 컬럼 사전

| 컬럼 | 의미 |
|---|---|
| `index`(첫 열, 헤더 없음) | 행 번호 |
| `timestamp` | PCB가 AOI에 진입한 시각. 개인정보/시점 익명화를 위해 연도는 전부 1970으로 치환됨. 같은 PCB의 여러 납땜점이 검사되므로 동일 timestamp를 가진 행이 다수 존재 |
| `class` | 0 = false call(AOI 오탐, 실제는 정상) / 1 = true defect(실제 불량). **클래스 극도로 불균형**(아래 표) |
| `inspection_type` | AOI 검사 설정 유형(0~4). 기판/부품별로 무엇을 어떻게 측정할지 정의하는 구성값. 유형마다 사용되는 `inspection_feat` 컬럼 집합이 다름 (`mapping.json` 참고) |
| `meta_feat1`~`meta_feat4` | 검사유형 내에서 값이 고정되는 범주형 메타정보: AOI 머신 에러코드, 검사 대상 부품 종류, PCB 상 부품 실장 각도 등 |
| `inspection_feat1`~`inspection_feat99` (일부 결번, 총 70개 사용) | AOI 카메라 이미지 기반 물리 측정값. X/Y 좌표 오프셋, 납땜 패드 크기, 다중 패드 오접속 여부, 각도 오프셋, 부품 극성(polarity) 등. **0~1로 정규화되어 있고 실제 물리 단위는 비공개**. 해당 검사유형에서 쓰이지 않는 컬럼은 기본값 0으로 채워지므로, 0이 "측정값 0"인지 "해당 없음"인지 mapping.json으로 확인 필요 |

### 클래스 불균형 (검사유형별)

| inspection_type | class 0 (false call) | class 1 (true defect) | 불량 비율 |
|---|---|---|---|
| 0 | 96,735 | 318 | 0.3% |
| 1 | 56,095 | 1,578 | 2.8% |
| 2 | 126,828 | 1,346 | 1.1% |
| 3 | 150,650 | 1,281 | 0.9% |
| 4 | 5,344 | 99 | 1.9% |

## inspection_type의 정확한 의미 (2026-08-22 조사)

**질문**: 같은 부품을 inspection_type을 다르게 해서 교차검증하는 것인가, 아니면 부품
종류에 따라 inspection_type이 정해지는 것인가?

**결론**: 둘 다 아님. 논문 원문(Data Description 섹션):

> "AOI machines in general can execute different measurements. Therefore, it is
> necessary that a technology expert configures where on the PCB are soldering
> spots and components that need to be inspected in what ways for all different
> types of PCBs. These configurations are so-called inspection types."

즉 `inspection_type`은 **부품의 속성이 아니라, 기술 전문가가 "PCB 종류별로 이
위치에서 무엇을 어떤 방식으로 측정할지" 사전 설정해둔 검사 구성**이다. 부품 종류가
inspection_type을 1:1로 결정하지도 않고, 동일 부품을 의도적으로 여러 설정으로
재검증하는 것도 아니다 (논문에 그런 설계 의도 언급 없음).

실측 검증(dataset.csv 440,274행 전수 스캔, meta_feat 값별로 관측된 inspection_type
집합의 크기):

| 컬럼 | 고유값 수 | 하나의 inspection_type에만 대응 | 여러 inspection_type에 걸쳐 나타남 |
|---|---|---|---|
| meta_feat1 | 75 | 36 | 39 |
| meta_feat2 | 5 | 2 | 3 |
| meta_feat3 | 2 | 0 | 2 |
| meta_feat4 | 49 | 27 | 22 |

meta_feat 값 상당수(특히 meta_feat1, meta_feat3)가 여러 inspection_type에 걸쳐
나타나므로 "부품 종류 → inspection_type 결정" 가설은 기각됨. 실제로는 PCB
설계/라인 구성상 유사한 측정 구성이 여러 PCB 타입·위치에 재사용되는 것으로 보임.

- 논문은 meta_feat1~4 각각이 정확히 무엇인지 개별적으로 명시하지 않고 "에러코드,
  부품 종류, 실장 각도 등을 포함한다"고 뭉뚱그려 서술함 → 어느 컬럼이 정확히
  "부품 종류"인지는 논문만으로는 확정 불가. (meta_feat2, meta_feat3는 고유값이
  각 5개/2개뿐이라 "부품 종류"보다는 이진 플래그나 소수 범주의 에러코드/각도
  구간에 더 가까워 보임 — 추가 검증 필요)

**추가 질문: "그럼 PCB 종류별로 inspection_type이 결정되는 건가?"**

아니라고 판단됨. inspection_type은 5개뿐인데 실제 생산되는 PCB 종류(설계)는 그보다
훨씬 많을 것이므로 "PCB 종류 1개 = inspection_type 1개" 대응 구조는 성립하기
어려움. 논문 문장을 풀면 inspection_type은 "PCB 종류 자체의 식별자"가 아니라
**"이 위치/부품에 필요한 측정 방식(방법론) 카테고리"**에 가까움 — 서로 다른 PCB
종류라도 비슷한 형태의 납땜점(예: 커넥터 핀형, 칩형, BGA형)이면 같은
inspection_type을 공유하는 구조로 추정.

- ❌ PCB 종류 → inspection_type 1:1 결정
- ✅ "이 위치에서 필요한 측정 방식" → inspection_type 분류, 여러 PCB 종류가 이를 재사용

**한계**: 이 데이터셋에는 PCB 종류(설계/모델)를 직접 식별하는 컬럼이 없어서 이
가설을 데이터로 직접 검증할 수는 없음. 논문 문장 해석에 근거한 추정이며, 100%
데이터로 확증된 것은 아님.

**추가 질문: "그럼 PCB 한 장(개별 보드)이 inspection_type 하나만 갖나?"**

아니오. `timestamp`를 PCB 단위로 보고(같은 timestamp = 같은 PCB의 여러 납땜점) 전수
검증함 (440,274행 전체 스캔):

- 고유 timestamp(=PCB) 수: 39,742개
- inspection_type이 하나만 나타난 PCB: 12,420개 (약 31%)
- inspection_type이 2개 이상 섞여 나타난 PCB: **27,322개 (약 69%)**
  - 예: `1970-10-18 20:01:23+00:00` 한 PCB에서 inspection_type 0,1,2,3이 전부 관측됨

→ **한 PCB 안에서도 검사 위치/부품마다 서로 다른 inspection_type이 적용된다.**
PCB 단위로 inspection_type이 고정되는 게 아니라, "이 PCB의 이 지점은 type 0,
저 지점은 type 2"처럼 지점별로 달라짐. 이는 "inspection_type = PCB 종류 식별자"가
아니라 "위치/부품별 측정 방식 카테고리"라는 해석을 뒷받침함.

## 알려진 한계점 (논문에서 명시)

1. **라벨 노이즈** — 각 라벨은 MIS 작업자 1인의 단독 판정. 132일간 여러 작업자가
   교대 근무했고, 작업자별/시간별 오류율 차이가 존재할 수 있으나 정량화되지 않음.
2. **클래스 불균형** — true defect가 검사유형별로 0.3~2.8%에 불과. 불균형 대응
   기법(리샘플링, 가중치 조정, threshold 튜닝 등) 없이 단순 정확도로 평가하면
   무의미함.
3. **Distribution drift** — AOI 프로그램 수정이나 인지되지 않은 외부 요인으로 인해
   132일 동안 피처 분포가 변할 수 있음. drift의 유형·시점·빈도는 전혀 파악되지
   않은 상태. → 시계열 분할(예: 앞부분으로 학습, 뒷부분으로 검증) 시 성능 저하가
   나타날 수 있으니 유의.

## 앞으로 추가할 항목

- [ ] 실제 dataset.csv를 로드해서 확인한 결측치/이상치 패턴
- [ ] inspection_type별 feature importance 또는 상관관계 분석 결과
- [ ] 전처리/모델링 시도 및 성능 기록

# 프로젝트 확장 방향 & 실행 로드맵

## 현재 방향 (2026-08-23 기준, "실전제조AI최종프로젝트발표주제.pdf" 요약)

- 제목: "실제 불량은 놓치지 않고, 불필요한 수동검사는 줄일 수 있을까?" —
  Siemens PCB AOI 데이터 기반 비용민감형 False Call 감소 및 CPU Edge 추론 PoC
- 포지셔닝: **AOI를 대체하는 모델이 아니라, AOI가 불량 의심한 포인트를 한 번 더
  거르는 "안전한 2차 판정기"**
- 목표 지표:
  - Slip Rate(실제 불량을 정상으로 오판해 유출) ≤ 1%
  - False Call 수동검사량 40% 이상 감소 (Volume Reduction)
  - 저사양 CPU에서 빠르게 도는 경량 모델 검증
- 모델 라인업: Dummy → Logistic Regression(baseline) → XGBoost(주력) →
  Compact XGBoost(edge 경량화) → INT8 MLP Distillation(선택 실험)
- 학습 전략: 검사유형별 데이터 분리 → 시간순 Train/Val/Test 분할 → 학습 →
  Validation에서 운영 임계값 선택 → 최근 Test로 최종 평가
- 평가지표: Slip Rate, Volume Reduction, 총비용(FP×오검비용 + FN×미검비용)
- Compact 모델 경량화: feature selection, tree depth 축소, early stopping,
  ONNX 변환 + ONNX Runtime CPU 추론, INT8 MLP distillation

**교수님 피드백: scope이 작다** → 아래 4가지를 추가해 "단순 이진분류 + 경량화"를
넘어 데이터 자체의 알려진 난제(불균형, drift, 라벨노이즈)에 대한 방법론적 기여와
비지도 이상탐지 관점을 더한 프로젝트로 확장.

이 4가지는 우연히도 [siemens_aoi_v2/notes.md](../siemens_aoi_v2/notes.md)에 이미
정리해둔 이 데이터셋의 **논문 명시 한계점**(라벨 노이즈, 클래스 불균형, distribution
drift)과 정확히 겹친다 — 즉 "데이터셋이 원래 안고 있는 문제를 정면으로 다루는
프로젝트"로 자연스럽게 확장 가능.

---

## 확장 방향 4가지 정리

### 1. 데이터 불균형(class imbalance) 대응
- **현재 상태**: cost-sensitive 임계값 선택으로 간접 대응만 하고 있음. 클래스
  비율은 검사유형별 0.3~2.8%로 극단적 불균형([notes.md](../siemens_aoi_v2/notes.md) 표 참고).
- **확장 포인트**: 리샘플링/가중치 기법을 명시적으로 비교하는 실험 축 추가
  (class weighting, SMOTE/ADASYN, undersampling 등). "임계값 튜닝만으론 부족한
  지점을 리샘플링이 보완하는가"를 정량 비교.

### 2. Distribution drift 대응 방법 설계
- **현재 상태**: 시간순 분할만 하고 있고, drift 자체를 탐지·대응하는 로직은 없음.
- **확장 포인트**: 132일 구간을 윈도우 단위로 쪼개 실제로 drift가 있는지 정량
  탐지(PSI/KS-test 등)하고, drift에 강건한 학습 전략(주기적 재학습, 최근 데이터
  가중치 부여, drift 감지 알고리즘)을 설계·검증. 논문에서 "drift 유형/시점 미파악"
  이라 밝힌 부분을 데이터로 직접 규명하는 셈이라 스토리가 좋음.

### 3. 라벨 오류에 대한 강건성 조치
- **현재 상태**: 라벨을 그대로 신뢰하고 학습 중. 논문은 "MIS 작업자 1인 단독
  판정, 오류율 미파악"이라고 명시.
- **확장 포인트**: confident learning류 기법(cleanlab 등) 또는 자체 구현
  cross-validation 기반으로 "라벨이 의심스러운 샘플"을 찾아내고, 이를 제거/재가중
  했을 때 모델이 더 안정적인지 검증. Slip Rate처럼 안전이 중요한 지표에서 특히
  의미 있는 방어선.

### 4. Unsupervised 이상탐지 도입
- **현재 상태**: 지도학습 이진분류만 존재.
- **확장 포인트**: Isolation Forest/One-Class SVM/Autoencoder 등으로 "정상(false
  call) 분포"를 학습해 이상 스코어를 뽑고, 이를 기존 지도학습 2차 판정기와 결합
  (앙상블 또는 추가 피처로). 라벨 없이도 이상 신호를 잡아낼 수 있다는 걸 보여주면
  "단순 분류기"라는 인상에서 벗어남. 부가적으로 이 이상탐지 스코어를 2번(drift
  탐지)에도 재사용할 수 있어 확장끼리 시너지가 남.

---

## 실행 로드맵 (작은 단위로 분해)

### Phase 0 — 기준선 확보 (모든 확장의 비교 기준)
- [ ] 기존 PPT에 나온 학습 전략 그대로 재현: 검사유형별 분리 → 시간순 분할 →
      Dummy/Logistic/XGBoost 학습 → Validation 임계값 선택 → Test 평가
- [ ] Slip Rate / Volume Reduction / 총비용 3개 지표를 코드로 고정 (이후 모든
      실험이 이 함수를 그대로 재사용해야 비교가 성립함)
- [ ] 검사유형별로 baseline 성능표 산출 및 저장 (재현 가능하게 스크립트화)

### Phase 1 — 데이터 불균형 대응
- [ ] 1-1. threshold-무관 지표(PR-AUC, F2-score) baseline 계산 — Accuracy가
      무의미함을 다시 한번 정량적으로 보여주는 근거자료
- [ ] 1-2. `scale_pos_weight`/`class_weight` 적용 XGBoost 실험
- [ ] 1-3. SMOTE 또는 ADASYN 오버샘플링 적용 실험
- [ ] 1-4. Random/Tomek undersampling 실험
- [ ] 1-5. Phase 0 baseline과 1-2~1-4를 Slip Rate/Volume Reduction/총비용 기준
      동일 표로 비교, 최적 기법 선정

### Phase 2 — Distribution Drift 대응
- [ ] 2-1. 132일을 주 단위(또는 적절한 크기) 윈도우로 분할
- [ ] 2-2. 윈도우 간 feature 분포 변화량 정량화 (PSI 또는 KS-test) → drift가
      실제로 언제·어떤 피처에서 발생하는지 표/그래프로 제시
- [ ] 2-3. 고정 모델(Phase 0 baseline)을 시간에 따라 그대로 적용했을 때 성능이
      실제로 열화되는지 rolling evaluation으로 확인
- [ ] 2-4. drift 대응 전략 1개 이상 구현: (a) sliding-window 재학습 시뮬레이션,
      또는 (b) 최근 데이터에 더 큰 가중치 부여, 또는 (c) ADWIN/DDM류 온라인 drift
      감지기 적용
- [ ] 2-5. 대응 적용 전/후 성능 안정성(시간에 따른 지표 변동폭) 비교

### Phase 3 — 라벨 오류 강건성
- [ ] 3-1. K-fold cross-validation으로 "모델이 강하게 반대하는 라벨" 후보 목록
      추출 (자체 구현 또는 cleanlab 라이브러리 활용)
- [ ] 3-2. 의심 샘플 일부를 직접 들여다보고 정성적으로 타당성 점검 (가능하면
      inspection_feat 패턴이 실제로 애매한지 확인)
- [ ] 3-3. 의심 샘플 제거 후 재학습 vs 그대로 둔 baseline 비교
- [ ] 3-4. (선택) 샘플 가중치 조정 방식으로 "제거" 대신 "완화" 접근도 비교

### Phase 4 — Unsupervised 이상탐지
- [ ] 4-1. False call(정상) 데이터만으로 Isolation Forest / Autoencoder 등
      후보 1~2개 학습
- [ ] 4-2. 이상탐지 스코어 단독으로 Slip Rate/Volume Reduction 평가 (지도학습과
      동일한 평가 파이프라인 재사용)
- [ ] 4-3. 지도학습 모델(XGBoost) 예측 + 이상탐지 스코어 결합 방식 설계 (앙상블
      또는 이상 스코어를 피처로 추가) 후 성능 비교
- [ ] 4-4. (선택) Phase 2에서 만든 drift 탐지에 동일 이상탐지 스코어를 재사용할
      수 있는지 검토 — 확장 항목 간 연결고리로 스토리텔링에 활용

### Phase 5 — 통합 및 발표자료 재구성
- [ ] 5-1. Phase 1~4 중 실제로 유의미한 개선을 보인 항목 선별
- [ ] 5-2. 기존 슬라이드 구조에 "확장된 목표/방법론" 섹션 추가
- [ ] 5-3. 최종 비교표(baseline vs 확장 파이프라인) 작성: Slip Rate, Volume
      Reduction, 총비용, (추가로) drift 안정성, 라벨노이즈 강건성 지표

## 우선순위 제안

전부 동시에 진행하기보다, 스토리텔링과 구현 난이도를 고려하면:

1. **Phase 4 (이상탐지)** — "단순 분류 아님"을 가장 직접적으로 보여주는 스코프
   확장, 구현 난이도 중간
2. **Phase 2 (drift)** — 데이터셋 고유 이슈를 정면으로 다뤄 학술적 설득력이 큼,
   탐지까지만 해도 스코프 확장 효과 있음
3. **Phase 1 (불균형)** — 기존 파이프라인에 이미 일부 있으므로 확장 부담이 가장
   적음, 우선 채워서 빠르게 완료 가능
4. **Phase 3 (라벨노이즈)** — ground truth가 없어 검증이 까다로움 (실제로 틀린
   라벨인지 확인할 방법이 제한적) → 탐색적 실험으로 포지셔닝하고 시간 남으면 진행

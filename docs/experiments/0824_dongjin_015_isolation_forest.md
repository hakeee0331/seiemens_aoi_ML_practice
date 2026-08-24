# 0824_dongjin_015_isolation_forest

## 연결된 노트북

`notebooks/0824_dongjin_015_isolation_forest.ipynb`

## 상태

완료

## 목적

작업자의 라벨 노이즈(오답)가 물리적으로 증명된 상황에서, 불완전한 정답에 의존하는 지도 학습 모델(XGBoost)을 완전히 배제하고 비지도 학습(Unsupervised Learning) 모델인 Isolation Forest를 도입하는 패러다임 전환 가설(Hypothesis 4)을 검증한다.

## 주요 변경사항

- `inspection_type` 별 분리(MoE) 구조는 유지하되, 분류기(Classifier)를 XGBoost에서 `sklearn.ensemble.IsolationForest`로 전면 교체.
- 모델은 Train Set(`X_train_clean`)의 다수 정상 데이터 분포를 학습하며, `decision_function` 점수를 역전산하여 비정상일수록 확률이 높아지도록 정규화(Normalization) 처리 후 성능 평가.

## 평가 방법

Test Set에서 지도 학습(XGBoost)과 동일하게 ROC-AUC 및 PR-AUC를 측정하여 순수 시그널 탐지 능력을 비교한다.

## 주요 결과

- **성능 대폭 하락.**
- Test ROC-AUC: 0.6258
- Test PR-AUC: **0.0361** (XGBoost 챔피언 모델의 0.456 대비 1/10 토막)
- 정규화된 Anomaly Score를 임계값 0.5로 잘랐을 때, TP와 FP 모두 0이 나올 정도로 이상치 점수 분포의 꼬리가 비정상적으로 길게 늘어짐. (즉, 극단적인 이상치 몇 개만 점수가 높고, 실제 불량들은 정상 데이터와 점수대가 겹침).

## 결론 및 인사이트

- Isolation Forest는 "이상치(Anomaly)는 정상 데이터보다 숫자가 적고, 피처 공간상에서 멀리 떨어져 있어 몇 번의 Random Split만으로 쉽게 고립된다"는 가정을 전제로 합니다.
- 하지만 지멘스 AOI 데이터의 불량은 단순히 치수가 크거나 작아서 생기는 '단순 아웃라이어'가 아닙니다. 정상 기판과 거의 똑같은 치수 분포를 가지면서도 미세한 차이(예: 미세 크랙, 0.1mm의 들뜸)로 불량이 되는 경우가 많습니다. 
- 즉, **정상 데이터 군집 한가운데에 숨어있는 악성 불량(Micro-defect)**이 많기 때문에 비지도 학습의 랜덤 공간 분할로는 이들을 전혀 찾아낼 수 없었습니다.
- 반면 XGBoost는 비록 라벨이 일부 오염되어 있더라도, 지도 학습을 통해 그 미세한 경계면(Decision Boundary)을 집요하게 파고들어 분할해냈던 것입니다. (특히 ADASYN의 합성 데이터가 이 경계면을 더욱 탄탄하게 만들어줌).
- 이로써 **불량 탐지에 있어서는 불완전한 라벨일지라도 정제(Cleansing) 후 지도 학습(XGBoost)을 활용하는 것이 비지도 학습보다 압도적으로 우수하다**는 사실이 최종 증명되었습니다.

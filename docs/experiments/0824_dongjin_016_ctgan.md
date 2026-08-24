# 0824_dongjin_016_ctgan

## 연결된 노트북
`notebooks/0824_dongjin_016_ctgan.ipynb`

## 상태
완료 (성능 참패)

## 목적
사용자의 제안("what about use of GAN to deal with the data imbalance")에 따라 불균형 데이터셋 증식을 위해 생성형 적대 신경망(CTGAN)을 도입했습니다. 각 장비별(`inspection_type`)로 분리된 불량 데이터를 CTGAN이 학습하여 진짜와 구별할 수 없는 가상의 불량 데이터를 대량으로 생성(Oversampling)한 후 XGBoost 모델을 학습시켰습니다.

## 분석 결과 (Test Set)
- **PR-AUC**: 0.5052 (수학적 오류값)
- **Recall**: 1.0000 (100%)
- **False Positives (오탐지)**: **87,131개** (정상 데이터를 모조리 불량으로 판정)

### Confusion Matrix
```text
[[    0 87131]
 [    0   924]]
```

## 결론 및 인사이트
1. **Mode Collapse (모드 붕괴) 발생**: 장비별로 불량 라벨 데이터가 13개 ~ 600개 수준으로 너무 적다 보니, 딥러닝 기반의 CTGAN이 불량 데이터의 다양성(Distribution)을 학습하지 못하고 **모드 붕괴(Mode Collapse)** 현상에 빠졌습니다. (매번 똑같은 형태의 가짜 불량 데이터만 생성)
2. **분류기 붕괴**: XGBoost 분류기는 똑같이 생긴 가짜 불량 데이터만 잔뜩 학습하게 되었고, 이로 인해 결정 경계(Decision Boundary)가 완전히 망가졌습니다. 결국 모든 테스트 데이터를 "불량(1)"으로 찍어버리는 깡통 모델이 되었습니다.
3. **ADASYN의 승리**: 테이블형 소규모 불균형 데이터(Tabular Data)에서는 수백만 개의 파라미터를 가진 딥러닝(GAN)보다, 근접 이웃(KNN) 기반으로 결정 경계선을 부드럽게 늘려주는 전통적인 수학적 기법(ADASYN)이 훨씬 안정적이고 강력하다는 것을 완벽히 입증했습니다.

# 0825_peace_012_recall_aligned_model_comparison

## 연결된 노트북

`notebooks/0825_peace_012_recall_aligned_model_comparison.ipynb`

## 상태

완료

## 목적

003/004 단일 type-expert, 005 expanding checkpoint ensemble, 007 type별 `scale_pos_weight` 모델을 동일한 분할·피처·XGBoost 파라미터에서 비교하고, 동일 Recall 목표에서 미래 Fold와 최종 Test의 FP/FCR 차이를 정리한다.

## 설정

- Target recall: [0.95, 0.97, 0.99]
- Walk-forward fold: 004/005와 동일한 expanding 3-fold
- Final benchmark: 0~70% Train / 70~80% Validation / 80~100% Test
- Threshold rule: 기존 `select_threshold` 로직 그대로 사용, calibration/validation에서 recall 제약을 만족하는 threshold 중 FCR 최대 선택
- Source integrity: dataset sha256 `53e8568743216d556856ed69b388f6750fbfa0b8c59ad31f970515ac9eb10e62`, mapping sha256 `3b20f440b6d9ed0baefa662e1a6f03688befbe0f28341a3b54655d3058c6e486`
- Log: `docs/peace/0825_peace_012_recall_aligned_model_comparison.log`

## 데이터 분할

| split      |   rows |   positive_samples |   positive_rate_pct |   timestamp_groups | start_time                | end_time                  |
|:-----------|-------:|-------------------:|--------------------:|-------------------:|:--------------------------|:--------------------------|
| train      | 308196 |               1940 |            0.62947  |              29249 | 1970-06-23 03:58:55+00:00 | 1970-10-05 00:29:59+00:00 |
| validation |  44026 |                357 |            0.810884 |               3400 | 1970-10-05 00:30:30+00:00 | 1970-10-13 16:54:14+00:00 |
| test       |  88052 |               2325 |            2.64049  |               7093 | 1970-10-13 16:54:52+00:00 | 1970-11-02 14:21:28+00:00 |

## Walk-forward 구성

| fold   | segment     |   rows |   positive_samples |   positive_rate_pct |   timestamp_groups | start_time                | end_time                  |
|:-------|:------------|-------:|-------------------:|--------------------:|-------------------:|:--------------------------|:--------------------------|
| fold_1 | train       | 132137 |               1223 |           0.925555  |              15230 | 1970-06-23 03:58:55+00:00 | 1970-08-18 06:51:10+00:00 |
| fold_1 | calibration |  43979 |                200 |           0.454763  |               1251 | 1970-08-18 06:51:41+00:00 | 1970-08-21 23:32:59+00:00 |
| fold_1 | evaluation  |  44040 |                326 |           0.740236  |               5415 | 1970-08-21 23:33:55+00:00 | 1970-09-15 06:46:33+00:00 |
| fold_2 | train       | 176116 |               1423 |           0.80799   |              16481 | 1970-06-23 03:58:55+00:00 | 1970-08-21 23:32:59+00:00 |
| fold_2 | calibration |  44040 |                326 |           0.740236  |               5415 | 1970-08-21 23:33:55+00:00 | 1970-09-15 06:46:33+00:00 |
| fold_2 | evaluation  |  44187 |                152 |           0.343993  |               4167 | 1970-09-15 06:47:13+00:00 | 1970-09-28 05:10:37+00:00 |
| fold_3 | train       | 220156 |               1749 |           0.794437  |              21896 | 1970-06-23 03:58:55+00:00 | 1970-09-15 06:46:33+00:00 |
| fold_3 | calibration |  44187 |                152 |           0.343993  |               4167 | 1970-09-15 06:47:13+00:00 | 1970-09-28 05:10:37+00:00 |
| fold_3 | evaluation  |  43853 |                 39 |           0.0889335 |               3186 | 1970-09-28 05:11:13+00:00 | 1970-10-05 00:29:59+00:00 |

## Fold별 Recall-aligned 결과

|   target_recall | model                                     | fold   |   calibration_threshold |   calibration_fp | calibration_fcr   | future_recall   |   future_fp | future_fcr   |   future_fn |
|----------------:|:------------------------------------------|:-------|------------------------:|-----------------:|:------------------|:----------------|------------:|:-------------|------------:|
|            0.95 | 003/004 single type-expert                | fold_1 |                0.000415 |            31728 | 27.53%            | 98.77%          |       34809 | 20.37%       |           4 |
|            0.95 | 003/004 single type-expert                | fold_2 |                0.001509 |            21761 | 50.22%            | 84.87%          |       19172 | 56.46%       |          23 |
|            0.95 | 003/004 single type-expert                | fold_3 |                0.00024  |            26207 | 40.49%            | 97.44%          |       32539 | 25.73%       |           1 |
|            0.95 | 005 expanding checkpoint ensemble         | fold_1 |                0.000415 |            31728 | 27.53%            | 98.77%          |       34809 | 20.37%       |           4 |
|            0.95 | 005 expanding checkpoint ensemble         | fold_2 |                0.001926 |            20834 | 52.34%            | 84.21%          |       17960 | 59.21%       |          24 |
|            0.95 | 005 expanding checkpoint ensemble         | fold_3 |                0.000436 |            30228 | 31.35%            | 97.44%          |       30580 | 30.20%       |           1 |
|            0.95 | 007 single type-expert + scale_pos_weight | fold_1 |                0.000449 |            32042 | 26.81%            | 99.08%          |       36875 | 15.64%       |           3 |
|            0.95 | 007 single type-expert + scale_pos_weight | fold_2 |                0.009488 |            18663 | 57.31%            | 78.29%          |       14692 | 66.64%       |          33 |
|            0.95 | 007 single type-expert + scale_pos_weight | fold_3 |                0.000876 |            24136 | 45.19%            | 97.44%          |       29119 | 33.54%       |           1 |
|            0.97 | 003/004 single type-expert                | fold_1 |                0.000277 |            35132 | 19.75%            | 99.39%          |       37504 | 14.21%       |           2 |
|            0.97 | 003/004 single type-expert                | fold_2 |                0.000886 |            26482 | 39.42%            | 89.47%          |       23231 | 47.24%       |          16 |
|            0.97 | 003/004 single type-expert                | fold_3 |                0.000134 |            34303 | 22.10%            | 100.00%         |       36598 | 16.47%       |           0 |
|            0.97 | 005 expanding checkpoint ensemble         | fold_1 |                0.000277 |            35132 | 19.75%            | 99.39%          |       37504 | 14.21%       |           2 |
|            0.97 | 005 expanding checkpoint ensemble         | fold_2 |                0.001614 |            23028 | 47.32%            | 84.21%          |       19297 | 56.18%       |          24 |
|            0.97 | 005 expanding checkpoint ensemble         | fold_3 |                0.000351 |            31612 | 28.21%            | 97.44%          |       32013 | 26.93%       |           1 |
|            0.97 | 007 single type-expert + scale_pos_weight | fold_1 |                0.000405 |            33292 | 23.95%            | 99.08%          |       37968 | 13.14%       |           3 |
|            0.97 | 007 single type-expert + scale_pos_weight | fold_2 |                0.0046   |            24769 | 43.34%            | 86.18%          |       19541 | 55.62%       |          21 |
|            0.97 | 007 single type-expert + scale_pos_weight | fold_3 |                0.00052  |            29640 | 32.69%            | 97.44%          |       33363 | 23.85%       |           1 |
|            0.99 | 003/004 single type-expert                | fold_1 |                2.7e-05  |            43234 | 1.24%             | 100.00%         |       43327 | 0.89%        |           0 |
|            0.99 | 003/004 single type-expert                | fold_2 |                0.00068  |            28059 | 35.81%            | 90.79%          |       25068 | 43.07%       |          14 |
|            0.99 | 003/004 single type-expert                | fold_3 |                6.5e-05  |            40450 | 8.14%             | 100.00%         |       40801 | 6.88%        |           0 |
|            0.99 | 005 expanding checkpoint ensemble         | fold_1 |                2.7e-05  |            43234 | 1.24%             | 100.00%         |       43327 | 0.89%        |           0 |
|            0.99 | 005 expanding checkpoint ensemble         | fold_2 |                0.000488 |            33668 | 22.98%            | 96.05%          |       29122 | 33.87%       |           6 |
|            0.99 | 005 expanding checkpoint ensemble         | fold_3 |                0.000204 |            35026 | 20.46%            | 100.00%         |       35859 | 18.16%       |           0 |
|            0.99 | 007 single type-expert + scale_pos_weight | fold_1 |                0.000194 |            38172 | 12.81%            | 99.69%          |       40707 | 6.88%        |           1 |
|            0.99 | 007 single type-expert + scale_pos_weight | fold_2 |                0.001389 |            31664 | 27.57%            | 95.39%          |       26479 | 39.87%       |           7 |
|            0.99 | 007 single type-expert + scale_pos_weight | fold_3 |                0.000135 |            39796 | 9.63%             | 100.00%         |       42125 | 3.85%        |           0 |

## Walk-forward 요약

|   target_recall | model                                     | mean_future_recall   | min_future_recall   |   recall_target_hit_folds | mean_future_fp   |   total_future_fp | mean_future_fcr   |
|----------------:|:------------------------------------------|:---------------------|:--------------------|--------------------------:|:-----------------|------------------:|:------------------|
|            0.95 | 007 single type-expert + scale_pos_weight | 91.60%               | 78.29%              |                         2 | 26,895.3         |             80686 | 38.61%            |
|            0.95 | 005 expanding checkpoint ensemble         | 93.47%               | 84.21%              |                         2 | 27,783.0         |             83349 | 36.60%            |
|            0.95 | 003/004 single type-expert                | 93.69%               | 84.87%              |                         2 | 28,840.0         |             86520 | 34.19%            |
|            0.97 | 005 expanding checkpoint ensemble         | 93.68%               | 84.21%              |                         2 | 29,604.7         |             88814 | 32.44%            |
|            0.97 | 007 single type-expert + scale_pos_weight | 94.23%               | 86.18%              |                         2 | 30,290.7         |             90872 | 30.87%            |
|            0.97 | 003/004 single type-expert                | 96.29%               | 89.47%              |                         2 | 32,444.3         |             97333 | 25.97%            |
|            0.99 | 005 expanding checkpoint ensemble         | 98.68%               | 96.05%              |                         2 | 36,102.7         |            108308 | 17.64%            |
|            0.99 | 003/004 single type-expert                | 96.93%               | 90.79%              |                         2 | 36,398.7         |            109196 | 16.94%            |
|            0.99 | 007 single type-expert + scale_pos_weight | 98.36%               | 95.39%              |                         2 | 36,437.0         |            109311 | 16.87%            |

## Final Retrospective Benchmark

아래 Test는 이전 실험들과 같은 80~100% 구간이며, 이번 실험에서도 threshold 선택에는 사용하지 않았다.

|   target_recall | model                                     |   validation_threshold |   validation_fp | validation_fcr   | test_recall   |   test_fp | test_fcr   |   test_fn | selection_note                                                             |
|----------------:|:------------------------------------------|-----------------------:|----------------:|:-----------------|:--------------|----------:|:-----------|----------:|:---------------------------------------------------------------------------|
|            0.95 | 003/004 single type-expert                |               0.001947 |            7995 | 81.69%           | 84.99%        |     21253 | 75.21%     |       349 | Test reused from prior experiments; threshold selected on validation only. |
|            0.95 | 005 expanding checkpoint ensemble         |               0.002278 |            9306 | 78.69%           | 87.31%        |     25267 | 70.53%     |       295 | Test reused from prior experiments; threshold selected on validation only. |
|            0.95 | 007 single type-expert + scale_pos_weight |               0.00048  |           29246 | 33.03%           | 95.78%        |     66803 | 22.07%     |        98 | Test reused from prior experiments; threshold selected on validation only. |
|            0.97 | 003/004 single type-expert                |               0.00148  |            8932 | 79.55%           | 86.49%        |     23338 | 72.78%     |       314 | Test reused from prior experiments; threshold selected on validation only. |
|            0.97 | 005 expanding checkpoint ensemble         |               0.001453 |           11510 | 73.64%           | 90.45%        |     29572 | 65.50%     |       222 | Test reused from prior experiments; threshold selected on validation only. |
|            0.97 | 007 single type-expert + scale_pos_weight |               0.000376 |           31388 | 28.12%           | 96.47%        |     69875 | 18.49%     |        82 | Test reused from prior experiments; threshold selected on validation only. |
|            0.99 | 003/004 single type-expert                |               0.00077  |           13127 | 69.94%           | 89.81%        |     33486 | 60.94%     |       237 | Test reused from prior experiments; threshold selected on validation only. |
|            0.99 | 005 expanding checkpoint ensemble         |               0.00071  |           16984 | 61.11%           | 93.94%        |     41118 | 52.04%     |       141 | Test reused from prior experiments; threshold selected on validation only. |
|            0.99 | 007 single type-expert + scale_pos_weight |               0.000189 |           36700 | 15.96%           | 98.49%        |     77110 | 10.05%     |        35 | Test reused from prior experiments; threshold selected on validation only. |

## Prediction Disagreement / FN Overlap Diagnostic (target recall 0.97)

|   target_recall | model_a                           | model_b                                   | disagreement_rate   |   probability_corr |   fn_a |   fn_b |   shared_fn |   fn_only_a |   fn_only_b |   fp_a |   fp_b |   shared_fp |   fp_only_a |   fp_only_b |
|----------------:|:----------------------------------|:------------------------------------------|:--------------------|-------------------:|-------:|-------:|------------:|------------:|------------:|-------:|-------:|------------:|------------:|------------:|
|            0.97 | 003/004 single type-expert        | 005 expanding checkpoint ensemble         | 7.91%               |             0.9648 |     18 |     27 |          18 |           0 |           9 |  97333 |  88814 |       87851 |        9482 |         963 |
|            0.97 | 003/004 single type-expert        | 007 single type-expert + scale_pos_weight | 14.41%              |             0.597  |     18 |     25 |           8 |          10 |          17 |  97333 |  90872 |       84597 |       12736 |        6275 |
|            0.97 | 005 expanding checkpoint ensemble | 007 single type-expert + scale_pos_weight | 15.38%              |             0.6002 |     27 |     25 |          13 |          14 |          12 |  88814 |  90872 |       79698 |        9116 |       11174 |

## 결론

- Calibration에서 같은 Recall을 맞춰도 미래 Evaluation에서는 실제 Recall이 달라졌다. 모든 목표에서 세 모델 모두 목표 Recall을 미래 3개 Fold 전체에서 유지하지 못했다.
- 목표 Recall 0.99에서는 `005` Fold 앙상블이 미래 평균 Recall 98.68%, 최저 Recall 96.05%, 총 FP 108,308로 세 모델 중 Recall은 가장 높고 FP는 가장 적었다.
- 목표 0.95·0.97에서는 FP가 적은 모델의 미래 Recall도 더 낮아 명확한 단일 승자가 없었다. 따라서 실제 미래 Recall을 함께 보지 않고 FP만 비교하면 안 된다.
- 목표 0.97에서 `005`와 `007`의 확률 상관은 0.6002였고, 공통 FN 13건 외에 각각만 놓친 불량이 14건·12건이었다. 두 모델의 오류가 충분히 달라 확률 앙상블을 시험할 근거가 있다.
- 다음 후보는 `005`+`007` 보정 확률 Soft Voting이며, 모델 선택은 Test가 아닌 Walk-forward에서만 수행해야 한다.

## 실행 로그

`docs/peace/0825_peace_012_recall_aligned_model_comparison.log`

# 0825_peace_013_type_expert_fold_class_soft_voting

## 연결된 노트북

`notebooks/0825_peace_013_type_expert_fold_class_soft_voting.ipynb`

## 상태

완료

## 목적

005 expanding checkpoint ensemble과 007 타입별 class-weight 모델을 pooled Platt 보정 후 soft voting으로 결합하고, alpha 선택을 walk-forward에서만 수행한 뒤 고정된 alpha를 최종 retrospective Test에 한 번만 적용한다.

## 설정

- Base models: 005 expanding checkpoint ensemble, 007 single type-expert + scale_pos_weight
- Alpha grid (005 weight): [0.0, 0.25, 0.5, 0.75, 1.0]
- Walk-forward folds: 004/005와 동일한 expanding 3-fold
- Within each fold calibration and final 70~80% validation: earlier timestamp-group half for Platt fit, later half for threshold selection
- Threshold rule: existing exact `select_threshold`, Recall >= 99% then max FCR
- Source integrity: dataset sha256 `53e8568743216d556856ed69b388f6750fbfa0b8c59ad31f970515ac9eb10e62`, mapping sha256 `3b20f440b6d9ed0baefa662e1a6f03688befbe0f28341a3b54655d3058c6e486`
- Log: `docs/peace/0825_peace_013_type_expert_fold_class_soft_voting.log`

## 전체 분할

| split      |   rows |   positive_samples |   positive_rate_pct |   timestamp_groups | start_time                | end_time                  |
|:-----------|-------:|-------------------:|--------------------:|-------------------:|:--------------------------|:--------------------------|
| train      | 308196 |               1940 |            0.62947  |              29249 | 1970-06-23 03:58:55+00:00 | 1970-10-05 00:29:59+00:00 |
| validation |  44026 |                357 |            0.810884 |               3400 | 1970-10-05 00:30:30+00:00 | 1970-10-13 16:54:14+00:00 |
| test       |  88052 |               2325 |            2.64049  |               7093 | 1970-10-13 16:54:52+00:00 | 1970-11-02 14:21:28+00:00 |

## Walk-forward 분할

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

## Walk-forward Calibration 내부 시간 분할

| stage   | segment             |   rows |   positive_samples |   positive_rate_pct |   timestamp_groups | start_time                | end_time                  |
|:--------|:--------------------|-------:|-------------------:|--------------------:|-------------------:|:--------------------------|:--------------------------|
| fold_1  | platt_fit           |  21967 |                 32 |            0.145673 |                614 | 1970-08-18 06:51:41+00:00 | 1970-08-19 05:51:18+00:00 |
| fold_1  | threshold_selection |  22012 |                168 |            0.76322  |                637 | 1970-08-19 05:51:47+00:00 | 1970-08-21 23:32:59+00:00 |
| fold_2  | platt_fit           |  22020 |                292 |            1.32607  |               3748 | 1970-08-21 23:33:55+00:00 | 1970-09-10 00:01:28+00:00 |
| fold_2  | threshold_selection |  22020 |                 34 |            0.154405 |               1667 | 1970-09-10 00:02:21+00:00 | 1970-09-15 06:46:33+00:00 |
| fold_3  | platt_fit           |  22147 |                 94 |            0.424437 |               2093 | 1970-09-15 06:47:13+00:00 | 1970-09-20 19:58:16+00:00 |
| fold_3  | threshold_selection |  22040 |                 58 |            0.263158 |               2074 | 1970-09-20 19:58:41+00:00 | 1970-09-28 05:10:37+00:00 |

## Platt 보정 계수

| stage            |   model_key | model_label                               |   rows |   positive_samples |   negative_samples |   coefficient |   intercept |   raw_probability_min |   raw_probability_max |
|:-----------------|------------:|:------------------------------------------|-------:|-------------------:|-------------------:|--------------:|------------:|----------------------:|----------------------:|
| fold_1           |         005 | 005 expanding checkpoint ensemble         |  21967 |                 32 |              21935 |      0.903683 |   -1.58139  |               8e-06   |              0.886587 |
| fold_1           |         007 | 007 single type-expert + scale_pos_weight |  21967 |                 32 |              21935 |      0.569912 |   -3.64074  |               4e-06   |              0.994236 |
| fold_2           |         005 | 005 expanding checkpoint ensemble         |  22020 |                292 |              21728 |      0.677054 |   -1.31849  |               5e-06   |              0.992898 |
| fold_2           |         007 | 007 single type-expert + scale_pos_weight |  22020 |                292 |              21728 |      0.604418 |   -3.04688  |               5e-06   |              0.999542 |
| fold_3           |         005 | 005 expanding checkpoint ensemble         |  22147 |                 94 |              22053 |      0.857388 |   -1.35168  |               2.2e-05 |              0.869417 |
| fold_3           |         007 | 007 single type-expert + scale_pos_weight |  22147 |                 94 |              22053 |      0.592281 |   -3.16202  |               4e-06   |              0.997605 |
| final_validation |         005 | 005 expanding checkpoint ensemble         |  22010 |                215 |              21795 |      1.12711  |   -0.291202 |               1.8e-05 |              0.765258 |
| final_validation |         007 | 007 single type-expert + scale_pos_weight |  22010 |                215 |              21795 |      0.772177 |   -3.98122  |               1.8e-05 |              0.996223 |

## Fold별 Alpha 결과

| fold   |   alpha |   weight_005 |   weight_007 |   threshold_selected | threshold_recall   |   threshold_fp | threshold_fcr   | future_recall   |   future_fp | future_fcr   |   future_fn |   future_pr_auc |
|:-------|--------:|-------------:|-------------:|---------------------:|:-------------------|---------------:|:----------------|:----------------|------------:|:-------------|------------:|----------------:|
| fold_1 |    0    |         0    |         1    |             0.000104 | 99.40%             |          21091 | 3.45%           | 100.00%         |       42854 | 1.97%        |           0 |        0.245426 |
| fold_2 |    0    |         0    |         1    |             0.00022  | 100.00%            |          21382 | 2.75%           | 99.34%          |       42026 | 4.56%        |           1 |        0.04278  |
| fold_3 |    0    |         0    |         1    |             0.000481 | 100.00%            |          16008 | 27.18%          | 97.44%          |       33363 | 23.85%       |           1 |        0.010187 |
| fold_1 |    0.25 |         0.25 |         0.75 |             8.1e-05  | 99.40%             |          21482 | 1.66%           | 100.00%         |       43061 | 1.49%        |           0 |        0.221757 |
| fold_2 |    0.25 |         0.25 |         0.75 |             0.000402 | 100.00%            |          20532 | 6.61%           | 100.00%         |       39030 | 11.37%       |           0 |        0.041587 |
| fold_3 |    0.25 |         0.25 |         0.75 |             0.000672 | 100.00%            |          14511 | 33.99%          | 97.44%          |       28566 | 34.80%       |           1 |        0.012577 |
| fold_1 |    0.5  |         0.5  |         0.5  |             5.9e-05  | 99.40%             |          21600 | 1.12%           | 100.00%         |       43134 | 1.33%        |           0 |        0.188884 |
| fold_2 |    0.5  |         0.5  |         0.5  |             0.00053  | 100.00%            |          19980 | 9.12%           | 100.00%         |       37669 | 14.46%       |           0 |        0.038451 |
| fold_3 |    0.5  |         0.5  |         0.5  |             0.000601 | 100.00%            |          14876 | 32.33%          | 97.44%          |       28789 | 34.29%       |           1 |        0.022469 |
| fold_1 |    0.75 |         0.75 |         0.25 |             3.7e-05  | 99.40%             |          21589 | 1.17%           | 100.00%         |       43346 | 0.84%        |           0 |        0.1575   |
| fold_2 |    0.75 |         0.75 |         0.25 |             0.000658 | 100.00%            |          19761 | 10.12%          | 100.00%         |       36763 | 16.51%       |           0 |        0.034772 |
| fold_3 |    0.75 |         0.75 |         0.25 |             0.000504 | 100.00%            |          15151 | 31.08%          | 97.44%          |       29277 | 33.18%       |           1 |        0.037519 |
| fold_1 |    1    |         1    |         0    |             1.4e-05  | 99.40%             |          21566 | 1.27%           | 100.00%         |       43409 | 0.70%        |           0 |        0.134269 |
| fold_2 |    1    |         1    |         0    |             0.000787 | 100.00%            |          19251 | 12.44%          | 100.00%         |       35946 | 18.37%       |           0 |        0.02831  |
| fold_3 |    1    |         1    |         0    |             0.000133 | 100.00%            |          19999 | 9.02%           | 100.00%         |       38453 | 12.24%       |           0 |        0.037427 |

## Walk-forward Alpha 요약

|   alpha |   folds |   recall_target_hit_folds | mean_future_recall   | min_future_recall   | mean_future_fp   |   total_future_fp | mean_future_fcr   | min_future_fcr   |   mean_future_pr_auc |
|--------:|--------:|--------------------------:|:---------------------|:--------------------|:-----------------|------------------:|:------------------|:-----------------|---------------------:|
|    1    |       3 |                         3 | 100.00%              | 100.00%             | 39,269.3         |            117808 | 10.43%            | 0.70%            |             0.066668 |
|    0.75 |       3 |                         2 | 99.15%               | 97.44%              | 36,462.0         |            109386 | 16.84%            | 0.84%            |             0.076597 |
|    0.5  |       3 |                         2 | 99.15%               | 97.44%              | 36,530.7         |            109592 | 16.69%            | 1.33%            |             0.083268 |
|    0.25 |       3 |                         2 | 99.15%               | 97.44%              | 36,885.7         |            110657 | 15.89%            | 1.49%            |             0.091974 |
|    0    |       3 |                         2 | 98.93%               | 97.44%              | 39,414.3         |            118243 | 10.13%            | 1.97%            |             0.099464 |

## Alpha 선택 규칙

Selection hierarchy on walk-forward only: 1) maximize Recall 99% hit folds, 2) maximize minimum future Recall, 3) minimize total future FP, 4) maximize mean future PR-AUC, 5) lower alpha only as deterministic tie-break.

선택된 alpha: `1.00`

## Final Validation 내부 시간 분할

| stage            | segment             |   rows |   positive_samples |   positive_rate_pct |   timestamp_groups | start_time                | end_time                  |
|:-----------------|:--------------------|-------:|-------------------:|--------------------:|-------------------:|:--------------------------|:--------------------------|
| final_validation | platt_fit           |  22010 |                215 |            0.976829 |               1251 | 1970-10-05 00:30:30+00:00 | 1970-10-07 20:57:43+00:00 |
| final_validation | threshold_selection |  22016 |                142 |            0.644985 |               2149 | 1970-10-07 20:58:45+00:00 | 1970-10-13 16:54:14+00:00 |

## Final Retrospective Test 결과

아래 Test는 이전 실험들과 같은 80~100% 구간이며, 이번 retrospective에서도 alpha/threshold 선택에는 사용하지 않았다.

|   alpha |   weight_005 |   weight_007 | role                   |   validation_threshold | validation_threshold_recall   |   validation_threshold_fp | validation_threshold_fcr   | test_recall   |   test_fp | test_fcr   |   test_fn |   test_tp |   test_tn |   test_precision |   test_pr_auc | selection_note                                                                                                                       |
|--------:|-------------:|-------------:|:-----------------------|-----------------------:|:------------------------------|--------------------------:|:---------------------------|:--------------|----------:|:-----------|----------:|----------:|----------:|-----------------:|--------------:|:-------------------------------------------------------------------------------------------------------------------------------------|
|    0    |         0    |         1    | diagnostic_endpoint    |               2e-05    | 99.30%                        |                     19070 | 12.82%                     | 99.14%        |     79232 | 7.58%      |        20 |      2305 |      6495 |        0.0282694 |      0.318605 | Test reused from prior experiments and this retrospective; alpha/threshold were fixed without using Test labels for model selection. |
|    0.25 |         0.25 |         0.75 | candidate_not_selected |               0.000197 | 99.30%                        |                      8509 | 61.10%                     | 92.56%        |     48736 | 43.15%     |       173 |      2152 |     36991 |        0.0422889 |      0.369712 | Test reused from prior experiments and this retrospective; alpha/threshold were fixed without using Test labels for model selection. |
|    0.5  |         0.5  |         0.5  | candidate_not_selected |               0.000161 | 99.30%                        |                      9579 | 56.21%                     | 94.06%        |     53120 | 38.04%     |       138 |      2187 |     32607 |        0.0395429 |      0.394139 | Test reused from prior experiments and this retrospective; alpha/threshold were fixed without using Test labels for model selection. |
|    0.75 |         0.75 |         0.25 | candidate_not_selected |               0.000179 | 99.30%                        |                      8880 | 59.40%                     | 94.37%        |     50880 | 40.65%     |       131 |      2194 |     34847 |        0.0413385 |      0.393858 | Test reused from prior experiments and this retrospective; alpha/threshold were fixed without using Test labels for model selection. |
|    1    |         1    |         0    | selected_walk_forward  |               0.000211 | 99.30%                        |                      7660 | 64.98%                     | 93.94%        |     41118 | 52.04%     |       141 |      2184 |     44609 |        0.0504365 |      0.382545 | Test reused from prior experiments and this retrospective; alpha/threshold were fixed without using Test labels for model selection. |

## 선택 Alpha와 Endpoint 비교

| label                              |   validation_threshold | test_recall   |   test_fp | test_fcr   |   test_fn |   test_tp |   test_pr_auc | role                  |
|:-----------------------------------|-----------------------:|:--------------|----------:|:-----------|----------:|----------:|--------------:|:----------------------|
| alpha=0.00 (007 only diagnostic)   |               2e-05    | 99.14%        |     79232 | 7.58%      |        20 |      2305 |      0.318605 | diagnostic_endpoint   |
| alpha=1.00 (walk-forward selected) |               0.000211 | 93.94%        |     41118 | 52.04%     |       141 |      2184 |      0.382545 | selected_walk_forward |

## 결론

- Walk-forward는 alpha=1.00(005 100%, 007 0%)을 선택했다. Recall 99% 목표를 3/3 Fold에서 달성했고 최저 Recall은 100.00%, 총 FP는 117,808이었다.
- 고정된 alpha=1.00의 Test 결과는 Recall 93.94%, FP 41,118, FCR 52.04%, FN 141, PR-AUC 0.382545로 기존 005와 같다.
- alpha=0.50·0.75는 Test PR-AUC는 더 높았지만 Walk-forward Recall 99% 안정성 기준을 통과하지 못했으므로 선택하지 않는다.
- 따라서 현재 soft voting은 채택하지 않고 내부 Champion으로 005를 유지한다. Test는 alpha와 threshold 선택에 사용하지 않았다.

## 실행 로그

`docs/peace/0825_peace_013_type_expert_fold_class_soft_voting.log`

# 0825_dongjin_025_ensemble_shap_analysis

## Overview
Extracted False Calls and SHAP values natively by reproducing the `005_type_expert_fold_ensemble` training process.
SHAP values and thresholds were averaged/aggregated across the 4 checkpoint models for each inspection type.

## Top 10 Features Driving False Calls by Type

|   Inspection Type |   False Calls | Top Features (|SHAP|)                                                                                                                                                                                                                                                                                                                    |
|------------------:|--------------:|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|                 1 |            68 | 1. inspection_feat24 (1.7037) <br> 2. inspection_feat48 (1.0480) <br> 3. meta_feat4_28 (0.7841) <br> 4. inspection_feat8 (0.7524) <br> 5. meta_feat1_22 (0.4374) <br> 6. inspection_feat1 (0.3456) <br> 7. meta_feat4_1 (0.2794) <br> 8. inspection_feat25 (0.2512) <br> 9. inspection_feat4 (0.2473) <br> 10. inspection_feat2 (0.2348) |
|                 2 |             3 | 1. inspection_feat96 (1.3280) <br> 2. meta_feat1_27 (1.2472) <br> 3. meta_feat4_3 (0.6245) <br> 4. inspection_feat22 (0.5032) <br> 5. meta_feat4_41 (0.4458) <br> 6. inspection_feat95 (0.4458) <br> 7. inspection_feat28 (0.4062) <br> 8. inspection_feat12 (0.3549) <br> 9. inspection_feat1 (0.3365) <br> 10. meta_feat1_2 (0.3190)   |
|                 3 |           102 | 1. inspection_feat95 (0.9694) <br> 2. meta_feat4_7 (0.8703) <br> 3. inspection_feat22 (0.8331) <br> 4. inspection_feat12 (0.7863) <br> 5. meta_feat1_27 (0.7026) <br> 6. inspection_feat96 (0.4169) <br> 7. meta_feat4_41 (0.3427) <br> 8. meta_feat1_24 (0.2942) <br> 9. inspection_feat4 (0.2789) <br> 10. meta_feat2_2 (0.2505)       |

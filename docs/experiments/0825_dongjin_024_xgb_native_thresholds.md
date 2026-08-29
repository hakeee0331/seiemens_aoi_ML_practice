# Experiment: 0825_dongjin_024_xgb_native_thresholds

**Date:** 2024-08-25  
**Author:** Dongjin  
**Status:** Completed  
**Type:** Feature Importance & Threshold Analysis  
**Base Model:** `0824_kimjaehak_005_xgboost_baseline.pkl`

## Objective
Extract the exact mathematical threshold boundaries that the XGBoost model learned for the top features contributing to False Calls (False Positives), grouped **by inspection type**.

Instead of training a surrogate `RuleFit` model (which trains a new linear combination of trees on top of predictions), this approach extracts the native rules directly from the XGBoost model's internal decision trees by using `model.get_booster().trees_to_dataframe()`. This guarantees 100% fidelity to the model's actual decision boundaries, while segmenting the analysis by `inspection_type` to account for the physical differences in what features mean across different inspections.

## Methodology
1. **Data Split**: Reproduced the 60/20/20 time-based split from the baseline `005` experiment.
2. **Isolate False Calls**: Filtered the test set to only instances where `class == 0` (True Negative) but the model predicted `1` (False Positive).
3. **Partition by Inspection Type**: Grouped the False Calls by their respective `inspection_type`.
4. **SHAP Analysis (Per Type)**: Applied `shap.TreeExplainer` on the False Calls for each inspection type to determine which features had the highest mean absolute SHAP values (i.e., driving the false positive prediction for that specific type).
5. **Extract Tree Thresholds (Per Type)**: Extracted all internal tree splits from the XGBoost booster. For the Top 10 features identified by SHAP per type, we grouped all internal node splits for that feature, counted the frequency, and summed the `Cover` (number of samples passing through the node) to find the most influential native split thresholds.

## Conclusion & Dashboard Application
By combining SHAP with native threshold extraction, we bypass the need for surrogate models like RuleFit. By doing this per inspection type, we respect the physical meaning of the features.
For the line worker dashboard, when a false call occurs for a given inspection type, the UI can immediately check these specific thresholds to provide actionable, mathematically precise insights.

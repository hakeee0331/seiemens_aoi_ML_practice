import nbformat as nbf

nb = nbf.v4.new_notebook()

nb.cells.append(nbf.v4.new_markdown_cell("""# 0826_dongjin_027_global_ensemble_shap

This notebook performs Global SHAP analysis natively on the **saved** `0825_peace_005_type_expert_fold_ensemble.pkl` model bundle.
Instead of filtering only False Calls, we compute SHAP values over the **entire Test Set** for each inspection type.
This allows us to identify the most dominant features the model relies on to separate `class = 0` (False Calls/Negatives) from `class = 1` (True Defects).

For each inspection type:
1. We compute SHAP values for the entire test set.
2. We aggregate Mean |SHAP| across all 4 checkpoint models.
3. We extract decision boundaries for the globally dominant features.
"""))

nb.cells.append(nbf.v4.new_code_cell("""import gc
import json
import pickle
from pathlib import Path
import pandas as pd
import numpy as np
import shap
import xgboost
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

# Configuration
DATA_PATH = Path("../data/raw/dataset.csv")
MAPPING_PATH = Path("../data/raw/mapping.json")
MODEL_BUNDLE_PATH = Path("../models/0825_peace_005_type_expert_fold_ensemble.pkl")
TARGET = "class"
TIME_COLUMN = "timestamp"
TYPE_COLUMN = "inspection_type"
RECORD_ID = "record_id"
"""))

nb.cells.append(nbf.v4.new_markdown_cell("""## 1. Load Data, Mapping, and Model Bundle"""))

nb.cells.append(nbf.v4.new_code_cell("""# Load Model Bundle
with open(MODEL_BUNDLE_PATH, 'rb') as f:
    bundle = pickle.load(f)

inspection_types = bundle['inspection_types']
feature_columns_by_type = bundle['feature_columns_by_type']
checkpoints = bundle['ensemble_checkpoints']

# Load Data
raw_df = pd.read_csv(DATA_PATH, low_memory=False)
if raw_df.columns[0].startswith("Unnamed:") or raw_df.columns[0] == "":
    raw_df = raw_df.rename(columns={raw_df.columns[0]: RECORD_ID})

raw_df[TIME_COLUMN] = pd.to_datetime(raw_df[TIME_COLUMN], errors="raise", utc=True)
raw_df = raw_df.sort_values([TIME_COLUMN, RECORD_ID], kind="stable").reset_index(drop=True)

meta_columns = [col for col in raw_df.columns if col.startswith("meta_feat")]

print("Model and Data loaded. Types:", inspection_types)
"""))

nb.cells.append(nbf.v4.new_markdown_cell("""## 2. Test Set Split"""))

nb.cells.append(nbf.v4.new_code_cell("""timestamp_group_sizes = raw_df.groupby(TIME_COLUMN, sort=True).size()
cumulative_rows = timestamp_group_sizes.cumsum().to_numpy()
timestamp_index = timestamp_group_sizes.index

def boundary_at(fraction: float):
    position = int(np.searchsorted(cumulative_rows, len(raw_df) * fraction, side="left"))
    return timestamp_index[position]

validation_end_time = boundary_at(0.80)
test_mask = raw_df[TIME_COLUMN] > validation_end_time
test_df = raw_df.loc[test_mask].copy()

print(f"Test Set Size: {len(test_df)}")
"""))

nb.cells.append(nbf.v4.new_markdown_cell("""## 3. Extract Global SHAP per Type"""))

nb.cells.append(nbf.v4.new_code_cell("""final_summary_rows = []

for inspection_type in inspection_types:
    print("=" * 80)
    print(f"INSPECTION TYPE: {inspection_type}")
    print("=" * 80)
    
    feature_columns = feature_columns_by_type[inspection_type]
    type_test = test_df.loc[test_df[TYPE_COLUMN] == inspection_type]
    y_test_type = type_test[TARGET].astype("int8")
    
    if len(type_test) == 0:
        continue
        
    X_type_raw = type_test[feature_columns]
    
    print(f"\\n  Total Samples (Test Set): {len(X_type_raw)}")
    print(f"  Negatives (class=0): {(y_test_type == 0).sum()}")
    print(f"  Positives (class=1): {(y_test_type == 1).sum()}\\n")
        
    # SHAP Analysis
    feature_abs_shap_sum = {}
    all_trees = []
    
    for ckpt in checkpoints:
        model_info = bundle['members'][ckpt][inspection_type]
        model = model_info['model']
        preprocessor = model_info['preprocessor']
        encoded_feature_names = preprocessor.get_feature_names_out()
        
        X_type_encoded = preprocessor.transform(X_type_raw)
        if hasattr(X_type_encoded, "toarray"):
            X_type_encoded = X_type_encoded.toarray()
            
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_type_encoded)
        
        # Mean absolute SHAP for this checkpoint across ALL test samples
        mean_abs_shap_ckpt = np.abs(shap_values).mean(axis=0)
        
        for name, val in zip(encoded_feature_names, mean_abs_shap_ckpt):
            feature_abs_shap_sum[name] = feature_abs_shap_sum.get(name, 0.0) + val
            
        # Thresholds
        trees_df = model.get_booster().trees_to_dataframe()
        feature_map = {f"f{i}": name for i, name in enumerate(encoded_feature_names)}
        trees_df['FeatureName'] = trees_df['Feature'].map(feature_map)
        all_trees.append(trees_df)
        
    # Average across the 4 checkpoints
    for name in feature_abs_shap_sum:
        feature_abs_shap_sum[name] /= len(checkpoints)
        
    # Sort and get top 10
    top_features = sorted(feature_abs_shap_sum.keys(), key=lambda k: feature_abs_shap_sum[k], reverse=True)[:10]
    
    print("  Global Top Features (according to Mean Ensemble |SHAP|):")
    top_summary = []
    for i, feature in enumerate(top_features, 1):
        shap_val = feature_abs_shap_sum[feature]
        top_summary.append(f"{feature} ({shap_val:.4f})")
        print(f"    {i}. {feature} (Mean |SHAP|: {shap_val:.4f})")
        
    final_summary_rows.append({
        "Inspection Type": inspection_type,
        "Test Samples": len(X_type_raw),
        "Global Top Features (|SHAP|)": " <br> ".join([f"{i}. {val}" for i, val in enumerate(top_summary, 1)])
    })
    
    # Thresholds
    print("\\n  -- Native Thresholds for Top Features (Aggregated) --")
    merged_trees = pd.concat(all_trees, ignore_index=True)
    
    for feature in top_features:
        feature_nodes = merged_trees[merged_trees['FeatureName'] == feature]
        if len(feature_nodes) == 0:
            continue
            
        threshold_agg = feature_nodes.groupby('Split').agg(
            Frequency=('Split', 'count'),
            Total_Cover=('Cover', 'sum')
        ).sort_values(by='Total_Cover', ascending=False)
        
        top_5 = threshold_agg.head(3)
        thresholds_str = ", ".join([f"< {th:.4f} (Cover: {row['Total_Cover']:.0f})" for th, row in top_5.iterrows()])
        print(f"    * {feature}: {thresholds_str}")
        
    print("\\n")
"""))

nb.cells.append(nbf.v4.new_markdown_cell("""## 4. Final Summary Table"""))

nb.cells.append(nbf.v4.new_code_cell("""import IPython.display as display
summary_df = pd.DataFrame(final_summary_rows)
display.display(display.HTML(summary_df.to_html(escape=False, index=False)))

with open("../docs/experiments/0826_dongjin_027_global_ensemble_shap.md", "w", encoding="utf-8") as f:
    f.write("# 0826_dongjin_027_global_ensemble_shap\\n\\n")
    f.write("## Overview\\n")
    f.write("Extracted Global SHAP values over the entire Test Set for each inspection type using the saved `models/0825_peace_005_type_expert_fold_ensemble.pkl` bundle.\\n")
    f.write("## Global Top 10 Features by Type\\n\\n")
    f.write(summary_df.to_markdown(index=False))
    f.write("\\n")
"""))

with open(r"notebooks\0826_dongjin_027_global_ensemble_shap.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

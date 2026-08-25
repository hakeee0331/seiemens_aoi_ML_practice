import nbformat as nbf

nb = nbf.v4.new_notebook()

nb.cells.append(nbf.v4.new_markdown_cell("""# 0825_dongjin_025_ensemble_shap_analysis

This notebook trains the `005_type_expert_fold_ensemble` model from scratch (4 checkpoints x 5 inspection types = 20 models) and performs SHAP and threshold extraction directly in memory. This avoids serialization issues with XGBoost binaries across Python environments.

For each inspection type:
1. We compute ensemble probability on the final Test Set and identify False Positives (False Calls).
2. We compute SHAP values for all 4 checkpoint models, averaging them to find the true Top 10 features driving the False Calls.
3. We extract native decision boundaries (`trees_to_dataframe()`) across all 4 models and aggregate their Cover.
"""))

nb.cells.append(nbf.v4.new_code_cell("""import gc
import json
from pathlib import Path
import pandas as pd
import numpy as np
import shap
import xgboost
from xgboost import XGBClassifier
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
import matplotlib.pyplot as plt

# Configuration
DATA_PATH = Path("../data/raw/dataset.csv")
MAPPING_PATH = Path("../data/raw/mapping.json")
TARGET = "class"
TIME_COLUMN = "timestamp"
TYPE_COLUMN = "inspection_type"
RECORD_ID = "record_id"
DECISION_THRESHOLD = 0.5
RANDOM_STATE = 42

XGB_PARAMS = {
    "objective": "binary:logistic",
    "eval_metric": "aucpr",
    "tree_method": "hist",
    "n_estimators": 400,
    "learning_rate": 0.05,
    "max_depth": 5,
    "min_child_weight": 10,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.1,
    "reg_lambda": 5.0,
    "max_delta_step": 1.0,
    "random_state": RANDOM_STATE,
    "n_jobs": -1,
    "verbosity": 0,
}

ENSEMBLE_CHECKPOINTS = [0.30, 0.40, 0.50, 0.70]
TRAIN_END_FRACTION = 0.70
VALIDATION_END_FRACTION = 0.80
"""))

nb.cells.append(nbf.v4.new_markdown_cell("""## 1. Data Loading and Preparation"""))

nb.cells.append(nbf.v4.new_code_cell("""# Load Data
raw_df = pd.read_csv(DATA_PATH, low_memory=False)
if raw_df.columns[0].startswith("Unnamed:") or raw_df.columns[0] == "":
    raw_df = raw_df.rename(columns={raw_df.columns[0]: RECORD_ID})

raw_df[TIME_COLUMN] = pd.to_datetime(raw_df[TIME_COLUMN], errors="raise", utc=True)
raw_df = raw_df.sort_values([TIME_COLUMN, RECORD_ID], kind="stable").reset_index(drop=True)

# Load Mapping
with open(MAPPING_PATH, encoding="utf-8") as f:
    feature_mapping = json.load(f)

inspection_types = sorted(raw_df[TYPE_COLUMN].unique().tolist())
meta_columns = [col for col in raw_df.columns if col.startswith("meta_feat")]

feature_columns_by_type = {}
for inspection_type in inspection_types:
    mapped_columns = feature_mapping[str(inspection_type)]
    feature_columns_by_type[inspection_type] = meta_columns + mapped_columns

def make_preprocessor(feature_columns):
    categorical = [c for c in meta_columns if c in feature_columns]
    continuous = [c for c in feature_columns if c not in categorical]
    return ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore", dtype=np.float32), categorical),
            ("continuous", "passthrough", continuous),
        ],
        sparse_threshold=1.0,
        verbose_feature_names_out=False,
    )

print("Data loaded. Types:", inspection_types)
"""))

nb.cells.append(nbf.v4.new_markdown_cell("""## 2. Splits and Checkpoint Boundaries"""))

nb.cells.append(nbf.v4.new_code_cell("""timestamp_group_sizes = raw_df.groupby(TIME_COLUMN, sort=True).size()
cumulative_rows = timestamp_group_sizes.cumsum().to_numpy()
timestamp_index = timestamp_group_sizes.index

def boundary_at(fraction: float):
    position = int(np.searchsorted(cumulative_rows, len(raw_df) * fraction, side="left"))
    return timestamp_index[position]

train_end_time = boundary_at(TRAIN_END_FRACTION)
validation_end_time = boundary_at(VALIDATION_END_FRACTION)

test_mask = raw_df[TIME_COLUMN] > validation_end_time
test_df = raw_df.loc[test_mask].copy()

walk_forward_boundaries = {
    fraction: boundary_at(fraction) for fraction in ENSEMBLE_CHECKPOINTS
}

print(f"Test Set Size: {len(test_df)}")
"""))

nb.cells.append(nbf.v4.new_markdown_cell("""## 3. Train Models & Extract SHAP per Type"""))

nb.cells.append(nbf.v4.new_code_cell("""models_by_type = {t: [] for t in inspection_types}
preprocessors_by_type = {t: None for t in inspection_types}
test_probabilities = pd.Series(np.nan, index=test_df.index, dtype="float64")

final_summary_rows = []

for inspection_type in inspection_types:
    print("=" * 80)
    print(f"INSPECTION TYPE: {inspection_type}")
    print("=" * 80)
    
    feature_columns = feature_columns_by_type[inspection_type]
    type_test = test_df.loc[test_df[TYPE_COLUMN] == inspection_type]
    y_test_type = type_test[TARGET].astype("int8")
    
    if len(type_test) == 0:
        continue
        
    # --- A. Training the Ensemble ---
    preprocessor = make_preprocessor(feature_columns)
    
    # Fit preprocessor on the maximum training set (0.70)
    train_70 = raw_df.loc[(raw_df[TIME_COLUMN] <= boundary_at(0.70)) & (raw_df[TYPE_COLUMN] == inspection_type)]
    preprocessor.fit(train_70[feature_columns])
    
    encoded_feature_names = preprocessor.get_feature_names_out()
    
    ensemble_preds = []
    
    for ckpt in ENSEMBLE_CHECKPOINTS:
        print(f"  Training checkpoint {ckpt}...")
        ckpt_train = raw_df.loc[(raw_df[TIME_COLUMN] <= walk_forward_boundaries[ckpt]) & (raw_df[TYPE_COLUMN] == inspection_type)]
        X_train = preprocessor.transform(ckpt_train[feature_columns])
        y_train = ckpt_train[TARGET].astype("int8")
        
        model = XGBClassifier(**XGB_PARAMS)
        model.fit(X_train, y_train, verbose=False)
        models_by_type[inspection_type].append(model)
        
        X_test_encoded = preprocessor.transform(type_test[feature_columns])
        preds = model.predict_proba(X_test_encoded)[:, 1]
        ensemble_preds.append(preds)
        
    # --- B. Find False Calls ---
    mean_preds = np.mean(np.vstack(ensemble_preds), axis=0)
    test_predictions = (mean_preds >= DECISION_THRESHOLD).astype("int8")
    
    mask_fp = (y_test_type == 0) & (test_predictions == 1)
    
    # We must use encoded features for SHAP because the model expects them
    X_fp_type_raw = type_test[feature_columns][mask_fp]
    
    print(f"\\n  Total False Calls: {len(X_fp_type_raw)}\\n")
    if len(X_fp_type_raw) == 0:
        continue
        
    X_fp_type_encoded = preprocessor.transform(X_fp_type_raw)
    
    # Check if sparse, convert to dense if needed for SHAP
    if hasattr(X_fp_type_encoded, "toarray"):
        X_fp_type_encoded = X_fp_type_encoded.toarray()
        
    # --- C. SHAP Analysis (Averaged across Ensemble) ---
    shap_values_list = []
    for model in models_by_type[inspection_type]:
        explainer = shap.TreeExplainer(model)
        shap_values_fp = explainer.shap_values(X_fp_type_encoded)
        shap_values_list.append(shap_values_fp)
        
    avg_shap_values = np.mean(np.array(shap_values_list), axis=0)
    mean_abs_shap = np.abs(avg_shap_values).mean(axis=0)
    
    top_indices = np.argsort(mean_abs_shap)[::-1][:10]
    top_features = [encoded_feature_names[idx] for idx in top_indices]
    
    print("  Top Features Driving False Calls (according to Mean Ensemble SHAP):")
    top_summary = []
    for i, feature in enumerate(top_features, 1):
        shap_val = mean_abs_shap[top_indices[i-1]]
        top_summary.append(f"{feature} ({shap_val:.4f})")
        print(f"    {i}. {feature} (Mean |SHAP|: {shap_val:.4f})")
        
    final_summary_rows.append({
        "Inspection Type": inspection_type,
        "False Calls": len(X_fp_type_raw),
        "Top Features (|SHAP|)": " <br> ".join([f"{i}. {val}" for i, val in enumerate(top_summary, 1)])
    })
    
    # --- D. Extract Thresholds (Aggregated across Ensemble) ---
    print("\\n  -- Native Thresholds for Top Features (Aggregated) --")
    
    all_trees = []
    for model in models_by_type[inspection_type]:
        trees_df = model.get_booster().trees_to_dataframe()
        # the 'Feature' column in trees_df matches the generic feature names f0, f1...
        # We need to map encoded_feature_names to f0, f1...
        feature_map = {f"f{i}": name for i, name in enumerate(encoded_feature_names)}
        trees_df['FeatureName'] = trees_df['Feature'].map(feature_map)
        all_trees.append(trees_df)
        
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

# Save table to Markdown
with open("../docs/experiments/0825_dongjin_025_ensemble_shap_analysis.md", "w", encoding="utf-8") as f:
    f.write("# 0825_dongjin_025_ensemble_shap_analysis\\n\\n")
    f.write("## Overview\\n")
    f.write("Extracted False Calls and SHAP values natively by reproducing the `005_type_expert_fold_ensemble` training process.\\n")
    f.write("SHAP values and thresholds were averaged/aggregated across the 4 checkpoint models for each inspection type.\\n\\n")
    f.write("## Top 10 Features Driving False Calls by Type\\n\\n")
    f.write(summary_df.to_markdown(index=False))
    f.write("\\n")
"""))

# FIX: Writing to the correct output notebook file!
with open(r"notebooks\0825_dongjin_025_ensemble_shap_analysis.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

#!/usr/bin/env python
# coding: utf-8

# # 0825_peace_005_type_expert_fold_ensemble
# 
# 타입별 XGBoost 전문가 모델에 시간순 Fold 앙상블을 실제 학습·추론 방식으로 적용한 실험입니다.
# 
# - 누적 체크포인트 0~30%, 0~40%, 0~50%, 0~70%에서 각각 타입별 모델 5개를 독립 학습합니다.
# - Walk-forward에서는 해당 시점까지 존재하는 체크포인트 모델의 확률을 동일 가중 평균합니다.
# - 최종 Validation/Test는 네 체크포인트 모델의 평균 확률로 평가합니다.
# - 분할·피처·파라미터·평가 지표는 `0825_peace_004_type_expert_walk_forward`와 동일합니다.
# 

# ## 1. 설정, 경로 탐색과 실행 로그

# In[1]:


import gc
import hashlib
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import xgboost
from IPython.display import display
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

EXPERIMENT_ID = "0825_peace_005_type_expert_fold_ensemble"
RANDOM_STATE = 42
TARGET = "class"
TIME_COLUMN = "timestamp"
TYPE_COLUMN = "inspection_type"
RECORD_ID = "record_id"
DECISION_THRESHOLD = 0.5
MIN_RECALL = 0.99
TRAIN_END_FRACTION = 0.70
VALIDATION_END_FRACTION = 0.80

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


def find_repo_root() -> Path:
    for candidate in [Path.cwd(), *Path.cwd().parents]:
        if (candidate / "AGENTS.md").exists() and (candidate / "notebooks").is_dir():
            return candidate.resolve()
    raise FileNotFoundError("AGENTS.md가 있는 저장소 루트를 찾지 못했습니다.")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_data_pair(repo_root: Path) -> tuple[Path, Path]:
    candidates = [
        repo_root / "data" / "raw",
        repo_root.parent,
        Path.cwd(),
        Path.cwd().parent,
        Path.cwd().parent.parent,
    ]
    checked = set()
    for directory in candidates:
        resolved = directory.resolve()
        if resolved in checked:
            continue
        checked.add(resolved)
        data_path = resolved / "dataset.csv"
        mapping_path = resolved / "mapping.json"
        if data_path.exists() and mapping_path.exists():
            return data_path, mapping_path
    raise FileNotFoundError("dataset.csv와 mapping.json 쌍을 찾지 못했습니다.")


REPO_ROOT = find_repo_root()
DATA_PATH, MAPPING_PATH = find_data_pair(REPO_ROOT)
LOG_DIR = REPO_ROOT / "docs" / "peace"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / f"{EXPERIMENT_ID}.log"

logger = logging.getLogger(EXPERIMENT_ID)
logger.setLevel(logging.INFO)
logger.handlers.clear()
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
file_handler = logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8")
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.propagate = False

DATA_SHA256_BEFORE = sha256_file(DATA_PATH)
MAPPING_SHA256_BEFORE = sha256_file(MAPPING_PATH)
logger.info("experiment=%s", EXPERIMENT_ID)
logger.info(
    "random_state=%d baseline_threshold=%.2f min_recall=%.2f",
    RANDOM_STATE,
    DECISION_THRESHOLD,
    MIN_RECALL,
)
logger.info("data_file=%s sha256=%s", DATA_PATH.name, DATA_SHA256_BEFORE)
logger.info("mapping_file=%s sha256=%s", MAPPING_PATH.name, MAPPING_SHA256_BEFORE)
logger.info(
    "versions python=%s pandas=%s sklearn=%s xgboost=%s",
    sys.version.split()[0], pd.__version__, sklearn.__version__, xgboost.__version__
)
logger.info("log_file=docs/peace/%s", LOG_PATH.name)
print("log saved to:", LOG_PATH.relative_to(REPO_ROOT))


# ## 2. 원본 데이터와 매핑 검증

# In[2]:


raw_df = pd.read_csv(DATA_PATH, low_memory=False)
source_index_column = raw_df.columns[0]
if source_index_column.startswith("Unnamed:") or source_index_column == "":
    raw_df = raw_df.rename(columns={source_index_column: RECORD_ID})
elif source_index_column != RECORD_ID:
    raise ValueError(f"예상하지 못한 첫 번째 컬럼: {source_index_column}")

with MAPPING_PATH.open(encoding="utf-8") as stream:
    feature_mapping = json.load(stream)

required_columns = {RECORD_ID, TIME_COLUMN, TYPE_COLUMN, TARGET}
missing_required = required_columns - set(raw_df.columns)
assert not missing_required, f"필수 컬럼 누락: {sorted(missing_required)}"
assert len(raw_df) == 440_274
assert raw_df[RECORD_ID].is_unique
assert set(raw_df[TARGET].unique()) == {0, 1}
assert raw_df[TARGET].value_counts().to_dict() == {0: 435_652, 1: 4_622}
assert set(raw_df[TYPE_COLUMN].unique()) == {0, 1, 2, 3, 4}
assert set(feature_mapping) == {"0", "1", "2", "3", "4"}

raw_df[TIME_COLUMN] = pd.to_datetime(raw_df[TIME_COLUMN], errors="raise", utc=True)
raw_df = raw_df.sort_values([TIME_COLUMN, RECORD_ID], kind="stable").reset_index(drop=True)
inspection_columns = [column for column in raw_df.columns if column.startswith("inspection_feat")]
mapped_union = set().union(*(set(columns) for columns in feature_mapping.values()))
assert len(inspection_columns) == 70
assert len(mapped_union) == 65
assert mapped_union <= set(inspection_columns)

numeric_inputs = raw_df.select_dtypes(include=[np.number]).drop(columns=[TARGET, RECORD_ID])
assert np.isfinite(numeric_inputs.to_numpy()).all()

data_summary = pd.Series(
    {
        "rows": len(raw_df),
        "columns": raw_df.shape[1],
        "false_call_0": int((raw_df[TARGET] == 0).sum()),
        "real_defect_1": int((raw_df[TARGET] == 1).sum()),
        "real_defect_rate_pct": raw_df[TARGET].mean() * 100,
        "inspection_types": raw_df[TYPE_COLUMN].nunique(),
        "inspection_features": len(inspection_columns),
        "mapped_feature_union": len(mapped_union),
        "timestamp_start": raw_df[TIME_COLUMN].min(),
        "timestamp_end": raw_df[TIME_COLUMN].max(),
    },
    name="raw_data",
)
display(data_summary)
logger.info(
    "data_verified rows=%d columns=%d class_0=%d class_1=%d",
    len(raw_df), raw_df.shape[1], int((raw_df[TARGET] == 0).sum()), int((raw_df[TARGET] == 1).sum())
)


# ## 3. 타입별 유효 피처

# In[3]:


inspection_types = sorted(raw_df[TYPE_COLUMN].unique().tolist())
meta_columns = [column for column in raw_df.columns if column.startswith("meta_feat")]
feature_columns_by_type = {}
feature_rows = []

for inspection_type in inspection_types:
    mapped_columns = feature_mapping[str(inspection_type)]
    assert len(mapped_columns) == len(set(mapped_columns))
    assert set(mapped_columns) <= set(raw_df.columns)
    selected_columns = meta_columns + mapped_columns
    feature_columns_by_type[inspection_type] = selected_columns
    feature_rows.append(
        {
            "inspection_type": inspection_type,
            "meta_features": len(meta_columns),
            "mapped_inspection_features": len(mapped_columns),
            "total_model_features": len(selected_columns),
        }
    )

feature_summary = pd.DataFrame(feature_rows).set_index("inspection_type")
display(feature_summary)
logger.info("feature_mapping_verified=%s", feature_summary.to_dict(orient="index"))


# ## 4. 동일한 시간순 Train/Validation/Test 분할

# In[4]:


timestamp_group_sizes = raw_df.groupby(TIME_COLUMN, sort=True).size()
cumulative_rows = timestamp_group_sizes.cumsum().to_numpy()
timestamp_index = timestamp_group_sizes.index


def boundary_at(fraction: float):
    position = int(np.searchsorted(cumulative_rows, len(raw_df) * fraction, side="left"))
    return timestamp_index[position]


train_end_time = boundary_at(TRAIN_END_FRACTION)
validation_end_time = boundary_at(VALIDATION_END_FRACTION)
train_mask = raw_df[TIME_COLUMN] <= train_end_time
validation_mask = (
    (raw_df[TIME_COLUMN] > train_end_time)
    & (raw_df[TIME_COLUMN] <= validation_end_time)
)
test_mask = raw_df[TIME_COLUMN] > validation_end_time

train_df = raw_df.loc[train_mask]
validation_df = raw_df.loc[validation_mask]
test_df = raw_df.loc[test_mask]
assert train_df[TIME_COLUMN].max() < validation_df[TIME_COLUMN].min()
assert set(train_df[TIME_COLUMN]).isdisjoint(set(validation_df[TIME_COLUMN]))
assert validation_df[TIME_COLUMN].max() < test_df[TIME_COLUMN].min()
assert set(validation_df[TIME_COLUMN]).isdisjoint(set(test_df[TIME_COLUMN]))
assert int(train_mask.sum() + validation_mask.sum() + test_mask.sum()) == len(raw_df)

split_summary = pd.DataFrame(
    [
        {
            "split": "train",
            "rows": len(train_df),
            "positive_samples": int(train_df[TARGET].sum()),
            "positive_rate_pct": train_df[TARGET].mean() * 100,
            "timestamp_groups": train_df[TIME_COLUMN].nunique(),
            "start_time": train_df[TIME_COLUMN].min(),
            "end_time": train_df[TIME_COLUMN].max(),
        },
        {
            "split": "validation",
            "rows": len(validation_df),
            "positive_samples": int(validation_df[TARGET].sum()),
            "positive_rate_pct": validation_df[TARGET].mean() * 100,
            "timestamp_groups": validation_df[TIME_COLUMN].nunique(),
            "start_time": validation_df[TIME_COLUMN].min(),
            "end_time": validation_df[TIME_COLUMN].max(),
        },
        {
            "split": "test",
            "rows": len(test_df),
            "positive_samples": int(test_df[TARGET].sum()),
            "positive_rate_pct": test_df[TARGET].mean() * 100,
            "timestamp_groups": test_df[TIME_COLUMN].nunique(),
            "start_time": test_df[TIME_COLUMN].min(),
            "end_time": test_df[TIME_COLUMN].max(),
        },
    ]
).set_index("split")
display(split_summary)
evaluation_policy = pd.Series(
    {
        "model_selection_uses_test": False,
        "threshold_selected_on_test": False,
        "fixed_test_threshold": DECISION_THRESHOLD,
    },
    name="evaluation_policy",
)
display(evaluation_policy)
logger.info("split_summary=%s", split_summary.reset_index().to_dict(orient="records"))
logger.info("test_policy model_selection=False threshold=%.2f", DECISION_THRESHOLD)


# ## 5. 동일한 평가 지표와 임계값 선택 함수

# In[5]:


def evaluate_predictions(y_true, prediction, probability):
    y_true = np.asarray(y_true, dtype=np.int8)
    prediction = np.asarray(prediction, dtype=np.int8)
    probability = np.asarray(probability, dtype=np.float64)
    tn, fp, fn, tp = confusion_matrix(y_true, prediction, labels=[0, 1]).ravel()
    has_both_classes = np.unique(y_true).size == 2
    has_positive = (tp + fn) > 0
    return {
        "rows": len(y_true),
        "positive_samples": int(y_true.sum()),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "accuracy": accuracy_score(y_true, prediction),
        "precision": precision_score(y_true, prediction, zero_division=0),
        "recall": recall_score(y_true, prediction, zero_division=0) if has_positive else np.nan,
        "false_call_reduction": tn / (tn + fp) if (tn + fp) else np.nan,
        "f1": f1_score(y_true, prediction, zero_division=0) if has_positive else np.nan,
        "roc_auc": roc_auc_score(y_true, probability) if has_both_classes else np.nan,
        "pr_auc": average_precision_score(y_true, probability) if has_both_classes else np.nan,
    }


def evaluate_probabilities(y_true, probability, threshold=DECISION_THRESHOLD):
    probability = np.asarray(probability, dtype=np.float64)
    prediction = (probability >= threshold).astype(np.int8)
    return evaluate_predictions(y_true, prediction, probability)


def select_threshold(y_true, probability, min_recall=MIN_RECALL):
    """Recall 제약을 만족하며 False Call Reduction이 최대인 threshold를 선택한다."""
    y_true = np.asarray(y_true, dtype=np.int8)
    probability = np.asarray(probability, dtype=np.float64)
    if np.unique(y_true).size != 2:
        raise ValueError("임계값 선택에는 positive와 negative가 모두 필요합니다.")

    order = np.argsort(-probability, kind="stable")
    sorted_probability = probability[order]
    sorted_target = y_true[order]
    cumulative_tp = np.cumsum(sorted_target == 1)
    cumulative_fp = np.cumsum(sorted_target == 0)
    group_ends = np.flatnonzero(
        np.r_[sorted_probability[:-1] != sorted_probability[1:], True]
    )

    thresholds = sorted_probability[group_ends]
    tp = cumulative_tp[group_ends]
    fp = cumulative_fp[group_ends]
    total_positive = int((y_true == 1).sum())
    total_negative = int((y_true == 0).sum())
    recall = tp / total_positive
    false_call_reduction = 1.0 - (fp / total_negative)
    feasible = np.flatnonzero(recall >= min_recall)
    if feasible.size == 0:
        raise RuntimeError(f"Recall {min_recall:.2%} 조건을 만족하는 threshold가 없습니다.")

    best_local = np.lexsort(
        (thresholds[feasible], recall[feasible], false_call_reduction[feasible])
    )[-1]
    best = feasible[best_local]
    selected_threshold = float(thresholds[best])
    metrics = evaluate_probabilities(y_true, probability, selected_threshold)
    return {"threshold": selected_threshold, "min_recall": min_recall, **metrics}


# 최적화 구현이 작은 합성 예제의 완전 탐색과 같은 결과인지 검증한다.
_test_y = np.array([1, 0, 1, 0, 1, 0], dtype=np.int8)
_test_probability = np.array([0.9, 0.8, 0.7, 0.6, 0.4, 0.2])
_optimized = select_threshold(_test_y, _test_probability, min_recall=2 / 3)
_reference_rows = []
for _threshold in np.unique(_test_probability):
    _metrics = evaluate_probabilities(_test_y, _test_probability, _threshold)
    if _metrics["recall"] >= 2 / 3:
        _reference_rows.append((_metrics["false_call_reduction"], _metrics["recall"], _threshold))
_reference = max(_reference_rows)
assert np.isclose(_optimized["threshold"], _reference[2])
logger.info("threshold_selector_unit_test=PASS")

def make_preprocessor(feature_columns):
    categorical = [column for column in meta_columns if column in feature_columns]
    continuous = [column for column in feature_columns if column not in categorical]
    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", dtype=np.float32),
                categorical,
            ),
            ("continuous", "passthrough", continuous),
        ],
        sparse_threshold=1.0,
        verbose_feature_names_out=True,
    )


def evaluate_calibration_and_future(calibration_frame, calibration_probability, evaluation_frame, evaluation_probability, stage_name):
    global_selection = select_threshold(calibration_frame[TARGET], calibration_probability, min_recall=MIN_RECALL)
    type_thresholds = {}
    type_prediction = pd.Series(np.nan, index=evaluation_frame.index, dtype="float64")
    threshold_rows = [{"stage": stage_name, "scope": "global", **global_selection}]
    type_rows = []
    for inspection_type in inspection_types:
        type_calibration = calibration_frame.loc[calibration_frame[TYPE_COLUMN] == inspection_type]
        selection = select_threshold(type_calibration[TARGET], calibration_probability.loc[type_calibration.index], min_recall=MIN_RECALL)
        type_thresholds[inspection_type] = selection["threshold"]
        threshold_rows.append({"stage": stage_name, "scope": f"type_{inspection_type}", **selection})
        type_evaluation = evaluation_frame.loc[evaluation_frame[TYPE_COLUMN] == inspection_type]
        type_probability = evaluation_probability.loc[type_evaluation.index]
        prediction = (type_probability >= selection["threshold"]).astype("int8")
        type_prediction.loc[type_evaluation.index] = prediction
        metrics = evaluate_predictions(type_evaluation[TARGET], prediction, type_probability)
        type_rows.append({"stage": stage_name, "inspection_type": inspection_type, "threshold": selection["threshold"], **metrics})
    strategy_metrics = {
        "fixed_0.5": evaluate_probabilities(evaluation_frame[TARGET], evaluation_probability, DECISION_THRESHOLD),
        "global_threshold": evaluate_probabilities(evaluation_frame[TARGET], evaluation_probability, global_selection["threshold"]),
        "type_specific_thresholds": evaluate_predictions(evaluation_frame[TARGET], type_prediction, evaluation_probability),
    }
    metric_rows = [{"stage": stage_name, "strategy": strategy, **metrics} for strategy, metrics in strategy_metrics.items()]
    return {"global_selection": global_selection, "type_thresholds": type_thresholds, "threshold_rows": threshold_rows, "type_rows": type_rows, "metric_rows": metric_rows}


# ## 6. 동일한 3-Fold Expanding Walk-forward 구간

# In[6]:


WALK_FORWARD_SPECS = [
    {
        "fold": "fold_1",
        "train_start": 0.00,
        "train_end": 0.30,
        "calibration_start": 0.30,
        "calibration_end": 0.40,
        "evaluation_start": 0.40,
        "evaluation_end": 0.50,
    },
    {
        "fold": "fold_2",
        "train_start": 0.00,
        "train_end": 0.40,
        "calibration_start": 0.40,
        "calibration_end": 0.50,
        "evaluation_start": 0.50,
        "evaluation_end": 0.60,
    },
    {
        "fold": "fold_3",
        "train_start": 0.00,
        "train_end": 0.50,
        "calibration_start": 0.50,
        "calibration_end": 0.60,
        "evaluation_start": 0.60,
        "evaluation_end": 0.70,
    },
]

walk_forward_boundaries = {
    fraction: boundary_at(fraction)
    for fraction in [0.30, 0.40, 0.50, 0.60, 0.70]
}
walk_forward_segments = {}
walk_forward_split_rows = []

for spec in WALK_FORWARD_SPECS:
    fold_name = spec["fold"]
    train_end = walk_forward_boundaries[spec["train_end"]]
    calibration_start = walk_forward_boundaries[spec["calibration_start"]]
    calibration_end = walk_forward_boundaries[spec["calibration_end"]]
    evaluation_start = walk_forward_boundaries[spec["evaluation_start"]]
    evaluation_end = walk_forward_boundaries[spec["evaluation_end"]]

    segments = {
        "train": raw_df.loc[raw_df[TIME_COLUMN] <= train_end],
        "calibration": raw_df.loc[
            (raw_df[TIME_COLUMN] > calibration_start)
            & (raw_df[TIME_COLUMN] <= calibration_end)
        ],
        "evaluation": raw_df.loc[
            (raw_df[TIME_COLUMN] > evaluation_start)
            & (raw_df[TIME_COLUMN] <= evaluation_end)
        ],
    }
    assert segments["train"][TIME_COLUMN].max() < segments["calibration"][TIME_COLUMN].min()
    assert segments["calibration"][TIME_COLUMN].max() < segments["evaluation"][TIME_COLUMN].min()
    assert set(segments["train"][TIME_COLUMN]).isdisjoint(segments["calibration"][TIME_COLUMN])
    assert set(segments["calibration"][TIME_COLUMN]).isdisjoint(segments["evaluation"][TIME_COLUMN])
    walk_forward_segments[fold_name] = segments

    for segment_name, frame in segments.items():
        walk_forward_split_rows.append(
            {
                "fold": fold_name,
                "segment": segment_name,
                "rows": len(frame),
                "positive_samples": int(frame[TARGET].sum()),
                "positive_rate_pct": frame[TARGET].mean() * 100,
                "timestamp_groups": frame[TIME_COLUMN].nunique(),
                "start_time": frame[TIME_COLUMN].min(),
                "end_time": frame[TIME_COLUMN].max(),
            }
        )

walk_forward_split_summary = pd.DataFrame(walk_forward_split_rows).set_index(
    ["fold", "segment"]
)
display(walk_forward_split_summary)
logger.info(
    "walk_forward_split_summary=%s",
    walk_forward_split_summary.reset_index().to_dict(orient="records"),
)


# ## 7. 누적 시간 체크포인트별 Fold 모델 학습

# In[7]:


ENSEMBLE_CHECKPOINTS = [0.30, 0.40, 0.50, 0.70]
FOLD_MEMBER_CHECKPOINTS = {"fold_1": [0.30], "fold_2": [0.30, 0.40], "fold_3": [0.30, 0.40, 0.50]}
FINAL_MEMBER_CHECKPOINTS = ENSEMBLE_CHECKPOINTS.copy()

prediction_targets = {}
for spec in WALK_FORWARD_SPECS:
    fold_name = spec["fold"]
    prediction_targets[f"{fold_name}_calibration"] = walk_forward_segments[fold_name]["calibration"]
    prediction_targets[f"{fold_name}_evaluation"] = walk_forward_segments[fold_name]["evaluation"]
prediction_targets["final_validation"] = validation_df
prediction_targets["final_test"] = test_df

checkpoint_predictions = {
    checkpoint: {
        target_name: pd.Series(np.nan, index=frame.index, dtype="float64")
        for target_name, frame in prediction_targets.items()
        if frame[TIME_COLUMN].min() > walk_forward_boundaries[checkpoint]
    }
    for checkpoint in ENSEMBLE_CHECKPOINTS
}
ensemble_training_rows = []
for checkpoint in ENSEMBLE_CHECKPOINTS:
    checkpoint_train = raw_df.loc[raw_df[TIME_COLUMN] <= walk_forward_boundaries[checkpoint]]
    for inspection_type in inspection_types:
        feature_columns = feature_columns_by_type[inspection_type]
        type_train = checkpoint_train.loc[checkpoint_train[TYPE_COLUMN] == inspection_type]
        y_train = type_train[TARGET].astype("int8")
        assert y_train.nunique() == 2
        preprocessor = make_preprocessor(feature_columns)
        X_train = preprocessor.fit_transform(type_train[feature_columns])
        model = XGBClassifier(**XGB_PARAMS)
        model.fit(X_train, y_train, verbose=False)
        for target_name, probability_series in checkpoint_predictions[checkpoint].items():
            target_frame = prediction_targets[target_name]
            type_target = target_frame.loc[target_frame[TYPE_COLUMN] == inspection_type]
            X_target = preprocessor.transform(type_target[feature_columns])
            probability_series.loc[type_target.index] = model.predict_proba(X_target)[:, 1]
            del X_target
        ensemble_training_rows.append({
            "checkpoint": checkpoint, "inspection_type": inspection_type,
            "train_rows": len(type_train), "train_positive": int(y_train.sum()),
            "raw_features": len(feature_columns), "encoded_features": X_train.shape[1],
            "trees": model.get_booster().num_boosted_rounds(),
        })
        logger.info("ensemble_member_fit_done checkpoint=%.2f type=%d rows=%d positive=%d", checkpoint, inspection_type, len(type_train), int(y_train.sum()))
        del preprocessor, model, X_train
        gc.collect()
for checkpoint, target_map in checkpoint_predictions.items():
    for target_name, probability in target_map.items():
        assert probability.notna().all(), (checkpoint, target_name)
ensemble_training_summary = pd.DataFrame(ensemble_training_rows).set_index(["checkpoint", "inspection_type"])
display(ensemble_training_summary)
logger.info("ensemble_members_trained=%d", len(ensemble_training_rows))


# ## 8. Walk-forward 미래 Evaluation 결과

# In[8]:


def mean_checkpoint_probability(checkpoints, target_name):
    probabilities = [checkpoint_predictions[checkpoint][target_name].to_numpy() for checkpoint in checkpoints]
    return pd.Series(np.mean(np.vstack(probabilities), axis=0), index=prediction_targets[target_name].index, dtype="float64")

walk_threshold_rows, walk_metric_rows, walk_type_rows = [], [], []
for spec in WALK_FORWARD_SPECS:
    fold_name = spec["fold"]
    members = FOLD_MEMBER_CHECKPOINTS[fold_name]
    result = evaluate_calibration_and_future(
        walk_forward_segments[fold_name]["calibration"], mean_checkpoint_probability(members, f"{fold_name}_calibration"),
        walk_forward_segments[fold_name]["evaluation"], mean_checkpoint_probability(members, f"{fold_name}_evaluation"), fold_name,
    )
    walk_threshold_rows.extend(result["threshold_rows"])
    walk_metric_rows.extend(result["metric_rows"])
    walk_type_rows.extend(result["type_rows"])
    logger.info("ensemble_walk_fold_done fold=%s checkpoints=%s", fold_name, members)

walk_forward_threshold_summary = pd.DataFrame(walk_threshold_rows).set_index(["stage", "scope"])
walk_forward_evaluation_metrics = pd.DataFrame(walk_metric_rows).set_index(["stage", "strategy"])
walk_forward_type_evaluation = pd.DataFrame(walk_type_rows).set_index(["stage", "inspection_type"])
walk_forward_strategy_summary = (
    walk_forward_evaluation_metrics.reset_index().groupby("strategy").agg(
        folds=("stage", "nunique"), mean_pr_auc=("pr_auc", "mean"),
        mean_recall=("recall", "mean"), min_recall=("recall", "min"),
        recall_99_folds=("recall", lambda values: int((values >= MIN_RECALL).sum())),
        mean_false_call_reduction=("false_call_reduction", "mean"),
        min_false_call_reduction=("false_call_reduction", "min"),
        total_tp=("tp", "sum"), total_fn=("fn", "sum"),
    )
)
display(walk_forward_threshold_summary[["threshold", "positive_samples", "recall", "false_call_reduction", "tp", "fn"]])
display(walk_forward_evaluation_metrics[["positive_samples", "pr_auc", "precision", "recall", "false_call_reduction", "f1", "tp", "fn", "fp", "tn"]])
display(walk_forward_type_evaluation[["threshold", "positive_samples", "pr_auc", "recall", "false_call_reduction", "tp", "fn"]])
display(walk_forward_strategy_summary)
logger.info("walk_forward_strategy_summary=%s", walk_forward_strategy_summary.to_dict(orient="index"))


# ## 9. 최종 Validation 임계값 선택과 Walk-forward 모델의 Test 추론

# In[9]:


validation_probability = mean_checkpoint_probability(FINAL_MEMBER_CHECKPOINTS, "final_validation")
test_probability = mean_checkpoint_probability(FINAL_MEMBER_CHECKPOINTS, "final_test")
model_summary = pd.Series({"ensemble_members": len(FINAL_MEMBER_CHECKPOINTS), "member_checkpoints": FINAL_MEMBER_CHECKPOINTS}, name="final_ensemble")

final_result = evaluate_calibration_and_future(validation_df, validation_probability, test_df, test_probability, "final_test")
global_threshold_selection = final_result["global_selection"]
thresholds_by_type = final_result["type_thresholds"]
threshold_summary = pd.DataFrame(final_result["threshold_rows"]).set_index(["stage", "scope"])
type_selected_test_metrics = pd.DataFrame(final_result["type_rows"]).set_index(["stage", "inspection_type"])
test_strategy_metrics = pd.DataFrame(final_result["metric_rows"]).set_index(["stage", "strategy"])
validation_fixed_metrics = pd.Series(evaluate_probabilities(validation_df[TARGET], validation_probability), name="validation_fixed_0.5")
type_validation_rows, type_test_rows = [], []
for inspection_type in inspection_types:
    type_validation = validation_df.loc[validation_df[TYPE_COLUMN] == inspection_type]
    type_test = test_df.loc[test_df[TYPE_COLUMN] == inspection_type]
    type_validation_rows.append({"inspection_type": inspection_type, **evaluate_probabilities(type_validation[TARGET], validation_probability.loc[type_validation.index])})
    type_test_rows.append({"inspection_type": inspection_type, **evaluate_probabilities(type_test[TARGET], test_probability.loc[type_test.index])})
type_validation_metrics = pd.DataFrame(type_validation_rows).set_index("inspection_type")
type_test_metrics = pd.DataFrame(type_test_rows).set_index("inspection_type")
display(model_summary)
display(threshold_summary[["threshold", "positive_samples", "recall", "false_call_reduction", "tp", "fn", "fp", "tn"]])
display(test_strategy_metrics[["pr_auc", "precision", "recall", "false_call_reduction", "f1", "tp", "fn", "fp", "tn"]])
display(type_selected_test_metrics[["threshold", "positive_samples", "pr_auc", "precision", "recall", "false_call_reduction", "tp", "fn", "fp", "tn"]])
display(type_validation_metrics)
display(type_test_metrics)
logger.info("validation_fixed_metrics=%s", validation_fixed_metrics.to_dict())
logger.info("test_strategy_metrics=%s", test_strategy_metrics.reset_index().to_dict(orient="records"))


# ## 10. 원본 무결성과 종료 확인

# In[10]:


DATA_SHA256_AFTER = sha256_file(DATA_PATH)
MAPPING_SHA256_AFTER = sha256_file(MAPPING_PATH)
assert DATA_SHA256_AFTER == DATA_SHA256_BEFORE
assert MAPPING_SHA256_AFTER == MAPPING_SHA256_BEFORE
verification = pd.Series({
    "dataset_sha256_unchanged": True, "mapping_sha256_unchanged": True,
    "trained_model_units": len(FINAL_MEMBER_CHECKPOINTS) * len(inspection_types), "final_ensemble_members": len(FINAL_MEMBER_CHECKPOINTS),
    "test_evaluated_with_walk_forward_model": True,
    "fixed_threshold": DECISION_THRESHOLD,
    "global_threshold": global_threshold_selection["threshold"],
    "type_thresholds": thresholds_by_type,
    "log_file": f"docs/peace/{LOG_PATH.name}",
}, name="verification")
display(verification)
logger.info("source_integrity=PASS walk_forward_test_model=True")
logger.info("experiment_complete=%s", EXPERIMENT_ID)
for handler in logger.handlers:
    handler.flush()


# ## 11. 결론과 해석
# 
# - 최종 Test PR-AUC는 **0.382545**로, 실제 누적 Fold 모델 네 개의 평균 확률에서 계산됐습니다.
# - Validation에서 선택한 공통 임계값은 Test Recall **93.94%**, False Call Reduction **52.04%**였습니다.
# - 타입별 임계값은 Test Recall **93.29%**, False Call Reduction **47.67%**였습니다.
# - Walk-forward 공통 임계값은 평균 Recall **98.68%**였지만 최저 Fold Recall은 **96.05%**로, 모든 미래 Fold에서 99%를 유지하지는 못했습니다.
# - 다음 비교에서는 앙상블이 타입당 4개 모델을 사용한다는 계산량 차이를 함께 고려해야 합니다.
# 

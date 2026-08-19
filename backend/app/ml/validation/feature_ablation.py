import numpy as np

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)

from app.ml.model import BehaviorModel


# ============================================================
# Configuration
# ============================================================

TRAIN_PATH = "data/ml_validation/train_normal.npy"
CALIBRATION_PATH = "data/ml_validation/calibration_normal.npy"

# These are development/validation samples.
# DO NOT use independent holdout data here.
ANOMALY_PATH = "data/ml_validation/calibration_anomaly.npy"

THRESHOLD_FPR = 0.10

N_ESTIMATORS = 300
CONTAMINATION = 0.05

SEEDS = [42, 123, 456, 789, 999]


# ============================================================
# Feature definitions
# ============================================================

FEATURE_NAMES = [
    "process_creation",
    "process_termination",
    "unique_processes",
    "average_cpu",
    "maximum_cpu",
    "average_memory",
    "maximum_memory",
    "external_connections",
    "failed_logins",
    "privilege_escalations",
    "filesystem_modifications",
    "service_restarts",
    "kernel_exec",
    "kernel_connect",
    "kernel_open",
    "kernel_unlink",
    "kernel_setuid",
    "kernel_ptrace",
]


# ============================================================
# Feature groups
# ============================================================

FEATURE_SETS = {
    "all_18": list(range(18)),

    # Remove CPU and memory.
    "behavioral_14": [
        0, 1, 2,
        7, 8, 9, 10, 11,
        12, 13, 14, 15, 16, 17,
    ],

    # Process + network + authentication.
    "process_network_auth": [
        0, 1, 2,
        7, 8, 9,
    ],

    # Filesystem + kernel.
    "filesystem_kernel": [
        10, 11,
        12, 13, 14, 15, 16, 17,
    ],

    # Explicit security-focused representation.
    "security_focused": [
        0, 1, 2,
        7, 8, 9,
        10, 11,
        12, 13, 14, 15, 16, 17,
    ],
}


# ============================================================
# Feature transformation
# ============================================================

LOG_FEATURES = {
    0,
    1,
    2,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
}


def transform(data: np.ndarray, feature_indices: list[int]) -> np.ndarray:

    data = np.asarray(
        data,
        dtype=float,
    ).copy()

    for index in LOG_FEATURES:
        if index in feature_indices:
            column = feature_indices.index(index)

            data[:, column] = np.log1p(
                np.maximum(
                    data[:, column],
                    0,
                )
            )

    return data


# ============================================================
# Evaluate one feature configuration
# ============================================================

def evaluate_feature_set(
    train: np.ndarray,
    calibration_normal: np.ndarray,
    calibration_anomaly: np.ndarray,
    feature_indices: list[int],
    seed: int,
):
    train_selected = train[:, feature_indices]

    normal_selected = calibration_normal[:, feature_indices]

    anomaly_selected = calibration_anomaly[:, feature_indices]

    # --------------------------------------------------------
    # Transform
    # --------------------------------------------------------

    train_transformed = transform(
        train_selected,
        feature_indices,
    )

    normal_transformed = transform(
        normal_selected,
        feature_indices,
    )

    anomaly_transformed = transform(
        anomaly_selected,
        feature_indices,
    )

    # --------------------------------------------------------
    # Scale
    # --------------------------------------------------------

    scaler = RobustScaler()

    train_scaled = scaler.fit_transform(
        train_transformed
    )

    normal_scaled = scaler.transform(
        normal_transformed
    )

    anomaly_scaled = scaler.transform(
        anomaly_transformed
    )

    # --------------------------------------------------------
    # Train Isolation Forest
    # --------------------------------------------------------

    model = IsolationForest(
        contamination=CONTAMINATION,
        n_estimators=N_ESTIMATORS,
        random_state=seed,
        n_jobs=-1,
    )

    model.fit(train_scaled)

    # --------------------------------------------------------
    # Calibration scores
    # --------------------------------------------------------

    calibration_scores = model.score_samples(
        normal_scaled
    )

    # Lower score = more anomalous.
    threshold = float(
        np.quantile(
            calibration_scores,
            THRESHOLD_FPR,
        )
    )

    # --------------------------------------------------------
    # Evaluate calibration anomaly set
    # --------------------------------------------------------

    normal_scores = model.score_samples(
        normal_scaled
    )

    anomaly_scores = model.score_samples(
        anomaly_scaled
    )

    y_true = np.concatenate(
        [
            np.zeros(len(normal_scores)),
            np.ones(len(anomaly_scores)),
        ]
    )

    y_pred = np.concatenate(
        [
            normal_scores <= threshold,
            anomaly_scores <= threshold,
        ]
    ).astype(int)

    accuracy = accuracy_score(
        y_true,
        y_pred,
    )

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    false_positive_rate = np.mean(
        normal_scores <= threshold
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": false_positive_rate,
        "threshold": threshold,
    }


# ============================================================
# Main
# ============================================================

def main():

    train = np.load(
        TRAIN_PATH
    )

    calibration_normal = np.load(
        CALIBRATION_PATH
    )

    calibration_anomaly = np.load(
        ANOMALY_PATH
    )

    print()
    print("# KATANA FEATURE ABLATION")
    print("=" * 72)

    print(
        f"Training normal     : {len(train)}"
    )

    print(
        f"Calibration normal  : {len(calibration_normal)}"
    )

    print(
        f"Calibration anomaly : {len(calibration_anomaly)}"
    )

    print(
        f"Estimators          : {N_ESTIMATORS}"
    )

    print(
        f"Contamination       : {CONTAMINATION}"
    )

    print(
        f"Target calibration FPR: {THRESHOLD_FPR}"
    )

    print()

    results = []

    # ========================================================
    # Evaluate every feature set across multiple seeds
    # ========================================================

    for feature_set_name, feature_indices in FEATURE_SETS.items():

        seed_results = []

        for seed in SEEDS:

            metrics = evaluate_feature_set(
                train,
                calibration_normal,
                calibration_anomaly,
                feature_indices,
                seed,
            )

            seed_results.append(metrics)

        mean_accuracy = np.mean(
            [x["accuracy"] for x in seed_results]
        )

        mean_precision = np.mean(
            [x["precision"] for x in seed_results]
        )

        mean_recall = np.mean(
            [x["recall"] for x in seed_results]
        )

        mean_f1 = np.mean(
            [x["f1"] for x in seed_results]
        )

        mean_fpr = np.mean(
            [x["fpr"] for x in seed_results]
        )

        std_f1 = np.std(
            [x["f1"] for x in seed_results]
        )

        results.append(
            {
                "name": feature_set_name,
                "features": len(feature_indices),
                "accuracy": mean_accuracy,
                "precision": mean_precision,
                "recall": mean_recall,
                "f1": mean_f1,
                "fpr": mean_fpr,
                "f1_std": std_f1,
            }
        )

    # ========================================================
    # Sort by F1
    # ========================================================

    results.sort(
        key=lambda x: x["f1"],
        reverse=True,
    )

    # ========================================================
    # Print results
    # ========================================================

    print(
        "Feature Set                 N     Accuracy  "
        "Precision  Recall    F1       FPR"
    )

    print("-" * 90)

    for result in results:

        print(
            f"{result['name']:26} "
            f"{result['features']:2d}    "
            f"{result['accuracy']:.4f}    "
            f"{result['precision']:.4f}     "
            f"{result['recall']:.4f}   "
            f"{result['f1']:.4f}   "
            f"{result['fpr']:.4f}"
        )

    # ========================================================
    # Best configuration
    # ========================================================

    acceptable = [
        x
        for x in results
        if x["fpr"] <= 0.15
    ]

    if acceptable:

        best = max(
            acceptable,
            key=lambda x: x["f1"],
        )

    else:

        best = results[0]

    print()
    print("=== BEST DEVELOPMENT CONFIGURATION ===")

    print(
        f"Feature set : {best['name']}"
    )

    print(
        f"Features    : {best['features']}"
    )

    print(
        f"Accuracy    : {best['accuracy']:.4f}"
    )

    print(
        f"Precision   : {best['precision']:.4f}"
    )

    print(
        f"Recall      : {best['recall']:.4f}"
    )

    print(
        f"F1          : {best['f1']:.4f}"
    )

    print(
        f"FPR         : {best['fpr']:.4f}"
    )

    print(
        f"F1 std      : {best['f1_std']:.4f}"
    )

    print()
    print(
        "IMPORTANT:"
    )
    print(
        "The independent holdout was NOT used."
    )
    print(
        "Only use the holdout after selecting the feature set."
    )


if __name__ == "__main__":
    main()
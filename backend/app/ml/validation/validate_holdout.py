import numpy as np

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

TRAIN_PATH = "data/ml_validation/train_normal.npy"
CALIBRATION_PATH = "data/ml_validation/calibration_normal.npy"
HOLDOUT_NORMAL_PATH = "data/ml_validation/holdout_normal.npy"
HOLDOUT_ANOMALY_PATH = "data/ml_validation/holdout_anomaly.npy"

N_ESTIMATORS = 300
CONTAMINATION = 0.05
TARGET_FPR = 0.10

SEED = 42

# behavioral_14
FEATURE_INDICES = [
    0, 1, 2,
    7, 8, 9, 10, 11,
    12, 13, 14, 15, 16, 17,
]

FEATURE_NAMES = [
    "process_creation",
    "process_termination",
    "unique_processes",
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


def transform(
    data: np.ndarray,
) -> np.ndarray:

    data = np.asarray(
        data,
        dtype=float,
    ).copy()

    for index in LOG_FEATURES:
        if index in FEATURE_INDICES:
            column = FEATURE_INDICES.index(index)

            data[:, column] = np.log1p(
                np.maximum(
                    data[:, column],
                    0,
                )
            )

    return data


def main():

    train = np.load(TRAIN_PATH)
    calibration_normal = np.load(CALIBRATION_PATH)
    holdout_normal = np.load(HOLDOUT_NORMAL_PATH)
    holdout_anomaly = np.load(HOLDOUT_ANOMALY_PATH)

    # --------------------------------------------------
    # Select features
    # --------------------------------------------------

    train_selected = train[:, FEATURE_INDICES]
    calibration_selected = calibration_normal[:, FEATURE_INDICES]
    normal_selected = holdout_normal[:, FEATURE_INDICES]
    anomaly_selected = holdout_anomaly[:, FEATURE_INDICES]

    # --------------------------------------------------
    # Transform
    # --------------------------------------------------

    train_transformed = transform(train_selected)
    calibration_transformed = transform(calibration_selected)
    normal_transformed = transform(normal_selected)
    anomaly_transformed = transform(anomaly_selected)

    # --------------------------------------------------
    # Scale
    # --------------------------------------------------

    scaler = RobustScaler()

    train_scaled = scaler.fit_transform(
        train_transformed
    )

    calibration_scaled = scaler.transform(
        calibration_transformed
    )

    normal_scaled = scaler.transform(
        normal_transformed
    )

    anomaly_scaled = scaler.transform(
        anomaly_transformed
    )

    # --------------------------------------------------
    # Train
    # --------------------------------------------------

    model = IsolationForest(
        contamination=CONTAMINATION,
        n_estimators=N_ESTIMATORS,
        random_state=SEED,
        n_jobs=-1,
    )

    model.fit(train_scaled)

    # --------------------------------------------------
    # Calibrate threshold using NORMAL calibration only
    # --------------------------------------------------

    calibration_scores = model.score_samples(
        calibration_scaled
    )

    threshold = float(
        np.quantile(
            calibration_scores,
            TARGET_FPR,
        )
    )

    # --------------------------------------------------
    # Independent holdout
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Metrics
    # --------------------------------------------------

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

    cm = confusion_matrix(
        y_true,
        y_pred,
    )

    tn, fp, fn, tp = cm.ravel()

    fpr = fp / (fp + tn)

    # --------------------------------------------------
    # Results
    # --------------------------------------------------

    print()
    print("# KATANA BEHAVIORAL-14 INDEPENDENT HOLDOUT")
    print("=" * 58)

    print(f"Training normal     : {len(train)}")
    print(f"Calibration normal  : {len(calibration_normal)}")
    print(f"Holdout normal      : {len(holdout_normal)}")
    print(f"Holdout anomalies   : {len(holdout_anomaly)}")
    print()
    print(f"Feature set         : behavioral_14")
    print(f"Features            : {len(FEATURE_INDICES)}")
    print(f"Estimators          : {N_ESTIMATORS}")
    print(f"Contamination       : {CONTAMINATION}")
    print(f"Calibration FPR     : {TARGET_FPR}")
    print(f"Seed                : {SEED}")
    print(f"Threshold           : {threshold:.6f}")

    print()
    print("Selected features:")
    for index, name in zip(
        FEATURE_INDICES,
        FEATURE_NAMES,
    ):
        print(f"  {index:2d}  {name}")

    print()
    print("=== HOLDOUT SCORE DISTRIBUTION ===")

    print(
        f"Normal mean         : "
        f"{normal_scores.mean():.6f}"
    )

    print(
        f"Anomaly mean        : "
        f"{anomaly_scores.mean():.6f}"
    )

    print(
        f"Normal below        : "
        f"{np.mean(normal_scores <= threshold):.4f}"
    )

    print(
        f"Anomaly below       : "
        f"{np.mean(anomaly_scores <= threshold):.4f}"
    )

    print()
    print("=== METRICS ===")

    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1 Score : {f1:.4f}")
    print(f"FPR      : {fpr:.4f}")

    print()
    print("=== CONFUSION MATRIX ===")
    print(cm)

    print()
    print("=== CLASSIFICATION REPORT ===")

    print(
        classification_report(
            y_true,
            y_pred,
            target_names=[
                "Normal",
                "Anomaly",
            ],
            zero_division=0,
        )
    )

    print("=== INTERPRETATION ===")

    print(f"True negatives : {tn}")
    print(f"False positives: {fp}")
    print(f"False negatives: {fn}")
    print(f"True positives : {tp}")


if __name__ == "__main__":
    main()
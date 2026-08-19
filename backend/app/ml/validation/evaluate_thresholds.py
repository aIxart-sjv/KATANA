import numpy as np

from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
)

from app.feature_engine.features import BehaviorFeatures
from app.ml.features_to_vector import to_vector
from app.ml.model import BehaviorModel


DATA_DIR = "data/ml_validation"

# ============================================================
# Configuration
# ============================================================

TRAIN_NORMAL_SIZE = 600

TARGET_FPR_PRIMARY = 0.05
TARGET_FPR_FALLBACK = 0.10

EXPECTED_RAW_FEATURES = 18
EXPECTED_PRODUCTION_FEATURES = 28


# ============================================================
# Raw feature -> BehaviorFeatures
# ============================================================

def raw_sample_to_behavior_features(
    sample: np.ndarray,
) -> BehaviorFeatures:
    """
    Convert one raw 18-dimensional validation sample into
    the exact BehaviorFeatures structure used by production.

    Raw feature order MUST remain synchronized with the
    validation dataset generation process.

    Feature order:

        0   process_creation_rate
        1   process_termination_rate
        2   unique_process_count
        3   average_cpu
        4   maximum_cpu
        5   average_memory
        6   maximum_memory
        7   external_connections
        8   failed_logins
        9   privilege_escalations
        10  filesystem_modifications
        11  service_restarts
        12  kernel_exec_count
        13  kernel_connect_count
        14  kernel_open_count
        15  kernel_unlink_count
        16  kernel_setuid_count
        17  kernel_ptrace_count
    """

    sample = np.asarray(
        sample,
        dtype=float,
    )

    if sample.ndim != 1:
        raise ValueError(
            "Expected a one-dimensional raw sample, "
            f"got shape {sample.shape}"
        )

    if len(sample) != EXPECTED_RAW_FEATURES:
        raise ValueError(
            "Expected "
            f"{EXPECTED_RAW_FEATURES} raw features, "
            f"got {len(sample)}"
        )

    return BehaviorFeatures(
        process_creation_rate=float(sample[0]),
        process_termination_rate=float(sample[1]),
        unique_process_count=int(sample[2]),

        average_cpu=float(sample[3]),
        maximum_cpu=float(sample[4]),

        average_memory=float(sample[5]),
        maximum_memory=float(sample[6]),

        external_connections=int(sample[7]),

        failed_logins=int(sample[8]),
        privilege_escalations=int(sample[9]),

        filesystem_modifications=int(sample[10]),
        service_restarts=int(sample[11]),

        kernel_exec_count=int(sample[12]),
        kernel_connect_count=int(sample[13]),
        kernel_open_count=int(sample[14]),
        kernel_unlink_count=int(sample[15]),
        kernel_setuid_count=int(sample[16]),
        kernel_ptrace_count=int(sample[17]),
    )


# ============================================================
# Production feature conversion
# ============================================================

def convert_to_28_features(
    data: np.ndarray,
) -> np.ndarray:
    """
    Convert raw 18-dimensional validation data into the exact
    28-dimensional production representation.

    Validation pipeline:

        18 raw features
                ↓
        BehaviorFeatures
                ↓
        to_vector()
                ↓
        28 production features

    This intentionally uses the same feature-engineering
    function as the production pipeline.
    """

    data = np.asarray(
        data,
        dtype=float,
    )

    if data.ndim != 2:
        raise ValueError(
            f"Expected 2D array, got shape {data.shape}"
        )

    if data.shape[1] != EXPECTED_RAW_FEATURES:
        raise ValueError(
            "Expected "
            f"{EXPECTED_RAW_FEATURES} raw features, "
            f"got {data.shape[1]}"
        )

    converted = []

    for sample in data:

        features = raw_sample_to_behavior_features(
            sample
        )

        vector = to_vector(
            features
        )

        if len(vector) != EXPECTED_PRODUCTION_FEATURES:
            raise RuntimeError(
                "Production feature engineering returned "
                f"{len(vector)} features instead of "
                f"{EXPECTED_PRODUCTION_FEATURES}."
            )

        converted.append(
            vector
        )

    result = np.asarray(
        converted,
        dtype=float,
    )

    expected_shape = (
        len(data),
        EXPECTED_PRODUCTION_FEATURES,
    )

    if result.shape != expected_shape:
        raise RuntimeError(
            "Production feature conversion produced "
            f"shape {result.shape}; expected "
            f"{expected_shape}."
        )

    return result


# ============================================================
# Dataset loading
# ============================================================

def load_validation_data():
    """
    Load all validation datasets and convert them through the
    exact production feature-engineering pipeline.

    Dataset split:

        train_normal.npy
            ├── first 600 -> model training
            └── remaining 300 -> threshold calibration

        train_anomaly.npy
            └── calibration anomaly data

        holdout_normal.npy
            └── independent evaluation

        holdout_anomaly.npy
            └── independent evaluation

    IMPORTANT:

        Holdout data is never used for threshold selection.
    """

    train_normal_raw = np.load(
        f"{DATA_DIR}/train_normal.npy"
    )

    train_anomaly_raw = np.load(
        f"{DATA_DIR}/train_anomaly.npy"
    )

    holdout_normal_raw = np.load(
        f"{DATA_DIR}/holdout_normal.npy"
    )

    holdout_anomaly_raw = np.load(
        f"{DATA_DIR}/holdout_anomaly.npy"
    )

    print(
        f"Train normal raw       : "
        f"{train_normal_raw.shape}"
    )

    print(
        f"Train anomaly raw      : "
        f"{train_anomaly_raw.shape}"
    )

    print(
        f"Holdout normal raw     : "
        f"{holdout_normal_raw.shape}"
    )

    print(
        f"Holdout anomaly raw    : "
        f"{holdout_anomaly_raw.shape}"
    )

    # --------------------------------------------------------
    # Validate dataset dimensions.
    # --------------------------------------------------------

    datasets = {
        "train_normal": train_normal_raw,
        "train_anomaly": train_anomaly_raw,
        "holdout_normal": holdout_normal_raw,
        "holdout_anomaly": holdout_anomaly_raw,
    }

    for name, dataset in datasets.items():

        if dataset.ndim != 2:
            raise ValueError(
                f"{name} must be 2D, "
                f"got shape {dataset.shape}"
            )

        if dataset.shape[1] != EXPECTED_RAW_FEATURES:
            raise ValueError(
                f"{name} must contain "
                f"{EXPECTED_RAW_FEATURES} features, "
                f"got {dataset.shape[1]}"
            )

    if len(train_normal_raw) <= TRAIN_NORMAL_SIZE:
        raise ValueError(
            "train_normal.npy must contain more than "
            f"{TRAIN_NORMAL_SIZE} samples so that both "
            "training and calibration data exist."
        )

    # --------------------------------------------------------
    # Split normal data.
    #
    # First 600:
    #     model training
    #
    # Remaining 300:
    #     threshold calibration
    #
    # Calibration normals MUST NOT be used for fitting.
    # --------------------------------------------------------

    train_normal_raw_split = (
        train_normal_raw[
            :TRAIN_NORMAL_SIZE
        ]
    )

    calibration_normal_raw = (
        train_normal_raw[
            TRAIN_NORMAL_SIZE:
        ]
    )

    # --------------------------------------------------------
    # Production feature conversion.
    # --------------------------------------------------------

    train_normal = convert_to_28_features(
        train_normal_raw_split
    )

    calibration_normal = convert_to_28_features(
        calibration_normal_raw
    )

    calibration_anomaly = convert_to_28_features(
        train_anomaly_raw
    )

    holdout_normal = convert_to_28_features(
        holdout_normal_raw
    )

    holdout_anomaly = convert_to_28_features(
        holdout_anomaly_raw
    )

    print()

    print(
        f"Train normal production       : "
        f"{train_normal.shape}"
    )

    print(
        f"Calibration normal production : "
        f"{calibration_normal.shape}"
    )

    print(
        f"Calibration anomaly production: "
        f"{calibration_anomaly.shape}"
    )

    print(
        f"Holdout normal production     : "
        f"{holdout_normal.shape}"
    )

    print(
        f"Holdout anomaly production    : "
        f"{holdout_anomaly.shape}"
    )

    return (
        train_normal,
        calibration_normal,
        calibration_anomaly,
        holdout_normal,
        holdout_anomaly,
    )


# ============================================================
# Score generation
# ============================================================

def get_scores(
    model: BehaviorModel,
    data: np.ndarray,
) -> np.ndarray:
    """
    Generate anomaly scores using the production BehaviorModel.

    Lower scores indicate more anomalous behavior.
    """

    scores = []

    for sample in data:

        score = model.score(
            sample.tolist()
        )

        scores.append(
            float(score)
        )

    return np.asarray(
        scores,
        dtype=float,
    )


# ============================================================
# Threshold evaluation
# ============================================================

def evaluate_threshold(
    normal_scores: np.ndarray,
    anomaly_scores: np.ndarray,
    threshold: float,
):
    """
    Evaluate a single anomaly threshold.

    Classification rule:

        score <= threshold
            -> anomaly

        score > threshold
            -> normal
    """

    normal_scores = np.asarray(
        normal_scores,
        dtype=float,
    )

    anomaly_scores = np.asarray(
        anomaly_scores,
        dtype=float,
    )

    y_true = np.concatenate(
        [
            np.zeros(
                len(normal_scores),
                dtype=int,
            ),
            np.ones(
                len(anomaly_scores),
                dtype=int,
            ),
        ]
    )

    y_pred = np.concatenate(
        [
            normal_scores <= threshold,
            anomaly_scores <= threshold,
        ]
    ).astype(int)

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    )

    if matrix.shape != (2, 2):
        raise RuntimeError(
            "Expected a 2x2 confusion matrix, "
            f"got {matrix.shape}."
        )

    tn, fp, fn, tp = matrix.ravel()

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

    fpr = (
        fp / (fp + tn)
        if (fp + tn) > 0
        else 0.0
    )

    return {
        "threshold": float(threshold),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "fpr": float(fpr),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


# ============================================================
# Score distribution
# ============================================================

def print_score_distribution(
    name: str,
    scores: np.ndarray,
):
    """
    Print useful statistics for an anomaly-score distribution.
    """

    scores = np.asarray(
        scores,
        dtype=float,
    )

    if len(scores) == 0:
        raise ValueError(
            f"Cannot print score distribution for "
            f"empty dataset: {name}"
        )

    print()
    print(name)
    print("-" * 80)

    print(
        f"  min    : {scores.min():.6f}"
    )

    print(
        f"  5%     : "
        f"{np.quantile(scores, 0.05):.6f}"
    )

    print(
        f"  median : "
        f"{np.median(scores):.6f}"
    )

    print(
        f"  95%    : "
        f"{np.quantile(scores, 0.95):.6f}"
    )

    print(
        f"  max    : {scores.max():.6f}"
    )


# ============================================================
# Threshold candidate generation
# ============================================================

def generate_threshold_candidates(
    normal_scores: np.ndarray,
    anomaly_scores: np.ndarray,
) -> np.ndarray:
    """
    Generate threshold candidates from the actual calibration
    score distribution.

    A threshold is placed between every pair of consecutive
    unique scores.

    This is preferable to an arbitrary fixed grid because
    each candidate represents a distinct classification state
    in the calibration dataset.
    """

    scores = np.concatenate(
        [
            np.asarray(
                normal_scores,
                dtype=float,
            ),
            np.asarray(
                anomaly_scores,
                dtype=float,
            ),
        ]
    )

    if len(scores) == 0:
        raise ValueError(
            "Cannot generate thresholds from empty scores."
        )

    unique_scores = np.unique(
        np.sort(scores)
    )

    if len(unique_scores) == 1:

        return unique_scores.copy()

    thresholds = (
        unique_scores[:-1]
        + unique_scores[1:]
    ) / 2.0

    lower_boundary = (
        unique_scores[0] - 1e-9
    )

    upper_boundary = (
        unique_scores[-1] + 1e-9
    )

    return np.concatenate(
        [
            np.asarray(
                [lower_boundary],
                dtype=float,
            ),
            thresholds,
            np.asarray(
                [upper_boundary],
                dtype=float,
            ),
        ]
    )


# ============================================================
# Threshold selection
# ============================================================

def select_threshold(
    normal_scores: np.ndarray,
    anomaly_scores: np.ndarray,
):
    """
    Select the operating threshold using calibration data.

    Priority:

        1. FPR <= 5%
        2. Within that constraint, maximize recall
        3. Maximize F1
        4. Maximize precision

    Fallback:

        FPR <= 10%

    Final fallback:

        Best F1.
    """

    thresholds = generate_threshold_candidates(
        normal_scores,
        anomaly_scores,
    )

    results = [
        evaluate_threshold(
            normal_scores=normal_scores,
            anomaly_scores=anomaly_scores,
            threshold=threshold,
        )
        for threshold in thresholds
    ]

    acceptable_primary = [
        result
        for result in results
        if result["fpr"] <= TARGET_FPR_PRIMARY
    ]

    acceptable_fallback = [
        result
        for result in results
        if result["fpr"] <= TARGET_FPR_FALLBACK
    ]

    if acceptable_primary:

        best = max(
            acceptable_primary,
            key=lambda result: (
                result["recall"],
                result["f1"],
                result["precision"],
            ),
        )

        selection_rule = (
            "FPR <= 5%; maximize recall"
        )

    elif acceptable_fallback:

        best = max(
            acceptable_fallback,
            key=lambda result: (
                result["recall"],
                result["f1"],
                result["precision"],
            ),
        )

        selection_rule = (
            "FPR <= 10% fallback; maximize recall"
        )

    else:

        best = max(
            results,
            key=lambda result: (
                result["f1"],
                result["recall"],
                result["precision"],
            ),
        )

        selection_rule = (
            "Best F1 fallback"
        )

    return (
        best,
        results,
        selection_rule,
    )


# ============================================================
# Threshold benchmark printing
# ============================================================

def print_threshold_benchmark(
    results: list[dict],
):
    """
    Print a compact and useful threshold benchmark.

    The full candidate space can contain hundreds or thousands
    of thresholds. Dumping all of them is unnecessary.

    We therefore display:

        - all candidates with FPR <= 5%
        - candidates close to the 5% boundary
        - candidates close to the 10% boundary
    """

    print()
    print(
        f"{'Threshold':>12} "
        f"{'Precision':>11} "
        f"{'Recall':>10} "
        f"{'F1':>10} "
        f"{'FPR':>10}"
    )

    print("-" * 65)

    displayed = set()

    for result in results:

        fpr = result["fpr"]

        should_display = (
            fpr <= TARGET_FPR_PRIMARY
            or abs(
                fpr - TARGET_FPR_PRIMARY
            ) < 0.005
            or abs(
                fpr - TARGET_FPR_FALLBACK
            ) < 0.005
        )

        if not should_display:
            continue

        threshold_key = round(
            result["threshold"],
            6,
        )

        if threshold_key in displayed:
            continue

        displayed.add(
            threshold_key
        )

        print(
            f"{result['threshold']:12.6f} "
            f"{result['precision']:11.4f} "
            f"{result['recall']:10.4f} "
            f"{result['f1']:10.4f} "
            f"{result['fpr']:10.4f}"
        )


# ============================================================
# Confusion matrix printing
# ============================================================

def print_confusion_matrix(
    result: dict,
):
    """
    Print a confusion matrix in KATANA's expected format.
    """

    print(
        np.array(
            [
                [
                    result["tn"],
                    result["fp"],
                ],
                [
                    result["fn"],
                    result["tp"],
                ],
            ]
        )
    )


# ============================================================
# Main validation
# ============================================================

def main():

    print()
    print("=" * 80)
    print("KATANA ML THRESHOLD VALIDATION")
    print("=" * 80)
    print()

    print(
        "Production pipeline:"
    )

    print(
        "18 raw features"
        " -> BehaviorFeatures"
        " -> to_vector()"
        " -> 28 features"
        " -> log transform"
        " -> RobustScaler"
        " -> Isolation Forest"
    )

    # --------------------------------------------------------
    # Load and convert datasets.
    # --------------------------------------------------------

    (
        train_normal,
        calibration_normal,
        calibration_anomaly,
        holdout_normal,
        holdout_anomaly,
    ) = load_validation_data()

    # --------------------------------------------------------
    # Dataset split summary.
    # --------------------------------------------------------

    print()
    print("DATA SPLIT")
    print("-" * 80)

    print(
        f"Model training normal     : "
        f"{len(train_normal)}"
    )

    print(
        f"Calibration normal        : "
        f"{len(calibration_normal)}"
    )

    print(
        f"Calibration anomaly       : "
        f"{len(calibration_anomaly)}"
    )

    print(
        f"Holdout normal            : "
        f"{len(holdout_normal)}"
    )

    print(
        f"Holdout anomaly           : "
        f"{len(holdout_anomaly)}"
    )

    # --------------------------------------------------------
    # Train model ONLY on training normal samples.
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("TRAINING BEHAVIOR MODEL")
    print("=" * 80)

    print(
        "Training using normal behavior only..."
    )

    model = BehaviorModel()

    model.train(
        train_normal.tolist()
    )

    print(
        "Model trained successfully."
    )

    # --------------------------------------------------------
    # Calibration.
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("CALIBRATION")
    print("=" * 80)

    print(
        "Generating calibration scores..."
    )

    calibration_normal_scores = get_scores(
        model,
        calibration_normal,
    )

    calibration_anomaly_scores = get_scores(
        model,
        calibration_anomaly,
    )

    # --------------------------------------------------------
    # Score distributions.
    # --------------------------------------------------------

    print()
    print("SCORE DISTRIBUTION")
    print("-" * 80)

    print_score_distribution(
        "Normal calibration scores:",
        calibration_normal_scores,
    )

    print_score_distribution(
        "Anomaly calibration scores:",
        calibration_anomaly_scores,
    )

    # --------------------------------------------------------
    # Select threshold.
    # --------------------------------------------------------

    print()
    print("THRESHOLD SEARCH")
    print("-" * 80)

    (
        best,
        results,
        selection_rule,
    ) = select_threshold(
        normal_scores=calibration_normal_scores,
        anomaly_scores=calibration_anomaly_scores,
    )

    # --------------------------------------------------------
    # Benchmark.
    # --------------------------------------------------------

    print_threshold_benchmark(
        results
    )

    # --------------------------------------------------------
    # Selected calibration threshold.
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("SELECTED CALIBRATION THRESHOLD")
    print("=" * 80)

    print(
        f"Selection rule : "
        f"{selection_rule}"
    )

    print(
        f"Threshold      : "
        f"{best['threshold']:.6f}"
    )

    print(
        f"Precision      : "
        f"{best['precision']:.4f}"
    )

    print(
        f"Recall         : "
        f"{best['recall']:.4f}"
    )

    print(
        f"F1             : "
        f"{best['f1']:.4f}"
    )

    print(
        f"FPR            : "
        f"{best['fpr']:.4f}"
    )

    print()
    print(
        "Calibration Confusion Matrix:"
    )

    print_confusion_matrix(
        best
    )

    # --------------------------------------------------------
    # Independent holdout evaluation.
    #
    # The holdout set has never been used for:
    #
    #   - model training
    #   - threshold selection
    #   - threshold optimization
    #
    # Therefore this is the important generalization test.
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("INDEPENDENT HOLDOUT EVALUATION")
    print("=" * 80)

    print(
        "The holdout data is completely excluded "
        "from model tuning and threshold selection."
    )

    print()
    print(
        "Generating holdout scores..."
    )

    holdout_normal_scores = get_scores(
        model,
        holdout_normal,
    )

    holdout_anomaly_scores = get_scores(
        model,
        holdout_anomaly,
    )

    holdout_result = evaluate_threshold(
        normal_scores=holdout_normal_scores,
        anomaly_scores=holdout_anomaly_scores,
        threshold=best["threshold"],
    )

    print()

    print(
        f"Threshold : "
        f"{holdout_result['threshold']:.6f}"
    )

    print(
        f"Precision : "
        f"{holdout_result['precision']:.4f}"
    )

    print(
        f"Recall    : "
        f"{holdout_result['recall']:.4f}"
    )

    print(
        f"F1        : "
        f"{holdout_result['f1']:.4f}"
    )

    print(
        f"FPR       : "
        f"{holdout_result['fpr']:.4f}"
    )

    print()
    print(
        "Holdout Confusion Matrix:"
    )

    print_confusion_matrix(
        holdout_result
    )

    # --------------------------------------------------------
    # Generalization comparison.
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("GENERALIZATION CHECK")
    print("=" * 80)

    print(
        f"{'Metric':<15}"
        f"{'Calibration':>15}"
        f"{'Holdout':>15}"
        f"{'Difference':>15}"
    )

    print("-" * 60)

    metrics = [
        ("Precision", "precision"),
        ("Recall", "recall"),
        ("F1", "f1"),
        ("FPR", "fpr"),
    ]

    for label, key in metrics:

        calibration_value = (
            best[key]
        )

        holdout_value = (
            holdout_result[key]
        )

        difference = (
            holdout_value
            - calibration_value
        )

        print(
            f"{label:<15}"
            f"{calibration_value:>15.4f}"
            f"{holdout_value:>15.4f}"
            f"{difference:>15.4f}"
        )

    # --------------------------------------------------------
    # Final validation summary.
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("KATANA VALIDATION SUMMARY")
    print("=" * 80)

    print(
        f"Selected threshold : "
        f"{best['threshold']:.6f}"
    )

    print(
        f"Holdout FPR        : "
        f"{holdout_result['fpr']:.4f}"
    )

    print(
        f"Holdout recall     : "
        f"{holdout_result['recall']:.4f}"
    )

    print(
        f"Holdout precision  : "
        f"{holdout_result['precision']:.4f}"
    )

    print(
        f"Holdout F1         : "
        f"{holdout_result['f1']:.4f}"
    )

    # --------------------------------------------------------
    # Validation decision.
    # --------------------------------------------------------

    print()

    if (
        holdout_result["fpr"]
        <= TARGET_FPR_PRIMARY
    ):

        print(
            "RESULT: PASS"
        )

        print(
            "The calibrated threshold maintained "
            "a holdout false-positive rate <= 5%."
        )

    elif (
        holdout_result["fpr"]
        <= TARGET_FPR_FALLBACK
    ):

        print(
            "RESULT: WARNING"
        )

        print(
            "The threshold generalized below 10% FPR "
            "but did not meet the preferred 5% target."
        )

    else:

        print(
            "RESULT: FAIL"
        )

        print(
            "The threshold produces more than 10% "
            "false positives on independent data."
        )

    # --------------------------------------------------------
    # Production decision.
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("PRODUCTION DECISION")
    print("=" * 80)

    if (
        holdout_result["fpr"]
        <= TARGET_FPR_PRIMARY
    ):

        print(
            "Validation target satisfied."
        )

        print(
            "The calibrated threshold may be considered "
            "for controlled production integration."
        )

        print()
        print(
            f"Candidate production threshold: "
            f"{best['threshold']:.6f}"
        )

        print()
        print(
            "IMPORTANT:"
        )

        print(
            "Do not hard-code this value blindly."
        )

        print(
            "Verify that AnomalyEngine uses the same "
            "score direction and the same preprocessing "
            "pipeline before deployment."
        )

    else:

        print(
            "DO NOT deploy this threshold."
        )

        print(
            "Further calibration, feature engineering, "
            "or model improvements are required."
        )

    print()


if __name__ == "__main__":
    main()
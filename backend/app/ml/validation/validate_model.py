import numpy as np

from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


NORMAL_PATH = "data/ml_validation/normal.npy"
ANOMALY_PATH = "data/ml_validation/anomaly.npy"

TRAIN_SIZE = 600


def evaluate_model(
    train_normal,
    test_normal,
    test_anomaly,
    contamination,
    n_estimators,
):
    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=n_estimators,
    )

    model.fit(train_normal)

    # ---------------------------------------------------------
    # Build test set
    # ---------------------------------------------------------

    test_data = np.concatenate(
        [
            test_normal,
            test_anomaly,
        ]
    )

    y_true = np.concatenate(
        [
            np.zeros(len(test_normal), dtype=int),
            np.ones(len(test_anomaly), dtype=int),
        ]
    )

    # Isolation Forest:
    #   1  = normal
    #  -1  = anomaly
    predictions = model.predict(test_data)

    y_pred = (predictions == -1).astype(int)

    # ---------------------------------------------------------
    # Metrics
    # ---------------------------------------------------------

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

    matrix = confusion_matrix(
        y_true,
        y_pred,
    )

    tn, fp, fn, tp = matrix.ravel()

    false_positive_rate = fp / (fp + tn)

    return {
        "contamination": contamination,
        "n_estimators": n_estimators,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": false_positive_rate,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
    }


def main():

    # ---------------------------------------------------------
    # Load fixed dataset
    # ---------------------------------------------------------

    normal = np.load(NORMAL_PATH)
    anomalies = np.load(ANOMALY_PATH)

    train_normal = normal[:TRAIN_SIZE]

    test_normal = normal[TRAIN_SIZE:]
    test_anomaly = anomalies

    print("==============================================")
    print("        KATANA ML VALIDATION BENCHMARK")
    print("==============================================")
    print()
    print(f"Total normal samples : {len(normal)}")
    print(f"Total anomaly samples: {len(anomalies)}")
    print(f"Training samples     : {len(train_normal)}")
    print(f"Normal test samples  : {len(test_normal)}")
    print(f"Anomaly test samples : {len(test_anomaly)}")
    print()

    # ---------------------------------------------------------
    # Configurations
    # ---------------------------------------------------------

    contamination_values = [
        "auto",
        0.01,
        0.02,
        0.05,
        0.10,
    ]

    estimator_values = [
        100,
        200,
        300,
    ]

    results = []

    # ---------------------------------------------------------
    # Run benchmark
    # ---------------------------------------------------------

    for contamination in contamination_values:

        for n_estimators in estimator_values:

            result = evaluate_model(
                train_normal=train_normal,
                test_normal=test_normal,
                test_anomaly=test_anomaly,
                contamination=contamination,
                n_estimators=n_estimators,
            )

            results.append(result)

    # ---------------------------------------------------------
    # Sort by F1
    # ---------------------------------------------------------

    results.sort(
        key=lambda x: x["f1"],
        reverse=True,
    )

    # ---------------------------------------------------------
    # Print results
    # ---------------------------------------------------------

    print("==============================================")
    print("                 RESULTS")
    print("==============================================")
    print()

    print(
        f"{'Contam':>8} "
        f"{'Trees':>7} "
        f"{'Accuracy':>9} "
        f"{'Precision':>10} "
        f"{'Recall':>9} "
        f"{'F1':>9} "
        f"{'FPR':>9}"
    )

    print("-" * 70)

    for result in results:

        print(
            f"{str(result['contamination']):>8} "
            f"{result['n_estimators']:>7} "
            f"{result['accuracy']:>9.4f} "
            f"{result['precision']:>10.4f} "
            f"{result['recall']:>9.4f} "
            f"{result['f1']:>9.4f} "
            f"{result['false_positive_rate']:>9.4f}"
        )

    # ---------------------------------------------------------
    # Best configuration
    # ---------------------------------------------------------

    best = results[0]

    print()
    print("==============================================")
    print("             BEST CONFIGURATION")
    print("==============================================")

    print(
        f"Contamination : {best['contamination']}"
    )

    print(
        f"Estimators    : {best['n_estimators']}"
    )

    print(
        f"Accuracy      : {best['accuracy']:.4f}"
    )

    print(
        f"Precision     : {best['precision']:.4f}"
    )

    print(
        f"Recall        : {best['recall']:.4f}"
    )

    print(
        f"F1 Score      : {best['f1']:.4f}"
    )

    print(
        f"False Positive: {best['false_positive_rate']:.4f}"
    )

    print()
    print("Confusion Matrix:")
    print(
        np.array(
            [
                [best["tn"], best["fp"]],
                [best["fn"], best["tp"]],
            ]
        )
    )

    print()
    print("Interpretation:")
    print(
        f"True negatives : {best['tn']}"
    )
    print(
        f"False positives: {best['fp']}"
    )
    print(
        f"False negatives: {best['fn']}"
    )
    print(
        f"True positives : {best['tp']}"
    )


if __name__ == "__main__":
    main()
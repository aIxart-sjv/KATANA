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
LABEL_PATH = "data/ml_validation/attack_labels.npy"

TRAIN_SIZE = 600

CONTAMINATION = 0.10
N_ESTIMATORS = 300

SEEDS = [42, 123, 456, 789, 999]


def evaluate_model(
    normal: np.ndarray,
    anomaly: np.ndarray,
    attack_labels: np.ndarray,
    seed: int,
):
    train_normal = normal[:TRAIN_SIZE]

    test_normal = normal[TRAIN_SIZE:]

    model = IsolationForest(
        contamination=CONTAMINATION,
        n_estimators=N_ESTIMATORS,
        random_state=seed,
    )

    # Train ONLY on normal behavior.
    model.fit(train_normal)

    # ---------------------------------------------------------
    # Overall test
    # ---------------------------------------------------------

    X_test = np.vstack(
        [
            test_normal,
            anomaly,
        ]
    )

    y_true = np.concatenate(
        [
            np.zeros(len(test_normal), dtype=int),
            np.ones(len(anomaly), dtype=int),
        ]
    )

    predictions = model.predict(X_test)

    # IsolationForest:
    #   1  = normal
    #  -1  = anomaly
    y_pred = (predictions == -1).astype(int)

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

    fpr = fp / (fp + tn)

    # ---------------------------------------------------------
    # Per-attack detection
    # ---------------------------------------------------------

    anomaly_predictions = y_pred[
        len(test_normal):
    ]

    attack_results = {}

    for attack_type in np.unique(attack_labels):

        mask = attack_labels == attack_type

        attack_true = np.ones(
            mask.sum(),
            dtype=int,
        )

        attack_pred = anomaly_predictions[mask]

        attack_recall = recall_score(
            attack_true,
            attack_pred,
            zero_division=0,
        )

        attack_results[attack_type] = {
            "samples": int(mask.sum()),
            "recall": float(attack_recall),
        }

    return {
        "seed": seed,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fpr,
        "matrix": matrix,
        "attack_results": attack_results,
    }


def print_result(result):

    print(
        f"{result['seed']:<8}"
        f"{result['accuracy']:<12.4f}"
        f"{result['precision']:<12.4f}"
        f"{result['recall']:<12.4f}"
        f"{result['f1']:<12.4f}"
        f"{result['fpr']:<12.4f}"
    )


def main():

    normal = np.load(
        NORMAL_PATH,
    )

    anomaly = np.load(
        ANOMALY_PATH,
    )

    attack_labels = np.load(
        LABEL_PATH,
    )

    print()
    print("KATANA ML VALIDATION BENCHMARK")
    print("=" * 70)

    print(
        f"Total normal samples : {len(normal)}"
    )

    print(
        f"Total anomaly samples: {len(anomaly)}"
    )

    print(
        f"Training samples     : {TRAIN_SIZE}"
    )

    print(
        f"Normal test samples  : {len(normal) - TRAIN_SIZE}"
    )

    print(
        f"Anomaly test samples : {len(anomaly)}"
    )

    print()
    print(
        f"Contamination: {CONTAMINATION}"
    )

    print(
        f"Estimators   : {N_ESTIMATORS}"
    )

    print()
    print(
        f"{'Seed':<8}"
        f"{'Accuracy':<12}"
        f"{'Precision':<12}"
        f"{'Recall':<12}"
        f"{'F1':<12}"
        f"{'FPR':<12}"
    )

    print("-" * 70)

    results = []

    for seed in SEEDS:

        result = evaluate_model(
            normal,
            anomaly,
            attack_labels,
            seed,
        )

        results.append(result)

        print_result(result)

    # ---------------------------------------------------------
    # Aggregate results
    # ---------------------------------------------------------

    accuracies = [
        r["accuracy"]
        for r in results
    ]

    precisions = [
        r["precision"]
        for r in results
    ]

    recalls = [
        r["recall"]
        for r in results
    ]

    f1_scores = [
        r["f1"]
        for r in results
    ]

    fprs = [
        r["fpr"]
        for r in results
    ]

    print()
    print("AGGREGATE RESULTS")
    print("-" * 70)

    print(
        f"Accuracy : "
        f"{np.mean(accuracies):.4f} "
        f"+/- {np.std(accuracies):.4f}"
    )

    print(
        f"Precision: "
        f"{np.mean(precisions):.4f} "
        f"+/- {np.std(precisions):.4f}"
    )

    print(
        f"Recall   : "
        f"{np.mean(recalls):.4f} "
        f"+/- {np.std(recalls):.4f}"
    )

    print(
        f"F1       : "
        f"{np.mean(f1_scores):.4f} "
        f"+/- {np.std(f1_scores):.4f}"
    )

    print(
        f"FPR      : "
        f"{np.mean(fprs):.4f} "
        f"+/- {np.std(fprs):.4f}"
    )

    # ---------------------------------------------------------
    # Per attack type
    # ---------------------------------------------------------

    print()
    print("PER-ATTACK DETECTION")
    print("-" * 70)

    attack_types = np.unique(
        attack_labels
    )

    for attack_type in attack_types:

        recalls_for_attack = []

        sample_count = 0

        for result in results:

            attack = result[
                "attack_results"
            ][attack_type]

            recalls_for_attack.append(
                attack["recall"]
            )

            sample_count = attack[
                "samples"
            ]

        print(
            f"{attack_type:<22}"
            f"samples={sample_count:<5}"
            f"recall={np.mean(recalls_for_attack):.4f}"
            f" +/- {np.std(recalls_for_attack):.4f}"
        )

    # ---------------------------------------------------------
    # Best seed
    # ---------------------------------------------------------

    best = max(
        results,
        key=lambda r: r["f1"],
    )

    print()
    print("BEST RUN")
    print("-" * 70)

    print(
        f"Seed      : {best['seed']}"
    )

    print(
        f"Accuracy  : {best['accuracy']:.4f}"
    )

    print(
        f"Precision : {best['precision']:.4f}"
    )

    print(
        f"Recall    : {best['recall']:.4f}"
    )

    print(
        f"F1        : {best['f1']:.4f}"
    )

    print(
        f"FPR       : {best['fpr']:.4f}"
    )

    print()
    print("Confusion Matrix:")
    print(best["matrix"])


if __name__ == "__main__":
    main()
import numpy as np

from app.feature_engine.features import BehaviorFeatures
from app.ml.features_to_vector import to_vector
from app.ml.model import BehaviorModel


DATA_DIR = "data/ml_validation"


def transform_samples(samples: np.ndarray) -> list[list[float]]:
    """
    Convert raw 18-feature samples into KATANA's
    production 28-feature representation.
    """

    transformed = []

    for sample in samples:
        features = BehaviorFeatures(
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

        transformed.append(
            to_vector(features)
        )

    return transformed


def summarize(name, scores):
    print(f"\n{name}")
    print("-" * 60)

    print(f"count : {len(scores)}")
    print(f"mean  : {scores.mean():.6f}")
    print(f"std   : {scores.std():.6f}")
    print(f"min   : {scores.min():.6f}")
    print(f"25%   : {np.percentile(scores, 25):.6f}")
    print(f"50%   : {np.percentile(scores, 50):.6f}")
    print(f"75%   : {np.percentile(scores, 75):.6f}")
    print(f"max   : {scores.max():.6f}")


def main():

    train_normal = np.load(
        f"{DATA_DIR}/train_normal.npy"
    )

    holdout_normal = np.load(
        f"{DATA_DIR}/holdout_normal.npy"
    )

    holdout_anomaly = np.load(
        f"{DATA_DIR}/holdout_anomaly.npy"
    )

    # ==========================================================
    # RAW 18 -> PRODUCTION 28
    # ==========================================================

    train_normal_production = transform_samples(
        train_normal
    )

    holdout_normal_production = transform_samples(
        holdout_normal
    )

    holdout_anomaly_production = transform_samples(
        holdout_anomaly
    )

    # ==========================================================
    # TRAIN
    # ==========================================================

    model = BehaviorModel()

    model.train(
        train_normal_production
    )

    # ==========================================================
    # SCORE
    # ==========================================================

    train_scores = np.array([
        model.score(sample)
        for sample in train_normal_production
    ])

    normal_scores = np.array([
        model.score(sample)
        for sample in holdout_normal_production
    ])

    anomaly_scores = np.array([
        model.score(sample)
        for sample in holdout_anomaly_production
    ])

    # ==========================================================
    # REPORT
    # ==========================================================

    print()
    print("# KATANA ISOLATION FOREST SCORE ANALYSIS")
    print("=" * 60)

    summarize(
        "TRAINING NORMAL",
        train_scores,
    )

    summarize(
        "HOLDOUT NORMAL",
        normal_scores,
    )

    summarize(
        "HOLDOUT ANOMALY",
        anomaly_scores,
    )

    # ==========================================================
    # SCORE OVERLAP
    # ==========================================================

    print()
    print("SCORE OVERLAP")
    print("-" * 60)

    print(
        "Normal 10th percentile:",
        np.percentile(normal_scores, 10),
    )

    print(
        "Normal 50th percentile:",
        np.percentile(normal_scores, 50),
    )

    print(
        "Normal 90th percentile:",
        np.percentile(normal_scores, 90),
    )

    print(
        "Anomaly 10th percentile:",
        np.percentile(anomaly_scores, 10),
    )

    print(
        "Anomaly 50th percentile:",
        np.percentile(anomaly_scores, 50),
    )

    print(
        "Anomaly 90th percentile:",
        np.percentile(anomaly_scores, 90),
    )


if __name__ == "__main__":
    main()
import os

import numpy as np


RNG = np.random.default_rng(42)

OUTPUT_DIR = "data/ml_validation"

N_NORMAL_TRAIN = 1200
N_NORMAL_HOLDOUT = 600
N_ANOMALY_TRAIN = 400
N_ANOMALY_HOLDOUT = 400


def clip(values, low, high):
    return np.clip(values, low, high)


def generate_normal(n: int, rng: np.random.Generator) -> np.ndarray:
    """
    Generate benign system-behavior windows.

    Normal behavior contains:
    - ordinary activity
    - CPU/resource fluctuations
    - occasional authentication failures
    - legitimate privilege operations
    - filesystem activity
    - service restarts
    - normal kernel activity
    """

    process_creation = clip(rng.normal(1.0, 0.65, n), 0, None)
    process_termination = clip(rng.normal(1.0, 0.65, n), 0, None)
    unique_processes = clip(rng.normal(12, 4.5, n), 1, None)

    average_cpu = clip(rng.normal(24, 10, n), 1, 90)

    maximum_cpu = clip(
        average_cpu + rng.normal(15, 10, n),
        average_cpu,
        100,
    )

    average_memory = clip(rng.normal(46, 10, n), 5, 95)

    maximum_memory = clip(
        average_memory + rng.normal(10, 8, n),
        average_memory,
        100,
    )

    external_connections = clip(
        rng.normal(9, 5, n),
        0,
        None,
    )

    failed_logins = rng.poisson(0.15, n)

    privilege_escalations = rng.binomial(
        1,
        0.03,
        n,
    )

    filesystem_modifications = clip(
        rng.normal(3, 1.8, n),
        0,
        None,
    )

    service_restarts = rng.binomial(
        1,
        0.08,
        n,
    )

    kernel_exec = clip(
        rng.normal(8, 3, n),
        0,
        None,
    )

    kernel_connect = clip(
        rng.normal(3, 1.8, n),
        0,
        None,
    )

    kernel_open = clip(
        rng.normal(20, 6, n),
        0,
        None,
    )

    kernel_unlink = clip(
        rng.normal(0.25, 0.5, n),
        0,
        None,
    )

    kernel_setuid = rng.binomial(
        1,
        0.02,
        n,
    )

    kernel_ptrace = rng.binomial(
        1,
        0.01,
        n,
    )

    return np.column_stack(
        [
            process_creation,
            process_termination,
            unique_processes,
            average_cpu,
            maximum_cpu,
            average_memory,
            maximum_memory,
            external_connections,
            failed_logins,
            privilege_escalations,
            filesystem_modifications,
            service_restarts,
            kernel_exec,
            kernel_connect,
            kernel_open,
            kernel_unlink,
            kernel_setuid,
            kernel_ptrace,
        ]
    )


def generate_attack(
    n: int,
    rng: np.random.Generator,
    severity_scale: float,
) -> tuple[np.ndarray, np.ndarray]:

    data = generate_normal(n, rng)

    attack_types = [
        "process_abuse",
        "network_abuse",
        "credential_attack",
        "filesystem_attack",
        "kernel_abuse",
        "mixed_attack",
    ]

    labels = []

    for i in range(n):

        attack_type = rng.choice(attack_types)

        labels.append(attack_type)

        severity = rng.uniform(
            0.6,
            1.4,
        ) * severity_scale

        if attack_type == "process_abuse":

            data[i, 0] += rng.uniform(1.0, 3.5) * severity
            data[i, 1] += rng.uniform(0.5, 2.5) * severity
            data[i, 2] += rng.uniform(4, 15) * severity

            data[i, 4] += rng.uniform(5, 25) * severity

            data[i, 12] += rng.uniform(4, 20) * severity

        elif attack_type == "network_abuse":

            data[i, 7] += rng.uniform(5, 20) * severity
            data[i, 13] += rng.uniform(3, 12) * severity
            data[i, 12] += rng.uniform(3, 15) * severity

        elif attack_type == "credential_attack":

            data[i, 8] += rng.uniform(1, 8) * severity
            data[i, 7] += rng.uniform(2, 12) * severity
            data[i, 0] += rng.uniform(0.5, 2.5) * severity

        elif attack_type == "filesystem_attack":

            data[i, 10] += rng.uniform(5, 25) * severity
            data[i, 14] += rng.uniform(8, 35) * severity
            data[i, 15] += rng.uniform(1, 7) * severity

        elif attack_type == "kernel_abuse":

            data[i, 12] += rng.uniform(10, 45) * severity
            data[i, 13] += rng.uniform(4, 18) * severity
            data[i, 14] += rng.uniform(10, 40) * severity

            if rng.random() < 0.65:
                data[i, 16] += rng.uniform(1, 4) * severity

            if rng.random() < 0.45:
                data[i, 17] += rng.uniform(1, 3) * severity

        elif attack_type == "mixed_attack":

            data[i, 0] += rng.uniform(1, 3) * severity
            data[i, 2] += rng.uniform(4, 18) * severity
            data[i, 7] += rng.uniform(4, 16) * severity
            data[i, 8] += rng.uniform(1, 6) * severity
            data[i, 10] += rng.uniform(4, 18) * severity
            data[i, 12] += rng.uniform(8, 35) * severity

            if rng.random() < 0.5:
                data[i, 16] += rng.uniform(1, 3) * severity

            if rng.random() < 0.35:
                data[i, 17] += rng.uniform(1, 3) * severity

        data[i, 3] = clip(data[i, 3], 0, 100)
        data[i, 4] = clip(data[i, 4], 0, 100)
        data[i, 5] = clip(data[i, 5], 0, 100)
        data[i, 6] = clip(data[i, 6], 0, 100)

    return data, np.array(labels)


def save_dataset():
    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    train_normal = generate_normal(
        N_NORMAL_TRAIN,
        RNG,
    )

    holdout_normal = generate_normal(
        N_NORMAL_HOLDOUT,
        RNG,
    )

    train_anomaly, train_labels = generate_attack(
        N_ANOMALY_TRAIN,
        RNG,
        severity_scale=0.85,
    )

    holdout_anomaly, holdout_labels = generate_attack(
        N_ANOMALY_HOLDOUT,
        RNG,
        severity_scale=1.15,
    )

    np.save(
        os.path.join(
            OUTPUT_DIR,
            "train_normal.npy",
        ),
        train_normal,
    )

    np.save(
        os.path.join(
            OUTPUT_DIR,
            "holdout_normal.npy",
        ),
        holdout_normal,
    )

    np.save(
        os.path.join(
            OUTPUT_DIR,
            "train_anomaly.npy",
        ),
        train_anomaly,
    )

    np.save(
        os.path.join(
            OUTPUT_DIR,
            "holdout_anomaly.npy",
        ),
        holdout_anomaly,
    )

    np.save(
        os.path.join(
            OUTPUT_DIR,
            "train_attack_labels.npy",
        ),
        train_labels,
    )

    np.save(
        os.path.join(
            OUTPUT_DIR,
            "holdout_attack_labels.npy",
        ),
        holdout_labels,
    )

    print("KATANA VALIDATION DATASET")
    print("=" * 40)
    print(f"Training normal  : {len(train_normal)}")
    print(f"Training attacks : {len(train_anomaly)}")
    print(f"Holdout normal   : {len(holdout_normal)}")
    print(f"Holdout attacks  : {len(holdout_anomaly)}")
    print(f"Features/sample  : {train_normal.shape[1]}")
    print(f"Saved to         : {OUTPUT_DIR}")


if __name__ == "__main__":
    save_dataset()
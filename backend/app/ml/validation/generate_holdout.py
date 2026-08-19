import os

import numpy as np


RNG = np.random.default_rng(2026)

OUTPUT_DIR = "data/ml_validation"

N_NORMAL = 600
N_ANOMALY = 400


def clip(values, low, high):
    return np.clip(values, low, high)


def generate_normal(n: int) -> np.ndarray:
    """
    Independent normal-behavior distribution.

    IMPORTANT:
    This intentionally uses different distributions from
    generate_dataset.py so the final evaluation is harder.
    """

    process_creation = clip(
        RNG.normal(1.2, 0.8, n),
        0,
        None,
    )

    process_termination = clip(
        RNG.normal(1.1, 0.75, n),
        0,
        None,
    )

    unique_processes = clip(
        RNG.normal(14, 5.5, n),
        1,
        None,
    )

    average_cpu = clip(
        RNG.normal(28, 13, n),
        1,
        95,
    )

    maximum_cpu = clip(
        average_cpu + RNG.normal(12, 13, n),
        average_cpu,
        100,
    )

    average_memory = clip(
        RNG.normal(50, 13, n),
        5,
        97,
    )

    maximum_memory = clip(
        average_memory + RNG.normal(8, 10, n),
        average_memory,
        100,
    )

    external_connections = clip(
        RNG.normal(11, 6, n),
        0,
        None,
    )

    # More benign variation than the training distribution.
    failed_logins = RNG.poisson(0.25, n)

    privilege_escalations = RNG.binomial(
        1,
        0.05,
        n,
    )

    filesystem_modifications = clip(
        RNG.normal(4, 2.5, n),
        0,
        None,
    )

    service_restarts = RNG.binomial(
        1,
        0.12,
        n,
    )

    kernel_exec = clip(
        RNG.normal(10, 4, n),
        0,
        None,
    )

    kernel_connect = clip(
        RNG.normal(4, 2.5, n),
        0,
        None,
    )

    kernel_open = clip(
        RNG.normal(23, 8, n),
        0,
        None,
    )

    kernel_unlink = RNG.binomial(
        1,
        0.10,
        n,
    ).astype(float)

    kernel_setuid = RNG.binomial(
        1,
        0.04,
        n,
    )

    kernel_ptrace = RNG.binomial(
        1,
        0.02,
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


def generate_anomalies(n: int) -> np.ndarray:
    """
    Generate an independent attack distribution.

    Attack patterns and magnitudes intentionally differ
    from the training/benchmark generator.
    """

    data = generate_normal(n)

    attack_types = [
        "process_abuse",
        "network_abuse",
        "credential_attack",
        "filesystem_attack",
        "kernel_abuse",
        "mixed_attack",
    ]

    for i in range(n):

        attack = RNG.choice(attack_types)

        if attack == "process_abuse":

            data[i, 0] += RNG.uniform(1.0, 3.0)
            data[i, 1] += RNG.uniform(0.5, 2.0)
            data[i, 2] += RNG.uniform(4, 15)

            data[i, 4] += RNG.uniform(8, 25)

            data[i, 12] += RNG.uniform(5, 25)

        elif attack == "network_abuse":

            data[i, 7] += RNG.uniform(5, 18)
            data[i, 13] += RNG.uniform(3, 12)
            data[i, 12] += RNG.uniform(3, 15)

        elif attack == "credential_attack":

            data[i, 8] += RNG.uniform(3, 12)
            data[i, 7] += RNG.uniform(1, 8)

            if RNG.random() < 0.5:
                data[i, 16] += RNG.uniform(0, 2)

        elif attack == "filesystem_attack":

            data[i, 10] += RNG.uniform(6, 25)
            data[i, 14] += RNG.uniform(8, 35)
            data[i, 15] += RNG.uniform(1, 6)

        elif attack == "kernel_abuse":

            data[i, 12] += RNG.uniform(10, 45)
            data[i, 13] += RNG.uniform(4, 18)
            data[i, 14] += RNG.uniform(10, 40)

            if RNG.random() < 0.55:
                data[i, 16] += RNG.uniform(1, 4)

            if RNG.random() < 0.35:
                data[i, 17] += RNG.uniform(1, 3)

        elif attack == "mixed_attack":

            data[i, 0] += RNG.uniform(0.5, 3)
            data[i, 2] += RNG.uniform(3, 15)

            data[i, 7] += RNG.uniform(4, 15)
            data[i, 8] += RNG.uniform(1, 6)

            data[i, 10] += RNG.uniform(4, 18)
            data[i, 12] += RNG.uniform(8, 35)

            if RNG.random() < 0.45:
                data[i, 16] += RNG.uniform(1, 3)

            if RNG.random() < 0.30:
                data[i, 17] += RNG.uniform(1, 3)

        data[i, 3] = clip(data[i, 3], 0, 100)
        data[i, 4] = clip(data[i, 4], 0, 100)
        data[i, 5] = clip(data[i, 5], 0, 100)
        data[i, 6] = clip(data[i, 6], 0, 100)

    return data


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    normal = generate_normal(N_NORMAL)
    anomaly = generate_anomalies(N_ANOMALY)

    np.save(
        os.path.join(
            OUTPUT_DIR,
            "holdout_normal.npy",
        ),
        normal,
    )

    np.save(
        os.path.join(
            OUTPUT_DIR,
            "holdout_anomaly.npy",
        ),
        anomaly,
    )

    print("KATANA INDEPENDENT HOLDOUT DATASET")
    print("=" * 45)
    print(f"Normal samples : {len(normal)}")
    print(f"Anomaly samples: {len(anomaly)}")
    print(f"Features/sample: {normal.shape[1]}")
    print(f"Saved to       : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
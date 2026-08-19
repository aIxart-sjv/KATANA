from app.feature_engine.features import BehaviorFeatures


# ============================================================
# KATANA PRODUCTION FEATURE CONTRACT
# ============================================================
#
# BehaviorFeatures
#       ↓
# 28-dimensional production vector
#
# Feature order:
#
#   0   process_creation_rate
#   1   process_termination_rate
#   2   unique_process_count
#   3   average_cpu
#   4   maximum_cpu
#   5   average_memory
#   6   maximum_memory
#   7   external_connections
#   8   failed_logins
#   9   privilege_escalations
#   10  filesystem_modifications
#   11  service_restarts
#   12  kernel_exec_count
#   13  kernel_connect_count
#   14  kernel_open_count
#   15  kernel_unlink_count
#   16  kernel_setuid_count
#   17  kernel_ptrace_count
#
# Engineered features:
#
#   18  process_activity_ratio
#   19  connections_per_process
#   20  failed_login_ratio
#   21  filesystem_per_process
#   22  exec_per_process
#   23  kernel_connect_ratio
#   24  kernel_open_per_process
#   25  unlink_ratio
#   26  privilege_kernel_interaction
#   27  ptrace_exec_ratio
#
# This order is a STRICT production ML contract.
# Do not reorder features without retraining and revalidating
# the complete model pipeline.
# ============================================================

FEATURE_COUNT = 28


def _safe_divide(
    numerator: float,
    denominator: float,
) -> float:
    """
    Safely divide two values.

    Zero denominators produce zero instead of NaN/inf.

    This is important because legitimate benign behavior can
    contain zero process, login, filesystem, or kernel events.
    """

    if denominator <= 0.0:
        return 0.0

    return numerator / denominator


def to_vector(
    features: BehaviorFeatures,
) -> list[float]:
    """
    Convert BehaviorFeatures into KATANA's 28-dimensional
    production ML feature vector.

    Pipeline:

        BehaviorFeatures
            ↓
        base behavioral features
            ↓
        engineered relationship features
            ↓
        28-dimensional vector

    The returned vector is consumed by BehaviorModel, which
    subsequently performs:

        log1p
            ↓
        RobustScaler
            ↓
        Isolation Forest

    Parameters
    ----------
    features:
        Extracted behavioral features.

    Returns
    -------
    list[float]
        Exactly 28 production ML features.
    """

    if not isinstance(
        features,
        BehaviorFeatures,
    ):
        raise TypeError(
            "to_vector() expects a BehaviorFeatures instance."
        )

    # ============================================================
    # BASE FEATURES
    # ============================================================

    process_creation = float(
        features.process_creation_rate
    )

    process_termination = float(
        features.process_termination_rate
    )

    unique_processes = float(
        features.unique_process_count
    )

    average_cpu = float(
        features.average_cpu
    )

    maximum_cpu = float(
        features.maximum_cpu
    )

    average_memory = float(
        features.average_memory
    )

    maximum_memory = float(
        features.maximum_memory
    )

    external_connections = float(
        features.external_connections
    )

    failed_logins = float(
        features.failed_logins
    )

    privilege_escalations = float(
        features.privilege_escalations
    )

    filesystem_modifications = float(
        features.filesystem_modifications
    )

    service_restarts = float(
        features.service_restarts
    )

    kernel_exec = float(
        features.kernel_exec_count
    )

    kernel_connect = float(
        features.kernel_connect_count
    )

    kernel_open = float(
        features.kernel_open_count
    )

    kernel_unlink = float(
        features.kernel_unlink_count
    )

    kernel_setuid = float(
        features.kernel_setuid_count
    )

    kernel_ptrace = float(
        features.kernel_ptrace_count
    )

    # ============================================================
    # ENGINEERED FEATURES
    # ============================================================
    #
    # These features capture relationships between raw behavioral
    # signals rather than only their absolute counts.
    #
    # Small epsilon values are intentionally NOT added to the
    # denominator. A zero denominator represents a meaningful
    # absence of the corresponding activity and maps to 0.0.
    # ============================================================

    process_activity_ratio = (
        _safe_divide(
            process_creation + process_termination,
            unique_processes,
        )
    )

    connections_per_process = (
        _safe_divide(
            external_connections,
            unique_processes,
        )
    )

    failed_login_ratio = (
        _safe_divide(
            failed_logins,
            external_connections,
        )
    )

    filesystem_per_process = (
        _safe_divide(
            filesystem_modifications,
            unique_processes,
        )
    )

    exec_per_process = (
        _safe_divide(
            kernel_exec,
            unique_processes,
        )
    )

    kernel_connect_ratio = (
        _safe_divide(
            kernel_connect,
            external_connections,
        )
    )

    kernel_open_per_process = (
        _safe_divide(
            kernel_open,
            unique_processes,
        )
    )

    unlink_ratio = (
        _safe_divide(
            kernel_unlink,
            kernel_open,
        )
    )

    privilege_kernel_interaction = (
        privilege_escalations
        * (
            kernel_setuid
            + kernel_ptrace
        )
    )

    ptrace_exec_ratio = (
        _safe_divide(
            kernel_ptrace,
            kernel_exec,
        )
    )

    # ============================================================
    # FINAL PRODUCTION VECTOR
    # ============================================================

    vector = [
        # --------------------------------------------------------
        # Base features: 0-17
        # --------------------------------------------------------

        process_creation,              # 0
        process_termination,           # 1
        unique_processes,              # 2

        average_cpu,                   # 3
        maximum_cpu,                   # 4
        average_memory,                # 5
        maximum_memory,                # 6

        external_connections,          # 7

        failed_logins,                 # 8
        privilege_escalations,         # 9

        filesystem_modifications,      # 10
        service_restarts,              # 11

        kernel_exec,                   # 12
        kernel_connect,                # 13
        kernel_open,                   # 14
        kernel_unlink,                 # 15
        kernel_setuid,                 # 16
        kernel_ptrace,                 # 17

        # --------------------------------------------------------
        # Engineered features: 18-27
        # --------------------------------------------------------

        process_activity_ratio,        # 18
        connections_per_process,       # 19
        failed_login_ratio,            # 20
        filesystem_per_process,        # 21
        exec_per_process,              # 22
        kernel_connect_ratio,          # 23
        kernel_open_per_process,       # 24
        unlink_ratio,                  # 25
        privilege_kernel_interaction,  # 26
        ptrace_exec_ratio,             # 27
    ]

    # ============================================================
    # VALIDATION
    # ============================================================

    if len(vector) != FEATURE_COUNT:
        raise RuntimeError(
            "KATANA production feature vector must contain "
            f"{FEATURE_COUNT} features, got {len(vector)}."
        )

    for index, value in enumerate(vector):
        if not isinstance(value, (int, float)):
            raise RuntimeError(
                f"Feature {index} is not numeric: {value!r}"
            )

    return vector
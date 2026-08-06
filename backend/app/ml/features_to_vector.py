from app.feature_engine.features import BehaviorFeatures


def to_vector(features: BehaviorFeatures) -> list[float]:

    return [

        features.process_creation_rate,

        features.process_termination_rate,

        float(features.unique_process_count),

        features.average_cpu,

        features.maximum_cpu,

        features.average_memory,

        features.maximum_memory,

        float(features.external_connections),

        float(features.failed_logins),

        float(features.privilege_escalations),

        float(features.filesystem_modifications),

        float(features.service_restarts),

    ]
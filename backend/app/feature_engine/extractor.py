from app.schemas.enums import EventType
from app.schemas.event import Event
from app.feature_engine.features import BehaviorFeatures


class FeatureExtractor:

    def extract(
        self,
        events: list[Event],
    ) -> BehaviorFeatures:

        features = BehaviorFeatures()

        if not events:
            return features

        cpu_values = []
        memory_values = []
        processes = set()

        for event in events:

            if event.pid:
                processes.add(event.pid)

            if event.cpu_percent is not None:
                cpu_values.append(event.cpu_percent)

            if event.memory_percent is not None:
                memory_values.append(event.memory_percent)

            match event.event_type:

                case EventType.PROCESS_STARTED:
                    features.process_creation_rate += 1

                case EventType.PROCESS_TERMINATED:
                    features.process_termination_rate += 1

                case EventType.EXTERNAL_CONNECTION:
                    features.external_connections += 1

                case EventType.LOGIN_FAILED:
                    features.failed_logins += 1

                case EventType.PRIVILEGE_ESCALATION:
                    features.privilege_escalations += 1

                case EventType.FILE_MODIFIED:
                    features.filesystem_modifications += 1

                case EventType.SERVICE_STOPPED:
                    features.service_restarts += 1

        features.unique_process_count = len(processes)

        if cpu_values:
            features.average_cpu = sum(cpu_values) / len(cpu_values)
            features.maximum_cpu = max(cpu_values)

        if memory_values:
            features.average_memory = sum(memory_values) / len(memory_values)
            features.maximum_memory = max(memory_values)

        return features
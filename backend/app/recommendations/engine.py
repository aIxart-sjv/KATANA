from app.feature_engine.features import BehaviorFeatures


class RecommendationEngine:
    """
    Generates safe, read-only investigation commands.

    Commands are NEVER executed automatically.
    """

    def generate(
        self,
        features: BehaviorFeatures,
    ) -> list[dict]:

        recommendations = []

        # ----------------------------------------------------------
        # PROCESS INVESTIGATION
        # ----------------------------------------------------------

        if (
            features.process_creation_rate > 20
            or features.unique_process_count > 30
        ):
            recommendations.append(
                {
                    "category": "process",
                    "reason": (
                        "Unusually high process activity detected."
                    ),
                    "command": (
                        "ps -eo pid,ppid,user,%cpu,%mem,"
                        "etime,cmd --sort=-%cpu"
                    ),
                }
            )

        # ----------------------------------------------------------
        # NETWORK INVESTIGATION
        # ----------------------------------------------------------

        if features.external_connections > 5:
            recommendations.append(
                {
                    "category": "network",
                    "reason": (
                        "Elevated external network activity detected."
                    ),
                    "command": "ss -tupn",
                }
            )

        # ----------------------------------------------------------
        # PRIVILEGE INVESTIGATION
        # ----------------------------------------------------------

        if features.privilege_escalations > 0:
            recommendations.append(
                {
                    "category": "privilege",
                    "reason": (
                        "Privilege escalation activity detected."
                    ),
                    "command": (
                        'journalctl --since "5 minutes ago" '
                        '| grep -Ei '
                        '"sudo|su|authentication|privilege"'
                    ),
                }
            )

        # ----------------------------------------------------------
        # FILESYSTEM INVESTIGATION
        # ----------------------------------------------------------

        if features.filesystem_modifications > 10:
            recommendations.append(
                {
                    "category": "filesystem",
                    "reason": (
                        "Elevated filesystem modification activity "
                        "detected."
                    ),
                    "command": (
                        "find /tmp /var/tmp "
                        "-type f -mmin -5 -ls"
                    ),
                }
            )

        # ----------------------------------------------------------
        # KERNEL INVESTIGATION
        # ----------------------------------------------------------

        if (
            features.kernel_ptrace_count > 0
            or features.kernel_setuid_count > 0
        ):
            recommendations.append(
                {
                    "category": "kernel",
                    "reason": (
                        "Sensitive kernel activity detected."
                    ),
                    "command": (
                        "journalctl --since "
                        '"5 minutes ago"'
                    ),
                }
            )

        # ----------------------------------------------------------
        # ALWAYS PROVIDE BASIC PROCESS VISIBILITY
        # ----------------------------------------------------------

        if not recommendations:
            recommendations.append(
                {
                    "category": "general",
                    "reason": (
                        "Review current system activity."
                    ),
                    "command": (
                        "ps -eo pid,ppid,user,%cpu,%mem,"
                        "etime,cmd --sort=-%cpu"
                    ),
                }
            )

        return recommendations
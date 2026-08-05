from dataclasses import dataclass


@dataclass(slots=True)
class ProcessInfo:
    pid: int
    ppid: int
    name: str
    username: str
    cpu_percent: float
    memory_percent: float


class ProcessSnapshot:
    def __init__(self):
        self.processes: dict[int, ProcessInfo] = {}

    def update(self, processes: dict[int, ProcessInfo]):
        self.processes = processes
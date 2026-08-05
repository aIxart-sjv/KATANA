from abc import ABC, abstractmethod


class BaseCollector(ABC):
    @abstractmethod
    async def collect(self):
        ...

    @abstractmethod
    async def start(self):
        ...

    @abstractmethod
    async def stop(self):
        ...
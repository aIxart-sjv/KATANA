import asyncio
from pathlib import Path


class KernelLoader:

    def __init__(self):

        self.process = None

    async def start(self):

        loader = (
            Path(__file__)
            .parent
            / "native"
            / "loader"
        )

        self.process = await asyncio.create_subprocess_exec(
            str(loader),
            stdout=asyncio.subprocess.PIPE,
        )

    async def read(self):

        while True:

            line = await self.process.stdout.readline()

            if not line:
                break

            print(
                "[Kernel]",
                line.decode().strip(),
            )

    async def stop(self):

        self.process.kill()
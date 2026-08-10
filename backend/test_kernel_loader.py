import asyncio

from app.kernel.loader.loader import KernelLoader


async def main():

    loader = KernelLoader()

    await loader.start()

    await loader.read()


asyncio.run(main())
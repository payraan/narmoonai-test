import asyncio
from monitor import ChannelMonitor

async def main():
    monitor = ChannelMonitor()
    await monitor.run_forever()

if __name__ == "__main__":
    asyncio.run(main())


#app SKPyLogger

import restapi, asyncio, logger

async def main():
    print("Starting...")
    await asyncio.gather(restapi.restapi(), logger.periodicLogging())

print("About to start loop")
loop = asyncio.new_event_loop()
loop.run_until_complete(main())
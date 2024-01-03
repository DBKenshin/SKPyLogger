#app SKPyLogger

import restapi, asyncio, logger

async def main():
    await asyncio.gather(restapi.restapi(), logger.periodicLogging())

loop = asyncio.new_event_loop()
loop.run_forever(main())
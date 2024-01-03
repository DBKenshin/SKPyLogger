#app SKPyLogger

import restapi, asyncio, logger
from flask import Flask

app = Flask(__name__)

async def main():
    print("Starting...")
    await asyncio.gather(restapi.restapi(app), logger.periodicLogging())

loop = asyncio.new_event_loop()
loop.run_until_complete(main())
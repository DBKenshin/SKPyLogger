import configparser, datetime, mysqldbconnection, asyncio
from datetime import timedelta
import requests

config = configparser.ConfigParser()
config.read('config.ini')
signalKServerAddress = config['SIGNALK']['signalkserveraddress'] + ":" + config['SIGNALK']['signalkserverport']
mySqlAddress = config['MYSQL']['mysqldbaddress'] + ":" + config['MYSQL']['mysqldbport']
mySqlUser = config['MYSQL']['mysqldbuser']
mySqlPassword = config['MYSQL']['mysqldbpassword']
mySqlDb = config['MYSQL']['mysqldbdb']
loggingFrequency = config['LOGGER']['loggingfreq']
logFreq = timedelta(minutes=int(loggingFrequency))

async def periodicLogging():
    print("initializing periodic logging")
    dbconnection = mysqldbconnection.mySqlDBConnection()
    with dbconnection:
        with dbconnection.cursor() as cursor:
            latestEntryTime = datetime.date.fromtimestamp(cursor.execute("SELECT timestamp FROM log_entry WHERE regular_entry = TRUE ORDER BY timestamp DESC LIMIT 1"))
            if latestEntryTime == None:
                latestEntryTime = 0
            currentTime = datetime.date.today()
            if (currentTime - latestEntryTime) > logFreq:
                logger(regular_entry=True)
            else:
                timeToSleep = logFreq - (currentTime - latestEntryTime)
                timeToSleepInSeconds = int(datetime.time.second(timeToSleep))
                asyncio.sleep(timeToSleepInSeconds)
                logger(regular_entry=True)
            
def logger(comment="", regular_entry=False):
    print("logging!")
    dbconnection = mysqldbconnection.mySqlDBConnection()
    if comment == None:
        comment = ""

    try:
        signalKAPIResponse = requests.get(signalKServerAddress + "/signalk")
        signalKAPIAddress = signalKAPIResponse.json()['endpoints']['v1']['signalk-http'] + "vessels/self/"
    except requests.ConnectionError as err:
        return(err)

    first = True
    columns = "(comment,"
    values = "VALUES('" + comment + "', '"
        
    for row in config.options('SIGNALKPATHS'):
        if first:
            first = False
        else:
            columns = columns + ", "
            values = values + "', '"
        columns = columns + row
        values = values + signalKAPIFetch(signalKAPIAddress, config['SIGNALKPATHS'][row])

    if regular_entry:
        columns = columns + ", regular_entry"
        values = values + ", TRUE"
    else:
        columns = columns + ", regular_entry"
        values = values + ", FALSE"
    columns = columns + ")"
    values = values + "')"
    logSQLstatement = "INSERT INTO current_log" + columns + " " + values
    with dbconnection:
        with dbconnection.cursor() as cursor:
            result = cursor.execute(logSQLstatement)
            return result


def signalKAPIFetch(api:str,parameter:str):
    response = requests.get(api + parameter.replace(".", "/"))
    return response.json()['value']
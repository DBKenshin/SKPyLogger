import configparser, mySqlConnection, datetime, time, asyncio
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

config = {
        'user': mySqlUser,
        'password': mySqlPassword,
        'host': mySqlAddress,
        'database': mySqlDb,
        'raise_on_warnings': True
    }

async def periodicLogging():
    connection = mySqlConnection(config)
    if connection and connection.is_connected():
        with connection.cursor(dictionary=True) as cursor:
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
    else:
        print("No database connection, logging disabled!")
            
def logger(comment:str, regular_entry=False):

    if comment == None:
        comment = ""

    try:
        signalKAPIResponse = requests.get(signalKServerAddress + "/signalk")
        signalKAPIAddress = signalKAPIResponse.json()['endpoints']['v1']['signalk-http'] + "vessels/self/"
    except requests.ConnectionError as err:
        return(err)

    first = True
    columns = "("
    values = "VALUES('"
        
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
    connection = mySqlConnection(config)
    if connection and connection.is_connected():
        with connection.cursor(dictionary=True) as cursor:
            result = cursor.execute(logSQLstatement)
            return result


def signalKAPIFetch(api:str,parameter:str):
    response = requests.get(api + parameter.replace(".", "/"))
    return response.json()['value']
import configparser, datetime, mysqldbconnection, asyncio, json, time
from datetime import timedelta, timezone
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
    print("Initializing periodic logging...")
    while True: # run forever
        dbconnection = mysqldbconnection.mySqlDBConnection()
        with dbconnection:
            with dbconnection.cursor() as cursor:
                cursor.execute("SELECT timestamp FROM log_entry WHERE regular_entry = TRUE ORDER BY timestamp DESC LIMIT 1")
                latestEntryTime = cursor.fetchone()['timestamp']
                latestEntryTime = latestEntryTime.replace(tzinfo=timezone.utc).astimezone(tz=timezone.utc)
                print("Last log entry at:")
                print(latestEntryTime)
                currentTime = datetime.datetime.now()
                currentTime = currentTime.replace(tzinfo=None).astimezone(tz=timezone.utc)
                print("Current time in UTC is:")
                print(currentTime)
                timediff = currentTime - latestEntryTime
                if timediff >= logFreq:
                    print("It has been " + str(timediff) + " since the last log entry")
                    logger(regular_entry=True)
                else:
                    timeToSleep = logFreq - (currentTime - latestEntryTime)
                    timeToSleepSeconds = int(timeToSleep.total_seconds())
                    print("Logger thread sleeping for " + str(timeToSleepSeconds) + "s")
                    await asyncio.sleep(timeToSleepSeconds)
                    #time.sleep(timeToSleepSeconds)
                    logger(regular_entry=True)
            
def logger(comment="", regular_entry=False):
    print("Writing a log...")
    dbconnection = mysqldbconnection.mySqlDBConnection()
    if comment == None:
        comment = ""

    try:
        signalKAPIResponse = requests.get(signalKServerAddress + "/signalk")
        signalKAPIAddress = signalKAPIResponse.json()['endpoints']['v1']['signalk-http'] + "vessels/self/"
        print("SignalK server contacted, API address is " + signalKAPIAddress)
    except requests.ConnectionError as err:
        return(err)

    first = True
    columns = "(comment,"
    values = "VALUES('" + comment + "', '"
        
    #TODO: instead of making multiple calls, just get the entire json dump from signalKAPIAddress and parse it here
    #TODO: Probably much faster since the SignalK server can be a little bit slow with each response
    signal_k_dump = signalKAPIFetch(signalKAPIAddress)

    for row in config.options('SIGNALKPATHS'):
        if first:
            first = False
        else:
            columns = columns + ", "
            values = values + "', '"
        columns = columns + row
        value_buffer = signal_k_dump[row]
        if "timestamp" in row:
            value_buffer = str(datetime.datetime.fromisoformat(value_buffer).strftime("%Y-%m-%d %H:%M:%S"))
        if "position" in row:
            value_buffer = json.dumps(value_buffer).replace("'", '"')
        if "attitude" in row:
            value_buffer = json.dumps(value_buffer).replace("'", '"')

        values = values + value_buffer

    if regular_entry:
        columns = columns + ", regular_entry"
        values = values + "', TRUE"
    else:
        columns = columns + ", regular_entry"
        values = values + "', FALSE"
    columns = columns + ")"
    values = values + ")"
    logSQLstatement = "INSERT INTO log_entry" + columns + " " + values
    with dbconnection:
        with dbconnection.cursor() as cursor:
            print("Executing the following SQL statement:")
            print(logSQLstatement)
            result = cursor.execute(logSQLstatement)
            print(result)
            return result

def signalKAPIFetch(api:str):
    #get the entire dump from SK
    response = requests.get(api)
    return response.json()

def signalKAPIFetch(api:str,parameter:str):
    #get only a single parameter from SK
    response = requests.get(api + parameter.replace(".", "/"))
    return response.json()['value']
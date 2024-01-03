import mysql.connector
from mysql.connector import errorcode

def mySqlConnection(config):
    try:
        return mysql.connector.connect(**config)
    except (mysql.connector.Error, IOError) as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Incorrect username or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("No such database")
        else:
            print(err)
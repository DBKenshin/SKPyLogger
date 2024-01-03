import configparser, pymysql.cursors

config = configparser.ConfigParser()
config.read('config.ini')
mySqlAddress = config['MYSQL']['mysqldbaddress'] + ":" + config['MYSQL']['mysqldbport']
mySqlUser = config['MYSQL']['mysqldbuser']
mySqlPassword = config['MYSQL']['mysqldbpassword']
mySqlDb = config['MYSQL']['mysqldbdb']

def mySqlDBConnection():
    try:
        dbconnection = pymysql.connect(
            user=mySqlUser,
            password=mySqlPassword,
            host=mySqlAddress,
            database=mySqlDb,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
            )
        return dbconnection
    except pymysql.Error as err:
        print(err)
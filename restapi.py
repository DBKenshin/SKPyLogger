from flask import Flask, request, jsonify
import configparser, datetime, logger, pymysql.cursors

config = configparser.ConfigParser()
config.read('config.ini')
signalKServerAddress = config['SIGNALK']['signalkserveraddress'] + ":" + config['SIGNALK']['signalkserverport']
mySqlAddress = config['MYSQL']['mysqldbaddress'] + ":" + config['MYSQL']['mysqldbport']
mySqlUser = config['MYSQL']['mysqldbuser']
mySqlPassword = config['MYSQL']['mysqldbpassword']
mySqlDb = config['MYSQL']['mysqldbdb']

dbconnection = pymysql.connect(
    user=mySqlUser,
    password=mySqlPassword,
    host=mySqlAddress,
    database=mySqlDb,
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
    )

async def restapi():
    app = Flask(__name__)

    @app.get("/recent")
    def get_recent():
        # Returns in JSON the most recent log entry
        with dbconnection:
            with dbconnection.cursor(dictionary=True) as cursor:
                result = cursor.execute("SELECT * FROM log_entry ORDER BY timestamp DESC LIMIT 1")
                return jsonify(result)

    @app.put("/recent")
    def put_recent():
        # Adds/replaces text in Comments field of most recent log entry, takes JSON
        if request.is_json:
            comment = request.form.get('comment', default="", type=str)
            with dbconnection:
                with dbconnection.cursor(dictionary=True) as cursor:
                    timestamp = cursor.execute("SELECT timestamp FROM log_entry ORDER BY timestamp DESC LIMIT 1")
                    result = cursor.execute("UPDATE log_entry SET comment = '" + comment + "' WHERE timestamp = " + timestamp)
                    return jsonify(result)
        return {"error": "Request must be JSON"}, 415

    @app.post("/recent")
    def post_recent():
        # Appends text to end of the most recent log entry’s Comments field, takes JSON
        if request.is_json:
            comment = request.form.get('comment', default="", type=str)
            with dbconnection:
                with dbconnection.cursor(dictionary=True) as cursor:
                    timestamp = cursor.execute("SELECT timestamp FROM log_entry ORDER BY timestamp DESC LIMIT 1")
                    existingComment = cursor.execute("SELECT comment FROM log_entry ORDER BY timestamp DESC LIMIT 1")
                    newComment = existingComment + " |Appended comment " + datetime.datetime.now() + "| " + comment
                    result = cursor.execute("UPDATE log_entry SET comment = '" + newComment + "' WHERE timestamp = " + timestamp)
                    return jsonify(result)
        return {"error": "Request must be JSON"}, 415

    @app.get("/timestamp/<float:time>/<int:rows>")
    def get_timestamp(time: float, rows: int):
        # Returns in JSON the number r entries at and immediately prior to time t
        with dbconnection:
            with dbconnection.cursor(dictionary=True) as cursor:
                result = cursor.execute("SELECT * FROM log_entry WHERE timestamp <= " + str(time) + "ORDER BY timestamp DESC LIMIT " + str(rows))
                return jsonify(result)

    @app.post("/timestamp/<float:time>")
    def post_timestamp(time: float):
        # Appends text to the end of the log entry with time t (exact value required), takes JSON
        if request.is_json:
            comment = request.form.get('comment', default="", type=str)
            with dbconnection:
                with dbconnection.cursor(dictionary=True) as cursor:
                    existingComment = cursor.execute("SELECT comment FROM log_entry WHERE timestamp = " + time)
                    newComment = existingComment + " |Appended comment " + str(datetime.datetime.now()) + "| " + comment
                    result = cursor.execute("UPDATE log_entry SET comment = '" + newComment + "' WHERE timestamp = " + time)
                    return jsonify(result)
        return {"error": "Request must be JSON"}, 415

    @app.put("/immediate")
    def put_immediate():
        # Triggers an immediate log entry with the included optional text in the Comments field, takes JSON (format to be defined)
        if request.is_json:
            comment = request.form.get('comment', default="", type=str)
            logresult = logger.logger(comment, False)
            return jsonify(logresult)
        return {"error": "Request must be JSON"}, 415
    
    @app.get("/signalk")
    def get_signalk():
        # returns the address of the SignalK server being used
        return signalKServerAddress
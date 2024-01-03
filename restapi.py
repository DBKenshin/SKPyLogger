from flask import Flask, request, jsonify
import configparser, datetime, logger, mysqldbconnection

config = configparser.ConfigParser()
config.read('config.ini')
signalKServerAddress = config['SIGNALK']['signalkserveraddress'] + ":" + config['SIGNALK']['signalkserverport']
mySqlAddress = config['MYSQL']['mysqldbaddress'] + ":" + config['MYSQL']['mysqldbport']
mySqlUser = config['MYSQL']['mysqldbuser']
mySqlPassword = config['MYSQL']['mysqldbpassword']
mySqlDb = config['MYSQL']['mysqldbdb']

async def restapi():
    print("REST API starting up...")
    app = Flask(__name__)

    @app.get("/recent")
    async def get_recent():
        # Returns in JSON the most recent log entry
        dbconnection = mysqldbconnection.mySqlDBConnection()
        async with dbconnection:
            with dbconnection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM log_entry ORDER BY timestamp DESC LIMIT 1")
                result = cursor.fetchone()
                return jsonify(result)

    @app.put("/recent")
    async def put_recent():
        # Adds/replaces text in Comments field of most recent log entry, takes JSON
        if request.is_json:
            comment = request.form.get('comment', default="", type=str)
            dbconnection = mysqldbconnection.mySqlDBConnection()
            async with dbconnection:
                with dbconnection.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT entry_id FROM log_entry ORDER BY timestamp DESC LIMIT 1")
                    entry_id = cursor.fetchone()
                    result = cursor.execute("UPDATE log_entry SET comment = '" + comment + "' WHERE entry_id = " + entry_id)
                    return jsonify(result)
        return {"error": "Request must be JSON"}, 415

    @app.post("/recent")
    async def post_recent():
        # Appends text to end of the most recent log entry’s Comments field, takes JSON
        if request.is_json:
            comment = request.form.get('comment', default="", type=str)
            dbconnection = mysqldbconnection.mySqlDBConnection()
            async with dbconnection:
                with dbconnection.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT entry_id FROM log_entry ORDER BY timestamp DESC LIMIT 1")
                    entry_id = cursor.fetchone()
                    cursor.execute("SELECT comment FROM log_entry ORDER BY timestamp DESC LIMIT 1")
                    existingComment = cursor.fetchone()
                    newComment = existingComment + " |Appended comment " + datetime.datetime.now() + "| " + comment
                    result = cursor.execute("UPDATE log_entry SET comment = '" + newComment + "' WHERE entry_id = " + entry_id)
                    return jsonify(result)
        return {"error": "Request must be JSON"}, 415

    @app.get("/timestamp/<float:time>/<int:rows>")
    async def get_timestamp(time: float, rows: int):
        # Returns in JSON the number r entries at and immediately prior to time t
        dbconnection = mysqldbconnection.mySqlDBConnection()
        async with dbconnection:
            with dbconnection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM log_entry WHERE timestamp <= " + str(time) + "ORDER BY timestamp DESC LIMIT " + str(rows))
                result = cursor.fetchone()
                return jsonify(result)

    @app.post("/entry_id/<int:entry_id>")
    async def post_entry_id(entry_id: int):
        # Appends text to the end of the log entry with entry_id (int), takes JSON
        if request.is_json:
            comment = request.form.get('comment', default="", type=str)
            dbconnection = mysqldbconnection.mySqlDBConnection()
            async with dbconnection:
                with dbconnection.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT comment FROM log_entry WHERE entry_id = " + entry_id)
                    existingComment = cursor.fetchone()
                    newComment = existingComment + " |Appended comment " + str(datetime.datetime.now()) + "| " + comment
                    cursor.execute("UPDATE log_entry SET comment = '" + newComment + "' WHERE entry_id = " + entry_id)
                    result = cursor.fetchone()
                    return jsonify(result)
        return {"error": "Request must be JSON"}, 415

    @app.put("/immediate")
    async def put_immediate():
        # Triggers an immediate log entry with the included optional text in the Comments field, takes JSON (format to be defined)
        if request.is_json:
            comment = request.form.get('comment', default="", type=str)
            logresult = logger.logger(comment, False)
            return jsonify(logresult)
        return {"error": "Request must be JSON"}, 415
    
    @app.get("/signalk")
    async def get_signalk():
        # returns the address of the SignalK server being used
        return signalKServerAddress
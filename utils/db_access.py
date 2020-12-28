import pymysql
import toolforge


def connect_to_user_database(db_name, user_db_port=None, user=None, password=None):
    """
    Establishes connection to database, created by user, in Toolforge.
    :param db_name: name of user's database
    :param user_db_port: port for connecting to db through ssh tunneling, if used
    :param user: Toolforge username of the tool
    :param password: Toolforge password pf the tool
    :return: pymysql.connection to the database
    """
    try:
        if user_db_port:
            conn = pymysql.connect(host='127.0.0.1', port=user_db_port,
                                   user=user, password=password)
            with conn.cursor() as cur:
                cur.execute("use " + db_name)
            conn.commit()
        else:
            conn = toolforge.toolsdb(db_name)

        return conn
    except pymysql.err.OperationalError as err:
        print('Failure: failure, please establish connection to Toolforge')
        print('Error: ', err)
        exit(1)


def connect_to_replicas_database(db_name, replicas_port=None, user=None, password=None):
    """
    Establishes connection to Wikimedia replicas database in Toolforge.
    :param db_name: name of the database
    :param replicas_port: port for connecting to db through ssh tunneling, if used
    :param user: Toolforge username of the tool
    :param password: Toolforge password pf the tool
    :return: pymysql.connection to the database
    """
    try:
        if replicas_port:
            conn = pymysql.connect(host='127.0.0.1', port=replicas_port,
                                   user=user, password=password)
            with conn.cursor() as cur:
                cur.execute("use " + db_name)
            conn.commit()
        else:
            conn = toolforge.connect(dbname=db_name)

        return conn
    except pymysql.err.OperationalError as err:
        print('Failure: failure, please establish connection to Toolforge')
        print('Error: ', err)
        exit(1)

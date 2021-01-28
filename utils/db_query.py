import toolforge
import pandas as pd
import numpy as np
import pymysql
import utils.db_access as db_acc

pymysql.converters.encoders[np.int64] = pymysql.converters.escape_int
pymysql.converters.conversions = pymysql.converters.encoders.copy()
pymysql.converters.conversions.update(pymysql.converters.decoders)


def encode_if_necessary(b):
    if type(b) is bytes:
        return b.decode("utf8")
    return b


def get_dbs(user_db_port=None, user=None, password=None):
    """
    Returns a list of all the dbnames from Sources table.

    :param user_db_port: Port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: list
    """
    try:
        conn = db_acc.connect_to_user_database(
            constants.DATABASE_NAME, user_db_port, user, password
        )
        with conn.cursor() as cur:
            cur.execute(
                "SELECT dbname FROM Sources WHERE url IS NOT NULL"
            )  # all, except 'meta'
            ret = [db[0] for db in cur]
        conn.close()
        return ret
    except Exception as err:
        print("Something went wrong.\n", err)
        exit(1)


def close_conn(conn):
    try:
        conn.close()
    except:
        pass


def query_data_generator(
    query,
    function_name,
    cols,
    db=None,
    replicas_port=None,
    user_db_port=None,
    user=None,
    password=None,
    replicas=True,
    row_count=500,
):
    """
    Query database (db) and return outputs in chunks.

    :param query: The SQL query to run.
    :param function_name: The function that was used to collect this data, useful for saving when data is missed due to errors.
    :param cols: The name of the columns to be used in dataframe for the data collected with SQL.
    :param db: The database from which the data was collected.
    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :param replicas: False if collecting data from toolsdb user database, True is collecting from other wikimedia databases.
    :param row_count: Number of rows to get in one query from the database.
    :return: dataframe
    """

    offset = 0
    row_count = row_count
    max_tries = 3

    while True:
        retry_counter = 0
        try:
            while True:
                try:
                    conn = (
                        db_acc.connect_to_replicas_database(
                            db, replicas_port, user, password
                        )
                        if replicas
                        else db_acc.connect_to_user_database(
                            DATABASE_NAME, user_db_port, user, password
                        )
                    )
                    with conn.cursor() as cur:
                        cur.execute(query + " LIMIT %d OFFSET %d" % (row_count, offset))
                        df = pd.DataFrame(cur.fetchall(), columns=cols).applymap(
                            encode_if_necessary
                        )
                    close_conn(conn)
                    break
                except (
                    pymysql.err.DatabaseError,
                    pymysql.err.OperationalError,
                ) as err:
                    close_conn(conn)
                    if retry_counter == max_tries:
                        raise Exception(err)
                    print(
                        "Retrying query of '%s' from %s in 1 minute..."
                        % (function_name, db)
                    )
                    retry_counter += 1
                    time.sleep(60)

            offset += row_count
            if len(df) == 0:
                return
            yield df
        except Exception as err:
            print("Something went wrong. Could not query from %s \n" % db, repr(err))
            with open("missed_db_info.txt", "a") as file:
                file.write(function_name + " " + db + "\n")
            break


def save_data(
    df,
    dbname,
    function_name,
    user_db_port=None,
    user=None,
    password=None,
    query=None,
    cols=None,
    custom=False,
):
    """
    Save data from df into Scripts table.

    :param df: The data to save into Scripts table; for custom=False df column names should match db column names.
    :param dbname: The database from which the data was collected.
    :param function_name: The function that was used to collect this data, useful for saving when data is missed due to errors.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :param query: Only used when custom=True. The query to use to save into table.
    :param cols: Only used when custom=True. The column list in order of params in the query.
    :param custom: True if providing custom query and column list to use to save into table.
    :return: None
    """

    if not custom:
        cols = df.columns.values[1:]  # skip page_id
        updates = ",".join([col + "=%s" for col in cols])

        query = "UPDATE Scripts SET %s WHERE dbname='%s' AND page_id=%s " % (
            updates,
            dbname,
            "%s",
        )

    max_tries = 3

    try:
        retry_counter = 0
        while True:
            try:
                conn = db_acc.connect_to_user_database(
                    DATABASE_NAME, user_db_port, user, password
                )
                with conn.cursor() as cur:
                    for index, elem in df.iterrows():
                        if not custom:
                            params = list(
                                np.concatenate((elem.values[1:], elem.values[0:1]))
                            )
                        else:
                            params = [elem[col] for col in cols]
                        cur.execute(query, params)
                conn.commit()
                close_conn(conn)
                break
            except (pymysql.err.DatabaseError, pymysql.err.OperationalError) as err:
                close_conn(conn)
                if retry_counter == max_tries:
                    raise Exception(err)
                print(
                    "Retrying saving of '%s' from %s in 1 minute..."
                    % (function_name, dbname)
                )
                retry_counter += 1
                time.sleep(60)

    except Exception as err:
        print("Something went wrong. Error saving pages from %s \n" % dbname, repr(err))
        with open("missed_db_info.txt", "a") as file:
            file.write(function_name + " " + dbname + "\n")
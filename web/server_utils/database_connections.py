import pymysql
import toolforge
import yaml
import pandas as pd
import numpy as np

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.safe_load(ymlfile)


pymysql.converters.encoders[np.int64] = pymysql.converters.escape_int
pymysql.converters.conversions = pymysql.converters.encoders.copy()
pymysql.converters.conversions.update(pymysql.converters.decoders)


def encode_if_necessary(b):
    if type(b) is bytes:
        return b.decode("utf8")
    return b


# duplicated from utils to avoid copying utils folder
def connect_to_user_database(user_db_port=None):
    """
    Establishes connection to database, created by user, in Toolforge.
    :param user_db_port: port for connecting to db through ssh tunneling, if used
    :return: pymysql.connection to the database
    """
    try:
        if user_db_port:
            conn = pymysql.connect(
                host="127.0.0.1",
                port=user_db_port,
                user=cfg['user_credits']['user'],
                password=cfg['user_credits']['password'],
                connect_timeout=1000,
            )
            with conn.cursor() as cur:
                cur.execute("use " + cfg['database_name'])
            conn.commit()
        else:
            conn = toolforge.toolsdb(cfg['database_name'], connect_timeout=1000)

        return conn
    except pymysql.err.OperationalError as err:
        print("Failure: Please establish connection to Toolforge")
        print("Error: ", err)
        exit(1)


def get_sourcecode_from_database(dbname, page_id, user_db_port=None):
    query = (
        "select dbname, page_id, title, sourcecode, cluster_wo_data "
        "from Scripts "
        "where dbname = %s and page_id = %s"
    )
    cols = ["dbname", "pageid", "title", "sourcecode", "cluster"]
    df = None
    try:
        conn = connect_to_user_database(user_db_port)
        with conn.cursor() as cur:
            cur.execute(query, (dbname, page_id))
            res = cur.fetchall()
            if res:
                df = pd.Series(
                    res[0],
                    index=cols,
                ).map(encode_if_necessary)

            return df
    except Exception as err:
        print("Something went wrong. ", repr(err))


def get_close_sourcecodes(dbname, page_id, cluster, user_db_port=None):
    query = (
        "select dbname, page_id, title "
        "from Scripts "
        "where cluster_wo_data = %s and page_id <> %s and dbname <> %s"
    )
    cols = ["dbname", "pageid", "title"]
    df = None
    try:
        conn = connect_to_user_database(user_db_port)
        with conn.cursor() as cur:
            cur.execute(query, (cluster, page_id, dbname))
            res = cur.fetchall()
            if res:
                df = pd.DataFrame(
                    res,
                    columns=cols,
                ).applymap(encode_if_necessary)

            return df
    except Exception as err:
        print("Something went wrong. ", repr(err))


def get_titles_and_filters(df, user_db_port=None):
    query = (
        "select dbname, page_id, title "
        "from Scripts "
        "where page_id = %s and dbname = %s"
    )
    cols = ["dbname", "pageid", "title"]
    res = []
    try:
        conn = connect_to_user_database(user_db_port)
        with conn.cursor() as cur:
            for _, elem in df.iterrows():
                cur.execute(
                    query, [elem["page_id"], elem["dbname"]]
                )
                res.append(cur.fetchall()[0])
        df = pd.DataFrame(
            res,
            columns=cols
            ).applymap(encode_if_necessary)

        return df
    except Exception as err:
        print("Something went wrong. ", repr(err))
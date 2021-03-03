import pymysql
import toolforge
import yaml
import pandas as pd
import numpy as np

from server_utils.save_for_client import save_column_to_json

# for successfully establishing connection to the databases, write your username, password
# and user's database name into config.yml
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
    :param user_db_port: port for connecting to db through ssh tunneling, if used.
    :return: pymysql.connection to the database.
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


def connect_to_replicas_database(db_name, replicas_port=None):
    """
    Establishes connection to Wikimedia replicas database in Toolforge.
    :param db_name: name of the database.
    :param replicas_port: port for connecting to db through ssh tunneling, if used.
    :return: pymysql.connection to the database.
    """
    try:
        if replicas_port:
            conn = pymysql.connect(
                host="127.0.0.1",
                port=replicas_port,
                user=cfg['user_credits']['user'],
                password=cfg['user_credits']['password'],
                connect_timeout=1000,
            )
            if db_name[-2:] != "_p":
                db_name = db_name + "_p"
            with conn.cursor() as cur:
                cur.execute("use " + db_name)
            conn.commit()
        else:
            conn = toolforge.connect(
                dbname=db_name, connect_timeout=1000, cluster="analytics"
            )

        return conn
    except pymysql.err.OperationalError as err:
        print("Failure: Please establish connection to Toolforge")
        print("Error: ", err)
        exit(1)


def get_language_family_linkage(replicas_port=None):
    """
    Connects to meta table in database replicas and fetches the information
    how dbnames, language of the wiki and project family are linked.
    Additionally, lists of all possible project families and all used languages
    are saved to json files for frontend to use.
    :param replicas_port: port for connecting to meta db through ssh tunneling, if used
    :return: pandas.DataFrame.
    """
    query = (
        "select dbname, lang, family "
        "from wiki "
        "where is_closed = 0"
    )
    cols = ["dbname", "lang", "family"]
    try:
        conn = connect_to_replicas_database('meta', replicas_port)
        with conn.cursor() as cur:
            cur.execute(query)
            df = pd.DataFrame(
                cur.fetchall(),
                columns=cols,
            )
            from pathlib import Path
            path = str(Path.home()) + '/www/python/src/client/public/'
            save_column_to_json(df, 'family', 'family.json', path)
            save_column_to_json(df, 'lang', 'lang.json', path)
            return df
    except Exception as err:
        print("Something went wrong. ", repr(err))


def get_sourcecode_from_database(dbname, page_id, user_db_port=None):
    """
    Fetches from user's database title, sourcecode and cluster of the script,
    set by its page ID and database name.
    :param dbname: name of the database, from which the processed script was fetched.
    :param page_id: page ID of this page on this database.
    :param user_db_port: port for connecting to db through ssh tunneling, if used.
    :return: pandas.Series.
    """
    query = (
        "select dbname, page_id, title, sourcecode, cluster "
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


def get_close_sourcecodes(dbname, page_id, cluster, user_db_port=None, eps=0):
    """
    Fetches information on the scripts, which are considered to be in the same cluster as checked entry
    or in the close ones.
    :param dbname: name of the database, from which the processed script was fetched.
    :param page_id: page ID of this page on this database.
    :param cluster: cluster number of the processed script.
    :param user_db_port: port for connecting to db through ssh tunneling, if used.
    :param eps: used for querying not only for the same cluster, but also for the close ones,
    so the function will return info on scripts, where cluster number is in [cluster-eps, cluster+eps]
    :return: pandas.DataFrame.
    """
    query = (
        "select dbname, page_id, title "
        "from Scripts "
        "where cluster <= %s and cluster >= %s "
    )
    cols = ["dbname", "pageid", "title"]
    df = None
    try:
        conn = connect_to_user_database(user_db_port)
        with conn.cursor() as cur:
            cur.execute(query, (cluster + eps, cluster - eps))
            res = cur.fetchall()
            if res:
                df = pd.DataFrame(
                    res,
                    columns=cols,
                ).applymap(encode_if_necessary)
                curr_index = df[(df['dbname'] == dbname) & (df['pageid'] == int(page_id))].index
                df.drop(curr_index, inplace=True)

            return df
    except Exception as err:
        print("Something went wrong. ", repr(err))


def get_scripts_titles(df, user_db_port=None):
    """
    Fetches page titles for the scripts, whose info is stored ino the dataframe.
    :param df: pandas.DataFrame, containing page IDs and dbnames for scripts we want the titles of.
    :param user_db_port: port for connecting to db through ssh tunneling, if used.
    :return: pandas.DataFrame
    """
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

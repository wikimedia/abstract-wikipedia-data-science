import pandas as pd
import argparse
import pymysql
import numpy as np

import utils.db_access as db_acc
from utils.db_query import encode_if_necessary, get_dbs
import constants

pymysql.converters.encoders[np.int64] = pymysql.converters.escape_int
pymysql.converters.conversions = pymysql.converters.encoders.copy()
pymysql.converters.conversions.update(pymysql.converters.decoders)


def save_to_db(entries, db, user_db_port=None, user=None, password=None):
    """
    Saves datframe into Scripts table.
    Note that title from page-table does not have namespace prefix, title from API does.
    We retain the value from API.

    :param entries: A dataframe with columns: dbname, page_id, in_database, page_is_redirect, page_is_new
    :param user_db_port: Port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

    query = (
        "INSERT INTO Scripts(dbname, page_id, in_database, page_is_redirect, page_is_new) "
        "VALUES(%s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE in_database = %s, page_is_redirect = %s, page_is_new = %s"
    )
    try:
        conn = db_acc.connect_to_user_database(
            constants.DATABASE_NAME, user_db_port, user, password
        )
        with conn.cursor() as cur:
            for index, elem in entries.iterrows():
                cur.execute(
                    query,
                    [
                        db,
                        elem["page_id"],
                        1,
                        elem["page_is_redirect"],
                        elem["page_is_new"],
                        1,
                        elem["page_is_redirect"],
                        elem["page_is_new"],
                    ],
                )
        conn.commit()
        conn.close()
    except Exception as err:
        print("Something went wrong.\n", err)
        exit(1)


def get_data(dbs, replicas_port=None, user_db_port=None, user=None, password=None):
    """
    Goes through all the wikis and fetches Scribunto modules from them, saving collected data to user's database.

    :param dbs: list of dbnames, from which the modules will be collected
    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """
    ## Get all pages
    for db in dbs:
        try:
            ## Connect
            conn = db_acc.connect_to_replicas_database(
                db + "_p", replicas_port, user, password
            )
            with conn.cursor() as cur:
                ## Query
                cur.execute("USE " + db + "_p")
                SQL_Query = pd.read_sql_query(
                    "SELECT page_id, page_is_redirect, page_is_new FROM page "
                    "WHERE page_content_model='Scribunto' AND page_namespace=828",
                    conn,
                )
                df_page = pd.DataFrame(SQL_Query).applymap(encode_if_necessary)

                # Saving to db
                save_to_db(df_page, db, user_db_port, user, password)
                # print("Finished loading scripts from ", db)
            conn.close()
        except Exception as err:
            print("Error loading pages from db:", db, "\nError:", err)

    print("Done loading from databases.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Updates Lua scripts in database in Toolforge, fetching info from database replicas. "
        "To use from local PC, provide all the additional flags needed for "
        "establishing connection through ssh tunneling."
        "More help available at "
        "https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#SSH_tunneling_for_local_testing_which_makes_use_of_Wiki_Replica_databases"
    )
    local_data = parser.add_argument_group(
        title="Info for connecting to Toolforge from local pc"
    )
    local_data.add_argument(
        "--replicas-port",
        "-r",
        type=int,
        default=None,
        help="Port for connecting to meta table through ssh tunneling, if used.",
    )
    local_data.add_argument(
        "--user-db-port",
        "-udb",
        type=int,
        default=None,
        help="Port for connecting to tables, created by user in Toolforge, "
        "through ssh tunneling, if used.",
    )
    local_data.add_argument(
        "--user", "-u", type=str, default=None, help="Toolforge username of the tool."
    )
    local_data.add_argument(
        "--password",
        "-p",
        type=str,
        default=None,
        help="Toolforge password of the tool.",
    )
    args = parser.parse_args()

    dbs = get_dbs(args.user_db_port, args.user, args.password)
    get_data(dbs, args.replicas_port, args.user_db_port, args.user, args.password)

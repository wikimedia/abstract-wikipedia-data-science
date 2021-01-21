import toolforge
import pandas as pd
import numpy as np
import pymysql
import argparse
import mwapi
import os
import time

import utils.db_access as db_acc
from db_script import encode_if_necessary, get_dbs
from constants import DATABASE_NAME

pymysql.converters.encoders[np.int64] = pymysql.converters.escape_int
pymysql.converters.conversions = pymysql.converters.encoders.copy()
pymysql.converters.conversions.update(pymysql.converters.decoders)


## Utils


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

    try:
        conn = (
            db_acc.connect_to_replicas_database(db, replicas_port, user, password)
            if replicas
            else db_acc.connect_to_user_database(
                DATABASE_NAME, user_db_port, user, password
            )
        )

        while True:
            retry_counter = 0

            conn.ping()
            with conn.cursor() as cur:
                while True:
                    try:
                        cur.execute(query + " LIMIT %d OFFSET %d" % (row_count, offset))
                        break
                    except (
                        pymysql.err.DatabaseError,
                        pymysql.err.OperationalError,
                    ) as err:
                        if retry_counter == max_tries:
                            raise Exception(err)
                        print(
                            "Retrying query of '%s' from %s in 1 minute..."
                            % (function_name, db)
                        )
                        retry_counter += 1
                        time.sleep(60)

                df = pd.DataFrame(cur.fetchall(), columns=cols).applymap(
                    encode_if_necessary
                )

            offset += row_count

            if len(df) == 0:
                return

            yield df

    except Exception as err:
        print("Something went wrong. Could not query from %s \n" % db, repr(err))
        with open("missed_db_info.txt", "a") as file:
            file.write(function_name + " " + db + "\n")

    finally:
        conn.close()


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

    :param df: The data to save into Scripts table.
    :param dbname: The database from which the data was collected.
    :param function_name: The function that was used to collect this data, useful for saving when data is missed due to errors.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :param query: Only used when custom=True. The query to use to save into table.
    :param cols: Only used when custom=True. The column list in order of params in the query.
    :param custom: True id providing custom query and column list to use to save into table.
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
        conn = db_acc.connect_to_user_database(
            DATABASE_NAME, user_db_port, user, password
        )

        retry_counter = 0
        while True:
            try:
                conn.ping()
                with conn.cursor() as cur:
                    for index, elem in df.iterrows():
                        if not custom:
                            params = list(
                                np.concatenate((elem.values[1:], elem.values[0:1]))
                            )
                        else:
                            params = []
                            for col in cols:
                                params.append(elem[col])
                        cur.execute(query, params)
                conn.commit()
                break
            except (pymysql.err.DatabaseError, pymysql.err.OperationalError) as err:
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

    finally:
        conn.close()


def get_interwiki(user_db_port=None, user=None, password=None):

    """
    Get interwiki mapping from API and save in user database.

    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

    session = mwapi.Session("https://en.wikipedia.org", user_agent="abstract-wiki-ds")
    params = {
        "action": "query",
        "format": "json",
        "meta": "siteinfo",
        "siprop": "interwikimap",
    }
    result = session.get(params)
    ret = result["query"]["interwikimap"]

    ## Save interwiki mapping to user_db
    query = (
        "INSERT INTO Interwiki(prefix, url) VALUES(%s, %s) "
        "ON DUPLICATE KEY UPDATE url = %s"
    )
    try:
        conn = db_acc.connect_to_user_database(
            DATABASE_NAME, user_db_port, user, password
        )
        with conn.cursor() as cur:
            for mp in ret:
                cur.execute(query, (mp["prefix"], mp["url"], mp["url"]))
        conn.commit()
    except Exception as err:
        print("Something went wrong. Could not get interwiki table\n", repr(err))
    finally:
        conn.close()


def get_revision_info(
    db, function_name, replicas_port=None, user_db_port=None, user=None, password=None
):
    """
    Get the number of revisions and information info about edits of the Scribunto modules and save in user database.

    :param db: The database to connect to and get data from.
    :param function_names: The name of this function, useful to save function name when data is missed.
    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

    query = (
        "SELECT page_id, "
        "COUNT(rev_page) AS edits, SUM(rev_minor_edit) AS minor_edits, "
        "MIN(rev_timestamp) AS first_edit, MAX(rev_timestamp) AS last_edit, "
        "SUM(CASE WHEN actor_user IS NULL THEN 1 ELSE 0 END) AS anonymous_edits, "
        "COUNT(DISTINCT actor_user) AS editors "
        "FROM page "
        "INNER JOIN revision "
        "    ON page_id=rev_page "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "LEFT JOIN actor "
        "    ON rev_actor=actor_id "
        "GROUP BY page_id"
    )

    cols = [
        "page_id",
        "edits",
        "minor_edits",
        "first_edit",
        "last_edit",
        "anonymous_edits",
        "editors",
    ]
    for df in query_data_generator(
        query,
        function_name,
        cols,
        db,
        replicas_port,
        user_db_port,
        user,
        password,
    ):
        save_data(df, db, function_name, user_db_port, user, password)


def get_iwlinks_info(
    db, function_name, replicas_port=None, user_db_port=None, user=None, password=None
):
    """
    Get the number of inter wiki pages that referenced a module and save in user database.
    iwls from other dbs need to be added for each module.
    `Module:` is not the only prefix for Scribunto modules. It is different for languages e.g `মডিউল:`, ماجول ,ماڈیول.
    So, url was matched with iwl_title.

    :param db: The database to connect to and get data from.
    :param function_names: The name of this function, useful to save function name when data is missed.
    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

    drop_query = "DROP TABLE IF EXISTS Iwlinks"
    create_query = (
        "CREATE TABLE Iwlinks ("
        "    iwl_from INT UNSIGNED, "
        "    iwl_prefix VARCHAR(20), "
        "    iwl_title VARCHAR(255), "
        "    PRIMARY KEY (iwl_from, iwl_prefix, iwl_title)"
        ")"
    )
    insert_query = (
        "INSERT INTO Iwlinks(iwl_from, iwl_prefix, iwl_title) "
        "VALUES(%s, %s, %s) "
        "ON DUPLICATE KEY UPDATE iwl_title = %s"
    )
    query = (
        "SELECT page_id, dbname, COUNT(DISTINCT iwl_from) AS iwls "
        "FROM Scripts "
        "INNER JOIN "
        "    ("
        "        SELECT iwl_from, REPLACE(url, '$1', iwl_title) AS iwl_url "
        "        FROM Interwiki "
        "        INNER JOIN Iwlinks "
        "        ON prefix=iwl_prefix "
        "    ) AS iwl "
        "ON url=iwl_url "
        "GROUP BY page_id, dbname"
    )
    save_query = "UPDATE Scripts SET iwls = iwls + %s WHERE dbname=%s AND page_id=%s "
    cols = ["iwls", "dbname", "page_id"]

    try:
        conn_db = db_acc.connect_to_user_database(
            DATABASE_NAME, user_db_port, user, password
        )
        with conn_db.cursor() as db_cur:

            db_cur.execute(drop_query)
            db_cur.execute(create_query)

            for df in query_data_generator(
                "SELECT iwl_from, iwl_prefix, iwl_title FROM iwlinks",
                function_name,
                ["iwl_from", "iwl_prefix", "iwl_title"],
                db,
                replicas_port,
                user_db_port,
                user,
                password,
            ):
                for index, elem in df.iterrows():
                    params = list(np.concatenate((elem.values, elem.values[-1:])))
                    db_cur.execute(insert_query, params)

            for df in query_data_generator(
                query,
                function_name,
                ["page_id", "dbname", "iwls"],
                DATABASE_NAME,
                replicas_port,
                user_db_port,
                user,
                password,
                False,
            ):
                save_data(
                    df,
                    db,
                    function_name,
                    user_db_port,
                    user,
                    password,
                    save_query,
                    cols,
                    True,
                )

            db_cur.execute(drop_query)

        conn_db.commit()
        conn_db.close()
    except Exception as err:
        print(
            "Something went wrong. Could not get iwlinks info of %s\n" % db, repr(err)
        )


def get_pagelinks_info(
    db, function_name, replicas_port=None, user_db_port=None, user=None, password=None
):
    """
    Get the number of (in-wiki) pages that referenced a module and save in user database.

    :param db: The database to connect to and get data from.
    :param function_names: The name of this function, useful to save function name when data is missed.
    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

    query = (
        "SELECT page_id, "
        "COUNT(pl_from) AS pls "
        "FROM page "
        "INNER JOIN pagelinks "
        "    ON page_title=pl_title "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "    AND pl_namespace=828 "
        "GROUP BY page_id"
    )

    cols = ["page_id", "pls"]
    for df in query_data_generator(
        query, function_name, cols, db, replicas_port, user_db_port, user, password
    ):
        save_data(df, db, function_name, user_db_port, user, password)


def get_langlinks_info(
    db, function_name, replicas_port=None, user_db_port=None, user=None, password=None
):
    """
    Get the number of languages links a module has (ll) and save in user database.
    Number of languages a module is available in (ll+1).Use the langlink table more to
    find out language independent subset of modules.

    :param db: The database to connect to and get data from.
    :param function_names: The name of this function, useful to save function name when data is missed.
    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

    query = (
        "SELECT page_id, COUNT(ll_lang) AS langs "
        "FROM page "
        "INNER JOIN langlinks "
        "    ON ll_from=page_id "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "GROUP BY page_id"
    )

    cols = ["page_id", "langs"]
    for df in query_data_generator(
        query, function_name, cols, db, replicas_port, user_db_port, user, password
    ):
        save_data(df, db, function_name, user_db_port, user, password)


def get_templatelinks_info(
    db, function_name, replicas_port=None, user_db_port=None, user=None, password=None
):
    """
    Get the number of transclusions of a module and save in user database.

    :param db: The database to connect to and get data from.
    :param function_names: The name of this function, useful to save function name when data is missed.
    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

    query = (
        "SELECT page_id, "
        "COUNT(tl_from) AS transcluded_in "
        "FROM page "
        "INNER JOIN templatelinks "
        "    ON page_title=tl_title "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "    AND tl_namespace=828 "
        "GROUP BY page_id"
    )

    cols = ["page_id", "transcluded_in"]
    for df in query_data_generator(
        query,
        function_name,
        cols,
        db,
        replicas_port,
        user_db_port,
        user,
        password,
    ):
        save_data(df, db, function_name, user_db_port, user, password)


def get_transclusions_info(
    db, function_name, replicas_port=None, user_db_port=None, user=None, password=None
):
    """
    Get the number of modules transcluded in a module and save in user database.
    The query makes sure both from and to pages are Scribunto modules

    :param db: The database to connect to and get data from.
    :param function_names: The name of this function, useful to save function name when data is missed.
    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

    query = (
        "SELECT tl_from AS page_id, COUNT(tl_title) AS transclusions "
        "FROM page "
        "INNER JOIN templatelinks "
        "    ON page_id=tl_from "
        "    AND tl_from_namespace=828 "
        "    AND tl_namespace=828 "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto'"
        "WHERE tl_title IN "
        "    ("
        "        SELECT page_title "
        "        FROM page "
        "        WHERE page_namespace=828 AND page_content_model='Scribunto' "
        "    ) "
        "GROUP BY tl_from"
    )

    cols = ["page_id", "transclusions"]
    for df in query_data_generator(
        query, function_name, cols, db, replicas_port, user_db_port, user, password
    ):
        save_data(df, db, function_name, user_db_port, user, password)


def get_categories_info(
    db, function_name, replicas_port=None, user_db_port=None, user=None, password=None
):
    """
    Get the number of categories a module is included in and save in user database.
    There is not concrete list of categores to look for. We can list it ourselves,
    but then again it varies according to language. If required, use the category
    table to identify important categories

    :param db: The database to connect to and get data from.
    :param function_names: The name of this function, useful to save function name when data is missed.
    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

    query = (
        "SELECT page_id, COUNT(cl_to) AS categories "
        "FROM page "
        "INNER JOIN categorylinks "
        "    ON cl_from=page_id "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "GROUP BY page_id"
    )

    cols = ["page_id", "categories"]
    for df in query_data_generator(
        query, function_name, cols, db, replicas_port, user_db_port, user, password
    ):
        save_data(df, db, function_name, user_db_port, user, password)


def get_edit_protection_info(
    db, function_name, replicas_port=None, user_db_port=None, user=None, password=None
):
    """
    Get protection level for `edit` for the modules and save in user database.

    :param db: The database to connect to and get data from.
    :param function_names: The name of this function, useful to save function name when data is missed.
    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

    query = (
        "SELECT page_id, pr_level AS pr_level_edit "
        "FROM page_restrictions "
        "INNER JOIN page "
        "    ON page_id=pr_page "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "    AND pr_type='edit'"
    )

    cols = ["page_id", "pr_level_edit"]
    for df in query_data_generator(
        query, function_name, cols, db, replicas_port, user_db_port, user, password
    ):
        save_data(df, db, function_name, user_db_port, user, password)


def get_move_protection_info(
    db, function_name, replicas_port=None, user_db_port=None, user=None, password=None
):
    """
    Get protection level for `move` for the modules and save in user database.

    :param db: The database to connect to and get data from.
    :param function_names: The name of this function, useful to save function name when data is missed.
    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

    query = (
        "SELECT page_id, pr_level AS pr_level_move "
        "FROM page_restrictions "
        "INNER JOIN page "
        "    ON page_id=pr_page "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "    AND pr_type='move'"
    )

    cols = ["page_id", "pr_level_move"]
    for df in query_data_generator(
        query, function_name, cols, db, replicas_port, user_db_port, user, password
    ):
        save_data(df, db, function_name, user_db_port, user, password)


def get_most_common_tag_info(
    db, function_name, replicas_port=None, user_db_port=None, user=None, password=None
):
    """
    Loading comma separated most common tag names for each page from all
    databases and save in user database. See the inline view (subquery)
    for details on each page.

    :param db: The database to connect to and get data from.
    :param function_names: The name of this function, useful to save function name when data is missed.
    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

    query = (
        "SELECT tagcount.page_id AS page_id, GROUP_CONCAT(ctd_name) AS tags "
        "FROM "
        "("
        "    SELECT page_id, ctd_name, COUNT(*) AS tags "
        "    FROM change_tag "
        "    INNER JOIN change_tag_def "
        "        ON ct_tag_id=ctd_id "
        "        AND ctd_user_defined=0 "
        "    INNER JOIN revision "
        "        ON ct_rev_id=rev_id "
        "    INNER JOIN page "
        "        ON rev_page=page_id "
        "        AND page_namespace=828 "
        "        AND page_content_model='Scribunto' "
        "    GROUP BY page_id, ctd_name "
        ") AS tagcount "
        "INNER JOIN "
        "("
        "    SELECT page_id, MAX(tags) AS most_common_tag_count "
        "    FROM "
        "    ("
        "        SELECT page_id, ctd_name, COUNT(*) AS tags "
        "        FROM change_tag "
        "        INNER JOIN change_tag_def "
        "            ON ct_tag_id=ctd_id "
        "            AND ctd_user_defined=0 "
        "        INNER JOIN revision "
        "            ON ct_rev_id=rev_id "
        "        INNER JOIN page "
        "            ON rev_page=page_id "
        "            AND page_namespace=828 "
        "            AND page_content_model='Scribunto' "
        "        GROUP BY page_id, ctd_name "
        "    ) AS tagcount "
        "    GROUP BY page_id"
        ") AS mosttag "
        "ON mosttag.page_id=tagcount.page_id "
        "AND tagcount.tags=mosttag.most_common_tag_count "
        "GROUP BY tagcount.page_id"
    )

    cols = ["page_id", "tags"]
    for df in query_data_generator(
        query,
        function_name,
        cols,
        db,
        replicas_port,
        user_db_port,
        user,
        password,
    ):
        save_data(df, db, function_name, user_db_port, user, password)


def get_data(
    function_names, replicas_port=None, user_db_port=None, user=None, password=None
):
    """
    Loading data from all databases using a specific function -- therefore collecting a specific set of data.

    :param function_names: A list of function names to call for all the databases.
    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

    dbs = get_dbs(user_db_port, user, password)

    for db in dbs:
        for function_name in function_names:
            eval(function_name)(
                db, function_name, replicas_port, user_db_port, user, password
            )
            # print("     Loaded %s for %s" % (function_name, db))

    print("Done loading all data")


def get_missed_data(replicas_port=None, user_db_port=None, user=None, password=None):
    """
    Retry loading missed data from databases.

    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

    success = False
    try:
        missed = []

        ## Read file
        with open("missed_db_info.txt", "r") as file:
            for line in file:
                if line:
                    missed.append(line.split())

        ## Empty file
        with open("missed_db_info.txt", "w") as file:
            file.write("")

        for function_name, db in missed:
            eval(function_name)(
                db, function_name, replicas_port, user_db_port, user, password
            )

        success = True

    except Exception as err:
        print("Something went wrong.\n", repr(err))

    finally:
        if not success:
            with open("missed_db_info.txt", "w") as file:
                for miss in missed:
                    file.write(miss[0] + " " + miss[1] + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gets information about Lua modules from multiple tables across the wiki."
        "To use from local PC, provide all the additional flags needed for "
        "establishing connection through ssh tunneling."
        "More help available at "
        "https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#SSH_tunneling_for_local_testing_which_makes_use_of_Wiki_Replica_databases"
    )
    parser.add_argument(
        "--interwiki",
        "-iw",
        action="store_true",
        help="Whether interwiki-table content should be re-fetched.",
    )
    parser.add_argument(
        "--function-names",
        "-fn",
        type=str,
        nargs="+",
        help="Name of the function to run for all wikis. "
        "One or more of: get_revision_info, get_iwlinks_info, get_pagelinks_info, "
        "get_langlinks_info, get_templatelinks_info, get_transclusions_info, "
        "get_categories_info, get_edit_protection_info, get_move_protection_info, "
        "get_most_common_tag_info",
    )
    parser.add_argument(
        "--get-missed",
        "-gm",
        action="store_true",
        help="Whether to get the missed information only. Taken from missed_db_info.txt, "
        "which lists function name and database name pairs.",
    )
    local_data = parser.add_argument_group(
        title="Info for connecting to Toolforge from local pc"
    )
    local_data.add_argument(
        "--replicas-port",
        "-r",
        type=int,
        default=None,
        help="Port for connecting to meta table through ssh tunneling.",
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

    if args.interwiki:
        get_interwiki(args.user_db_port, args.user, args.password)

    if args.get_missed:
        get_missed_data(args.replicas_port, args.user_db_port, args.user, args.password)
    else:
        get_data(
            args.function_names,
            args.replicas_port,
            args.user_db_port,
            args.user,
            args.password,
        )

import toolforge
import pandas as pd
import numpy as np
import pymysql
import argparse
import mwapi

import utils.db_access as db_acc
from db_script import encode_if_necessary, get_dbs
from constants import DATABASE_NAME

pymysql.converters.encoders[np.int64] = pymysql.converters.escape_int
pymysql.converters.conversions = pymysql.converters.encoders.copy()
pymysql.converters.conversions.update(pymysql.converters.decoders)


## Utils


def query_data_generator(
    query,
    db=None,
    replicas_port=None,
    user_db_port=None,
    user=None,
    password=None,
    replicas=True,
):
    try:

        if replicas:
            conn = db_acc.connect_to_replicas_database(
                db, replicas_port, user, password
            )
        else:
            conn = db_acc.connect_to_user_database(
                DATABASE_NAME, user_db_port, user, password
            )

        cur = conn.cursor()

        offset = 0
        row_count = 500
        while True:
            df = pd.read_sql(
                query + " LIMIT %d OFFSET %d" % (row_count, offset), conn
            ).applymap(encode_if_necessary)
            offset += row_count
            if len(df) == 0:
                return
            yield df

    except Exception as err:
        print("Something went wrong. Could not query from %s \n" % db, err)

    finally:
        conn.close()


def save_data(df, dbname, user_db_port=None, user=None, password=None):

    cols = df.columns.values[1:]  # skip page_id
    updates = ",".join([col + "=%s" for col in cols])

    query = "UPDATE Scripts SET %s WHERE dbname='%s' AND page_id=%s " % (
        updates,
        dbname,
        "%s",
    )

    try:
        conn = db_acc.connect_to_user_database(
            DATABASE_NAME, user_db_port, user, password
        )
        with conn.cursor() as cur:
            for index, elem in df.iterrows():
                params = list(np.concatenate((elem.values[1:], elem.values[0:1])))
                cur.execute(query, params)
        conn.commit()
        conn.close()
    except Exception as err:
        print("Something went wrong. Error saving pages from %s \n" % dbname, err)


## Populate Interwiki


def get_interwiki(user_db_port=None, user=None, password=None):

    ## Get interwiki mapping from API
    user_agent = toolforge.set_user_agent("abstract-wiki-ds")
    session = mwapi.Session("https://en.wikipedia.org", user_agent=user_agent)
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
        conn.close()
    except Exception as err:
        print("Something went wrong. Could not get interwiki table\n", err)
        exit(1)


## Get info from DB


def get_revision_info(
    db, replicas_port=None, user_db_port=None, user=None, password=None
):
    ## Number of revisions and information info about edits of the Scribunto modules
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

    for df in query_data_generator(
        query, db, replicas_port, user_db_port, user, password
    ):
        save_data(df, db, user_db_port, user, password)


def get_iwlinks_info(
    db, replicas_port=None, user_db_port=None, user=None, password=None
):
    ## Number of inter wiki pages that referenced a module
    ## iwls from other dbs need to be added for each module

    """
    `Module:` is not the only prefix for Scribunto modules.
    It is different for languages e.g `মডিউল:`, ماجول ,ماڈیول
    So, url was matched with iwl_title
    """

    init_query = "DROP TABLE IF EXISTS Iwlinks"
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
    drop_query = "DROP TABLE Iwlinks"
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

    try:
        conn_db = db_acc.connect_to_user_database(
            DATABASE_NAME, user_db_port, user, password
        )
        with conn_db.cursor() as db_cur:

            db_cur.execute(init_query)
            db_cur.execute(create_query)

            for df in query_data_generator(
                query="SELECT * FROM iwlinks",
                db=db,
                replicas_port=replicas_port,
                user_db_port=user_db_port,
                user=user,
                password=password,
            ):
                for index, elem in df.iterrows():
                    params = list(np.concatenate((elem.values, elem.values[-1:])))
                    db_cur.execute(insert_query, params)

            for df in query_data_generator(
                query, DATABASE_NAME, replicas_port, user_db_port, user, password, False
            ):
                save_data(df, db, user_db_port, user, password)

            db_cur.execute(drop_query)

        conn_db.commit()
        conn_db.close()
    except Exception as err:
        print("Something went wrong. Could not get iwlinks info of %s\n" % db, err)


def get_pagelinks_info(
    db, replicas_port=None, user_db_port=None, user=None, password=None
):
    ## Number of (in-wiki) pages that referenced a module

    query = (
        "SELECT page_id, "
        "COUNT(DISTINCT pl_from) AS pls "
        "FROM page "
        "INNER JOIN pagelinks "
        "    ON page_title=pl_title "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "    AND pl_namespace=828 "
        "GROUP BY page_id"
    )

    for df in query_data_generator(
        query, db, replicas_port, user_db_port, user, password
    ):
        save_data(df, db, user_db_port, user, password)


def get_langlinks_info(
    db, replicas_port=None, user_db_port=None, user=None, password=None
):
    ## Number of languages links a module has (ll)
    ## Number of languages a module is available in (ll+1)
    ## Use the langlink table more to find out language independent subset of modules

    query = (
        "SELECT page_id, COUNT(DISTINCT ll_lang) AS langs "
        "FROM page "
        "INNER JOIN langlinks "
        "    ON ll_from=page_id "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "GROUP BY page_id"
    )

    for df in query_data_generator(
        query, db, replicas_port, user_db_port, user, password
    ):
        save_data(df, db, user_db_port, user, password)


def get_templatelinks_info(
    db, replicas_port=None, user_db_port=None, user=None, password=None
):
    ## Number of transclusions of a module

    query = (
        "SELECT page_id, "
        "COUNT(DISTINCT tl_from) AS transcluded_in "
        "FROM page "
        "INNER JOIN templatelinks "
        "    ON page_title=tl_title "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "    AND tl_namespace=828 "
        "GROUP BY page_id"
    )

    for df in query_data_generator(
        query, db, replicas_port, user_db_port, user, password
    ):
        save_data(df, db, user_db_port, user, password)


def get_transclusions_info(
    db, replicas_port=None, user_db_port=None, user=None, password=None
):
    ## Number of modules transcluded in a module
    ## this includes docs and other stuffs too
    ## so we need to filter by namespace and content_model
    ## The query makes sure both from and to pages are Scribunto modules

    query = (
        "SELECT tl_from, COUNT(DISTINCT tl_title) AS transclusions "
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

    for df in query_data_generator(
        query, db, replicas_port, user_db_port, user, password
    ):
        save_data(df, db, user_db_port, user, password)


def get_categories_info(
    db, replicas_port=None, user_db_port=None, user=None, password=None
):
    ## Number of categories a module is included in
    ## There is not concrete list of categores to look for.
    ## We can list it ourselves, but then again it varies according to language.
    ## If required, use the category table to identify important categories

    query = (
        "SELECT page_id, COUNT(DISTINCT cl_to) AS categories "
        "FROM page "
        "INNER JOIN categorylinks "
        "    ON cl_from=page_id "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "GROUP BY page_id"
    )

    for df in query_data_generator(
        query, db, replicas_port, user_db_port, user, password
    ):
        save_data(df, db, user_db_port, user, password)


def get_edit_protection_info(
    db, replicas_port=None, user_db_port=None, user=None, password=None
):
    ## Protection level for `edit` for the modules

    query = (
        "SELECT page_id, pr_level AS pr_level_edit FROM page_restrictions "
        "INNER JOIN page "
        "    ON page_id=pr_page "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "    AND pr_type='edit'"
    )

    for df in query_data_generator(
        query, db, replicas_port, user_db_port, user, password
    ):
        save_data(df, db, user_db_port, user, password)


def get_move_protection_info(
    db, replicas_port=None, user_db_port=None, user=None, password=None
):
    ## Protection level for `move` for the modules

    query = (
        "SELECT page_id, pr_level AS pr_level_move FROM page_restrictions "
        "INNER JOIN page "
        "    ON page_id=pr_page "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "    AND pr_type='move'"
    )

    for df in query_data_generator(
        query, db, replicas_port, user_db_port, user, password
    ):
        save_data(df, db, user_db_port, user, password)


def get_most_common_tag_info(
    db, replicas_port=None, user_db_port=None, user=None, password=None
):
    ## Comma separated most common tag names for each page
    ## See the inline view (subquery) for details on each page

    query = (
        "SELECT tagcount.page_id, GROUP_CONCAT(ctd_name) AS tags "
        "FROM "
        "("
        "    SELECT page_id, ctd_name, COUNT(*) AS tags "
        "    FROM change_tag "
        "    INNER JOIN change_tag_def "
        "        ON ct_tag_id=ctd_id "
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

    for df in query_data_generator(
        query, db, replicas_port, user_db_port, user, password
    ):
        save_data(df, db, user_db_port, user, password)


def get_data(
    function_name, replicas_port=None, user_db_port=None, user=None, password=None
):

    dbs = get_dbs(user_db_port, user, password)

    for db in dbs:
        eval(function_name)(db, replicas_port, user_db_port, user, password)
        print("     Loaded %s for %s" % (function_name, db))

    print("Done loading all data")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gets information about Lua modules from multiple tables across the wiki."
        "To use from local PC, use flag --local and all the additional flags needed for "
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
        "--function-name",
        "-fn",
        type=str,
        help="Name of the function to run for all wikis. "
        "One of get_revision_info, get_iwlinks_info, get_pagelinks_info, "
        "get_langlinks_info, get_templatelinks_info, get_transclusions_info, "
        "get_categories_info, get_edit_protection_info, get_move_protection_info, "
        "get_most_common_tag_info",
    )
    parser.add_argument(
        "--local",
        "-l",
        action="store_true",
        help="Connection is initiated from local pc.",
    )
    local_data = parser.add_argument_group(
        title="Info for connecting to Toolforge from local pc"
    )
    local_data.add_argument(
        "--replicas-port",
        "-r",
        type=int,
        help="Port for connecting to meta table through ssh tunneling.",
    )
    local_data.add_argument(
        "--user-db-port",
        "-udb",
        type=int,
        help="Port for connecting to tables, created by user in Toolforge, "
        "through ssh tunneling, if used.",
    )
    local_data.add_argument(
        "--user", "-u", type=str, help="Toolforge username of the tool."
    )
    local_data.add_argument(
        "--password", "-p", type=str, help="Toolforge password of the tool."
    )
    args = parser.parse_args()

    if not args.local:
        if args.interwiki:
            get_interwiki()
        get_data(args.function_name)
    else:
        if args.interwiki:
            get_interwiki(args.user_db_port, args.user, args.password)
        get_data(
            args.function_name,
            args.replicas_port,
            args.user_db_port,
            args.user,
            args.password,
        )

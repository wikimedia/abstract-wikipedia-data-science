import pandas as pd
import argparse
import toolforge
import mwapi

import utils.db_access as db_acc
from constants import DATABASE_NAME


def get_mapping(user_db_port=None, user=None, password=None):
    try:
        conn = db_acc.connect_to_user_database(
            DATABASE_NAME, user_db_port, user, password
        )
        with conn.cursor() as cur:
            cur.execute("SELECT dbname, url FROM Sources WHERE url IS NOT NULL")
            db_map = {data[0]: data[1] for data in cur}
        conn.close()
        return db_map
    except Exception as err:
        print("Something went wrong.\n", err)
        exit(1)


def get_pageviews(pageid, wiki, days):
    user_agent = toolforge.set_user_agent("abstract-wiki-ds")
    session = mwapi.Session(wiki, user_agent=user_agent)
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageviews",
        "pageids": pageid,
        "pvipdays": days,
        "formatversion": 2,
    }
    result = session.get(params)
    cnt = 0
    for k, v in result["query"]["pages"][0]["pageviews"].items():
        if v:
            cnt += v
    return cnt


def get_modules(user_db_port=None, user=None, password=None):
    try:
        conn = db_acc.connect_to_user_database(
            DATABASE_NAME, user_db_port, user, password
        )

        with conn.cursor() as cur:
            cur.execute("SELECT dbname, page_id, title FROM Scripts")
            for data in cur:
                yield data

        conn.close()
    except Exception as err:
        print("Something went wrong.\n", err)
        exit(1)


def get_transclusions(dbname, title, replicas_port=None, user=None, password=None):
    try:
        conn = db_acc.connect_to_replicas_database(
            dbname, replicas_port, user, password
        )

        with conn.cursor() as cur:
            cur.execute(
                "SELECT tl_from "
                "FROM templatelinks "
                "WHERE tl_namespace=828 AND tl_title= BINARY %s ",
                title,
            )
            for data in cur:
                yield data[0]

        conn.close()
    except Exception as err:
        print("Something went wrong.\n", err)
        exit(1)


def save_pageview(
    page_id, dbname, pageviews, add=False, user_db_port=None, user=None, password=None
):

    if add:
        query = (
            "UPDATE Scripts SET pageviews=pageviews+%s WHERE dbname=%s AND page_id=%s "
        )
    else:
        query = "UPDATE Scripts SET pageviews=%s WHERE dbname=%s AND page_id=%s "

    try:
        conn = db_acc.connect_to_user_database(
            DATABASE_NAME, user_db_port, user, password
        )

        with conn.cursor() as cur:
            cur.execute(query, [pageviews, dbname, page_id])

        conn.commit()
        conn.close()
    except Exception as err:
        print("Something went wrong.\n", err)


def get_all_pageviews(
    replicas_port=None, user_db_port=None, user=None, password=None, days=1
):
    db_map = get_mapping(user_db_port, user, password)

    for (dbname, module_page_id, title) in get_modules(user_db_port, user, password):
        pageviews = 0
        wiki = db_map[dbname]

        for page_id in get_transclusions(dbname, title, replicas_port, user, password):
            pageviews += get_pageviews(page_id, wiki, days)

        save_pageview(
            module_page_id, dbname, pageviews, days == 1, user_db_port, user, password
        )


def pageviews_type(x):
    x = int(x)
    if x < 1 or x > 60:
        raise argparse.ArgumentError("Should be a value from 1 to 60.")
    return x


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gets pageview information with API and saves in Scripts database."
        "To use from local PC, provide all the additional flags needed for "
        "establishing connection through ssh tunneling."
        "More help available at "
        "https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#SSH_tunneling_for_local_testing_which_makes_use_of_Wiki_Replica_databases"
    )
    parser.add_argument(
        "--days",
        "-d",
        type=pageviews_type,
        default=1,
        help="Number of days of pageviews to get. A number from 1 to 60. "
        "Intended usage: Set 60 on initial run and 1 on subsequent daily runs.",
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
    get_all_pageviews(
        args.replicas_port, args.user_db_port, args.user, args.password, args.days
    )

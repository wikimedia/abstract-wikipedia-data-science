import pandas as pd
import argparse
import toolforge
import mwapi
import requests
from urllib.parse import quote_plus
from datetime import datetime, timedelta

import utils.db_access as db_acc
from constants import DATABASE_NAME


def get_pageviews_rest_api(title, wiki, date, all):

    title = quote_plus(title)
    date_from = "20000101"
    granularity = "monthly"
    if not all:
        date_from = date
        granularity = "daily"

    url = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        + wiki
        + "/all-access/all-agents/"
        + title
        + "/"
        + granularity
        + "/"
        + date_from
        + "/"
        + date
    )

    USER_AGENT = {"User-Agent": "abstract-wiki-ds"}
    response = requests.get(url, headers=USER_AGENT)

    if response.status_code == 200:
        res = response.json()
        cnt = 0
        for item in res["items"]:
            cnt += item["views"]
        return cnt

    elif response.status_code == 404:
        return 0

    else:
        print(response.status_code, response.reason)


def get_mapping(user_db_port, user, password):
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


def get_modules(user_db_port, user, password):
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


def get_transclusions(dbname, title, replicas_port, user, password):
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


def save_pageview(page_id, dbname, pageviews, add, user_db_port, user, password):

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


def api2db_title(title):
    ix = title.find(":")
    return title if ix == -1 else title[ix + 1 :]


def get_title(dbname, page_id, replicas_port, user, password):

    try:
        conn = db_acc.connect_to_replicas_database(
            dbname, replicas_port, user, password
        )

        with conn.cursor() as cur:
            cur.execute("SELECT page_title FROM page WHERE page_id=%s", page_id)
            title = cur.fetchone()[0]
        conn.close()
        return title
    except Exception as err:
        print("Something went wrong.\n", err)
        exit(1)


def get_date():
    ## Gets yesterdays date in YYYYMMDD format
    return datetime.date(datetime.now() - timedelta(1)).strftime("%Y%m%d")


def get_all_pageviews(replicas_port, user_db_port, user, password, all, rest_api):
    db_map = get_mapping(user_db_port, user, password)
    days = 60 if all else 1

    for (dbname, module_page_id, title) in get_modules(user_db_port, user, password):

        title = api2db_title(title)
        pageviews = 0
        wiki = db_map[dbname]

        for page_id in get_transclusions(dbname, title, replicas_port, user, password):
            if rest_api:
                pageviews += get_pageviews_rest_api(
                    get_title(dbname, page_id, replicas_port, user, password),
                    wiki,
                    get_date(),
                    all,
                )
            else:
                pageviews += get_pageviews(page_id, wiki, days)

        save_pageview(
            module_page_id, dbname, pageviews, not all, user_db_port, user, password
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gets pageview information with API and saves in Scripts database."
        "To use from local PC, provide all the additional flags needed for "
        "establishing connection through ssh tunneling."
        "More help available at "
        "https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#SSH_tunneling_for_local_testing_which_makes_use_of_Wiki_Replica_databases"
    )
    parser.add_argument(
        "--use-rest",
        "-rest",
        action="store_true",
        help="Whether to use REST API. Uses PHP API if not set. "
        "REST API collects pageviews since July, 2015 whereas PHP API gets data for the last 60 days only. "
        "To collect daily data, both work the same (although values differ due to internal API caching)",
    )
    parser.add_argument(
        "--all-days",
        "-d",
        action="store_true",
        help="Whether to get pageviews `till today` or `only today`. "
        "Intended usage: Use it on initial run and on subsequent daily runs avoid it to get daily data only.",
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
        args.replicas_port,
        args.user_db_port,
        args.user,
        args.password,
        args.all_days,
        args.use_rest,
    )

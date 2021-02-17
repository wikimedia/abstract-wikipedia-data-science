import pandas as pd
import argparse
import mwapi
import requests
import os
import gzip
from urllib.parse import quote_plus
from datetime import datetime, timedelta

import utils.db_access as db_acc
from constants import DATABASE_NAME

## Global mapping of pages and their pageviews
## Populated when source = "dumps"
dumps = {}


def read_dump_file(filepath):
    ## See abbreviation schema in
    ## https://wikitech.wikimedia.org/wiki/Analytics/Data_Lake/Traffic/Pageviews

    get_abbr_map = {
        "b": "wikibooks",
        "d": "wiktionary",
        "f": "foundationwiki",
        "n": "wikinews",
        "q": "wikiquote",
        "s": "wikisource",
        "v": "wikiversity",
        "voy": "wikivoyage",
        "w": "mediawikiwiki",
        "wd": "wikidatawiki",
    }
    for filename in os.listdir(filepath):
        if filename.split("-")[0] != "pageviews":
            continue
        filename = os.path.join(filepath, filename)
        with gzip.open(filename, "rt") as file:
            for line in file:
                lines = line.split()
                source, title, pageview = line[0], " ".join(line[1:-2]), int(line[-2])
                source = source.split(".")
                if len(source) == 3:
                    del source[1]  # mentions .m (mobile device) or .zero
                if len(source) == 1 or source[1] == "m":
                    # en or en.m or commons.m
                    dbname = source[0] + "wiki"
                else:
                    dbname = source[0] + get_abbr_map[source[1]]

                key = (dbname, title)
                if key in dumps.keys():
                    dumps[key] += pageview
                else:
                    dumps[key] = pageview


def load_dumps(all):
    dirpath = "/public/dumps/public/other/pageviews"
    if all:
        for year in os.listdir(dirpath):
            if not year.isnumeric():
                continue

            year_path = os.listdir(os.path.join(dirpath, year))
            for month in year_path:
                month_path = os.path.join(year_path, month)
                for filename in os.listdir(month_path):
                    filepath = os.path.join(month_path, filename)
                    read_dump_file(filepath)
    else:
        ## The 'year' of last month
        date = datetime.now() - timedelta(30)
        date = datetime(date.year, date.month, 1).strftime("%Y%m%d")

        year = date[:4]
        month = date[4:6]
        month = year + "-" + month

        filepath = os.path.join(dirpath, year, month)
        read_dump_file(filepath)


def get_pageviews_rest_api(title, wiki, all):
    """
    Get pageviews for a specific page using the WikiMedia REST API.

    :param title: Title of the page whose pageviews to fetch.
    :param wiki: URL of the wiki. Like en.wikipedia.org.
    :param date: The date till when the pageviews should be fetched.
    :param all: Set True to fetch all page views till `date`. Else fetches pageviews only for `date` day.
    :return: int
    """

    try:
        title = quote_plus(title)
        date_from = "20000101"
        granularity = "monthly"
        ## giving todays date will fetch data till last month
        date = datetime.now().strftime("%Y%m%d")
        if not all:
            ## The first of last month
            date_from = datetime.now() - timedelta(30)
            date_from = datetime(date_from.year, date_from.month, 1).strftime("%Y%m%d")

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

        else:
            print(response.status_code, response.reason)

    except Exception as err:
        print(
            "Something went wrong fetching from REST API for %s in %s.\n"
            % (title, wiki),
            err,
        )

    return 0


def get_mapping(user_db_port, user, password):
    """
    Fetch and return database name to URL mapping.

    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: dictionary of fetched info in form {dbname1: url1, dbname2:url2,...}
    """
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
        print("Something went wrong getting dbname-url mapping.\n", err)
        exit(1)


def get_pageviews(pageid, wiki, days):
    """
    Get pageviews for a specific page using the WikiMedia PHP API.

    :param pageid: Id of the page whose pageviews to fetch.
    :param wiki: URL of the wiki. Like en.wikipedia.org.
    :param days: The number of last days data to fetch.
    :return: int
    """

    cnt = 0
    try:
        session = mwapi.Session(wiki, user_agent="abstract-wiki-ds")
        params = {
            "action": "query",
            "format": "json",
            "prop": "pageviews",
            "pageids": pageid,
            "pvipdays": days,
            "formatversion": 2,
        }
        result = session.get(params)
        for k, v in result["query"]["pages"][0]["pageviews"].items():
            if v:
                cnt += v

    except Exception as err:
        print(
            "Something went wrong fetching from API for %d in %s.\n" % (pageid, wiki),
            err,
        )

    return cnt


def get_modules(user_db_port, user, password):
    """
    A generator to fetch and return all pages in the Scripts table.

    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: Tuples with dbname, page_id, and title
    """

    try:
        conn = db_acc.connect_to_user_database(
            DATABASE_NAME, user_db_port, user, password
        )

        with conn.cursor() as cur:
            cur.execute("SELECT dbname, page_id FROM Scripts")
            for data in cur:
                yield data

        conn.close()
    except Exception as err:
        print("Something went wrong fetching module list.\n", err)
        exit(1)


def get_transclusions(dbname, title, replicas_port, user, password):
    """
    A generator to fetch and return all pageid of pages that transclude the `title` module.

    :param dbname: Which database the module corresponds to.
    :param title: Title of the module.
    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: int
    """

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
        print(
            "Something went wrong getting transclusions for %s in %s.\n"
            % (title, dbname),
            err,
        )


def save_pageview(page_id, dbname, pageviews, add, user_db_port, user, password):
    """
    Save pageviews data into Scripts table.

    :param page_id: The Id of the page whose pageviews is to be stored.
    :param dbname: Which database the module corresponds to.
    :param pageviews: The value to be stored in table.
    :param add: Whether to add to the existing pageviews(when collecting monthly data) or not.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

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
        print(
            "Something went wrong saving to db (%d, %s, %d).\n"
            % (page_id, dbname, pageviews),
            err,
        )


def get_title(dbname, page_id, replicas_port, user, password):
    """
    Get title of the page with id as `page_id`.

    :param dbname: Which database the module corresponds to.
    :param page_id: The Id of the page whose page title is to be fetched.
    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: Page title as string.
    """

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
        print("Something went wrong getting page title.\n", err)
        exit(1)


def get_all_pageviews(replicas_port, user_db_port, user, password, all, source):
    """
    Get pageviews for all pages which transclude modules and save them.

    :param replicas_port: port for connecting to meta table through ssh tunneling, if used.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :param all: Set True to fetch all page views till yesterday. Else fetches pageviews only for"
    "           last month.
    :param source: Either php, rest or dumps. Identifies where to collect the pageviews data from.
    :return: None
    """

    db_map = get_mapping(user_db_port, user, password)
    days = 60 if all else 30  # for php API only

    for (dbname, module_page_id) in get_modules(user_db_port, user, password):
        try:

            if module_page_id is None:
                continue

            title = get_title(dbname, module_page_id, replicas_port, user, password)
            pageviews = 0
            wiki = db_map[dbname]

            for page_id in get_transclusions(
                dbname, title, replicas_port, user, password
            ):
                if source == "rest":
                    page_title = get_title(
                        dbname, page_id, replicas_port, user, password
                    )
                    pageviews += get_pageviews_rest_api(page_title, wiki, all)
                elif source == "dumps":
                    page_title = get_title(
                        dbname, page_id, replicas_port, user, password
                    )
                    pageviews += dumps[(dbname, page_title)]
                else:
                    pageviews += get_pageviews(page_id, wiki, days)

            save_pageview(
                module_page_id, dbname, pageviews, not all, user_db_port, user, password
            )

        except Exception as err:
            print(
                "Something went wrong for page %d in %s.\n" % (module_page_id, dbname),
                err,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gets pageview information with API or from dumps and saves in Scripts database."
        "To use from local PC, provide all the additional flags needed for "
        "establishing connection through ssh tunneling."
        "More help available at "
        "https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#SSH_tunneling_for_local_testing_which_makes_use_of_Wiki_Replica_databases"
    )
    parser.add_argument(
        "--use-rest",
        "-rest",
        action="store_true",
        help="Whether to use REST API. Uses PHP API if -dump is also not set. "
        "REST API collects pageviews since July, 2015 whereas PHP API gets data for the last 60 days only. "
        "To collect monthly data, both work the same (although values differ due to internal API caching)",
    )
    parser.add_argument(
        "--use-dumps",
        "-dumps",
        action="store_true",
        help="Whether to collect data from the pageviews dumps. Uses PHP API if -rest is also not set. "
        "Can only be set if being used from toolforge as it needs access to dump files. "
        "Only one of -rest or -dump can be set at a time, if any at all. "
        "Colects pageviews since May, 2015 if -d is set, else for the last month.",
    )
    parser.add_argument(
        "--all-days",
        "-d",
        action="store_true",
        help="Whether to get pageviews `till today` or `only last month`. "
        "Intended usage: Use it on initial run and on subsequent monthly runs avoid it to get monthly data only.",
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

    source = "php"
    if args.use_rest and args.use_dumps:
        exit("Both -dump and -rest cannot be set, please choose only one.")
    elif args.use_rest:
        source = "rest"
    elif args.use_dumps:
        source = "dumps"
        load_dumps(args.all_days)

    get_all_pageviews(
        args.replicas_port,
        args.user_db_port,
        args.user,
        args.password,
        args.all_days,
        source,
    )

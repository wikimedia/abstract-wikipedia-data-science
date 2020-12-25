## imports
import toolforge
import pymysql.err
import pymysql
import pandas as pd
import os.path
import argparse


DATABASE_NAME = 's54588__data'


def get_wikipages_from_db(meta_port=None, user=None, password=None):
    """
    Requests all names of the databases and linked urls for all working Wikimedia projects.

    :return: ((dbname1, url1), (dbname2, url2),...)
    """
    query = ("\n"
             "    select dbname, url\n"
             "    from wiki\n"
             "    where is_closed = 0")

    if meta_port:
        conn = pymysql.connect(host='127.0.0.1', port=meta_port,
                               user=user, password=password)
    else:
        conn = toolforge.connect('meta')
    with conn.cursor() as cur:
        cur.execute("use meta_p;")
        cur.execute(query)
        return cur.fetchall()


def get_creation_date_from_db(meta_port=None, user=None, password=None):
    """
    Requests date of the creation of the meta table (which seems to be the date of the update).

    :return: Datetime.datetime
    """
    query = ("\n"
             "    select create_time\n"
             "    from INFORMATION_SCHEMA.TABLES\n"
             "    where table_name = 'wiki'")
    try:
        if meta_port:
            conn = pymysql.connect(host='127.0.0.1', port=meta_port,
                                   user=user, password=password)
        else:
            conn = toolforge.connect('meta')
        with conn.cursor() as cur:
            cur.execute("use meta_p;")
            cur.execute(query)
            return cur.fetchone()[0]
    except pymysql.err.OperationalError:
        print('Wikiprojects update checker: failure, please use only in Toolforge environment')
        exit(1)


def save_links_to_db(entries, sources_port=None, user=None, password=None):
    """
    Saves links and dbnames to the local project database.

    :param entries: List(tuple) of lists(tuples), with pairs 'dbname - url'
    :return: None
    """
    query = ("insert into Sources(dbname, url) values(%s, %s)\n"
             "on duplicate key update url = %s")
    try:
        if sources_port:
            conn = pymysql.connect(host='127.0.0.1', port=sources_port,
                                   user=user, password=password)
        else:
            conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute("use " + DATABASE_NAME)
            for elem in entries:
                cur.execute(query, [elem[0], elem[1], elem[1]])
        conn.commit()
        conn.close()
    except pymysql.err.OperationalError:
        print('Wikiprojects update checker: failure, please use only in Toolforge environment')
        exit(1)


def get_last_update_local_db(sources_port=None, user=None, password=None):
    """
    Looks into csv with last update times and fetches last update time for meta table, if it is stored.
    If such file doesn't exits, creates it.

    :return: Datetime.datetime of last update or None
    """
    query = ("select update_time\n"
             "from Sources\n"
             "where dbname = 'meta'\n")
    update_time = None

    try:
        if sources_port:
            conn = pymysql.connect(host='127.0.0.1', port=sources_port,
                                   user=user, password=password)
        else:
            conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute("use " + DATABASE_NAME)
            cur.execute(query)
            update_time = cur.fetchone()
        return update_time
    except pymysql.err.OperationalError:
        print('Wikiprojects update checker: failure, please use only in Toolforge environment')
        exit(1)


def update_local_db(update_time, sources_port=None, user=None, password=None):
    """
    Saves new update time for meta table, creating corresponding row if needed.

    :param update_time: Datetime.datetime, time of last update for meta table
    :return: None
    """
    query = ("insert into Sources(dbname, update_time) values('meta', %s)\n"
             "on duplicate key update update_time = %s"
             )
    try:
        if sources_port:
            conn = pymysql.connect(host='127.0.0.1', port=sources_port,
                                   user=user, password=password)
        else:
            conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            time = update_time.strftime('%Y-%m-%d %H:%M:%S')
            cur.execute("use " + DATABASE_NAME)
            cur.execute(query, [time, time])
        conn.commit()
        conn.close()
    except pymysql.err.OperationalError:
        print('Wikiprojects update checker: failure, please use only in Toolforge environment')
        exit(1)



def update_checker(meta_port=None, sources_port=None, user=None, password=None):
    wiki_db_update_time = get_creation_date_from_db(meta_port, user, password)
    print('Wikiprojects update checker: time of last update fetched from database')
    local_db_update_time = get_last_update_local_db(sources_port, user, password)
    print('Wikiprojects update checker: local time of last update fetched')
    if local_db_update_time is not None:
        if wiki_db_update_time == local_db_update_time:
            print('Wikiprojects update checker: update not needed')
            return

    db_info = get_wikipages_from_db(meta_port, user, password)
    print('Wikiprojects update checker: wikilinks info fetched from db')
    save_links_to_db(db_info, sources_port, user, password)
    print('Wikiprojects update checker: wikipages links updated in db')
    update_local_db(wiki_db_update_time, sources_port, user, password)
    print('Wikiprojects update checker: update finished')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", "-l", action="store_true",
                        help="Connection is initiated from local pc.")
    local_data = parser.add_argument_group(title="Info for connecting to Toolforge from local pc.")
    local_data.add_argument("--meta-port", "-m", type=int,
                            help="Port for connecting to meta table through ssh tunneling, if used.")
    local_data.add_argument("--sources-port", "-s", type=int,
                            help="Port for connecting to local Sources table through ssh tunneling, if used.")
    local_data.add_argument("--user", "-u", type=str,
                            help="Toolforge username of the tool.")
    local_data.add_argument("--password", "-p", type=str,
                            help="Toolforge password of the tool.")
    args = parser.parse_args()

    if not args.local:
        update_checker()
    else:
        update_checker(args.meta_port, args.sources_port, args.user, args.password)

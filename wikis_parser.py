## imports
import pymysql.err
import pymysql
import argparse

import utils.db_access as db_acc


DATABASE_NAME = 's54588__data'


def get_wikipages_from_db(replicas_port=None, user=None, password=None):
    """
    Requests all names of the databases and linked urls for all working Wikimedia projects.

    :param replicas_port: Port for connecting to meta table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: ((dbname1, url1), (dbname2, url2),...)
    """
    query = ("\n"
             "    select dbname, url\n"
             "    from wiki\n"
             "    where is_closed = 0")

    conn = db_acc.connect_to_replicas_database('meta_p', replicas_port, user, password)
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def get_creation_date_from_db(replicas_port=None, user=None, password=None):
    """
    Requests date of the creation of the meta table (which seems to be the date of the update).

    :param replicas_port: Port for connecting to meta table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: Datetime.datetime
    """
    query = ("\n"
             "    select create_time\n"
             "    from INFORMATION_SCHEMA.TABLES\n"
             "    where table_name = 'wiki'")
    try:
        conn = db_acc.connect_to_replicas_database('meta_p', replicas_port, user, password)
        with conn.cursor() as cur:
            cur.execute(query)
            time = cur.fetchone()[0]
            return time
    except pymysql.err.OperationalError:
        print('Wikiprojects update checker: failure, please establish connection to Toolforge')
        exit(1)


def save_links_to_db(entries, user_db_port=None, user=None, password=None):
    """
    Saves links and dbnames to the local project database.

    :param entries: List(tuple) of lists(tuples), with pairs 'dbname - url'
    :param user_db_port: Port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """
    query = ("insert into Sources(dbname, url) values(%s, %s)\n"
             "on duplicate key update url = %s")
    try:
        conn = db_acc.connect_to_user_database(DATABASE_NAME, user_db_port, user, password)
        with conn.cursor() as cur:
            for elem in entries:
                cur.execute(query, [elem[0], elem[1], elem[1]])
        conn.commit()
        conn.close()
    except pymysql.err.OperationalError:
        print('Wikiprojects update checker: failure, please establish connection to Toolforge')
        exit(1)


def get_last_update_local_db(user_db_port=None, user=None, password=None):
    """
    Looks into database with last update times and fetches last update time for meta table, if it is stored.
    If such file doesn't exits, creates it.

    :param user_db_port: Port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: Datetime.datetime of last update or None
    """
    query = ("select update_time\n"
             "from Sources\n"
             "where dbname = 'meta'\n")
    update_time = None

    try:
        conn = db_acc.connect_to_user_database(DATABASE_NAME, user_db_port, user, password)
        with conn.cursor() as cur:
            cur.execute(query)
            update_time = cur.fetchone()[0]
            return update_time
    except pymysql.err.OperationalError:
        print('Wikiprojects update checker: failure, please establish connection to Toolforge')
        exit(1)


def update_local_db(update_time, user_db_port=None, user=None, password=None):
    """
    Saves new update time for meta table, creating corresponding row if needed.

    :param update_time: Datetime.datetime, time of last update for meta table
    :param user_db_port: Port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """
    query = ("insert into Sources(dbname, update_time) values('meta', %s)\n"
             "on duplicate key update update_time = %s"
             )
    try:
        conn = db_acc.connect_to_user_database(DATABASE_NAME, user_db_port, user, password)
        with conn.cursor() as cur:
            time = update_time.strftime('%Y-%m-%d %H:%M:%S')
            cur.execute(query, [time, time])
        conn.commit()
        conn.close()
    except pymysql.err.OperationalError:
        print('Wikiprojects update checker: failure, please establish connection to Toolforge')
        exit(1)


def update_checker(replicas_port=None, user_db_port=None, user=None, password=None):
    wiki_db_update_time = get_creation_date_from_db(replicas_port, user, password)
    print('Wikiprojects update checker: time of last update fetched from database')
    local_db_update_time = get_last_update_local_db(user_db_port, user, password)
    print('Wikiprojects update checker: local time of last update fetched')
    if local_db_update_time is not None:
        if wiki_db_update_time == local_db_update_time:
            print('Wikiprojects update checker: update not needed')
            return

    db_info = get_wikipages_from_db(replicas_port, user, password)
    print('Wikiprojects update checker: wikilinks info fetched from db')
    save_links_to_db(db_info, user_db_port, user, password)
    print('Wikiprojects update checker: wikipages links updated in db')
    update_local_db(wiki_db_update_time, user_db_port, user, password)
    print('Wikiprojects update checker: update finished')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Updates wiki info stored in database in Toolforge. "
                    "To use from local PC, use flag --local and all the additional flags needed for Ad"
                    "establishing connection through ssh tunneling."
                    "More help available at "
                    "https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#SSH_tunneling_for_local_testing_which_makes_use_of_Wiki_Replica_databases"
    )
    parser.add_argument("--local", "-l", action="store_true",
                        help="Connection is initiated from local pc.")
    local_data = parser.add_argument_group(title="Info for connecting to Toolforge from local pc")
    local_data.add_argument("--replicas-port", "-r", type=int,
                            help="Port for connecting to meta table through ssh tunneling, if used.")
    local_data.add_argument("--user-db-port", "-udb", type=int,
                            help="Port for connecting to tables, created by user in Toolforge, "
                                 "through ssh tunneling, if used.")
    local_data.add_argument("--user", "-u", type=str,
                            help="Toolforge username of the tool.")
    local_data.add_argument("--password", "-p", type=str,
                            help="Toolforge password of the tool.")
    args = parser.parse_args()

    if not args.local:
        update_checker()
    else:
        update_checker(args.replicas_port, args.user_db_port, args.user, args.password)

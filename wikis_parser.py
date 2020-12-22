import toolforge
import pymysql.err
import pandas as pd
import os.path

CSV_LINKS = 'wikipages.csv'
CSV_UPDATE_TIME = 'update_time.csv'

DATABASE_NAME = 's54588__data'

def get_wikipages_from_db():
    """
    Requests all names of the databases and linked urls for all working Wikimedia projects.

    :return: ((dbname1, url1), (dbname2, url2),...)
    """
    query = ("\n"
             "    select dbname, url\n"
             "    from wiki\n"
             "    where is_closed = 0")

    conn = toolforge.connect('meta')
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def get_creation_date_from_db():
    """
    Requests date of the creation of the meta table (which seems to be the date of the update).

    :return: Datetime.datetime
    """
    query = ("\n"
             "    select create_time\n"
             "    from INFORMATION_SCHEMA.TABLES\n"
             "    where table_name = 'wiki'")
    try:
        conn = toolforge.connect('meta')
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchone()[0]
    except pymysql.err.OperationalError:
        print('Wikiprojects update checker: failure, please use only in Toolforge environment')
        exit(1)


def save_links_to_db(entries):
    """
    Saves links and dbnames to the local project database.

    :param entries: List(tuple) of lists(tuples), with pairs 'dbname - url'
    :return: None
    """
    query = ("if not exists ("
             "select 1 from Sources where dbname = %s)"
             "begin"
             "insert into Sources(dbname, url) values(%s, %s)"
             "end;")
    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            for elem in entries:
                cur.execute(query, elem[0], elem[0], elem[1])
        conn.commit()
        conn.close()
    except pymysql.err.OperationalError:
        print('Wikiprojects update checker: failure, please use only in Toolforge environment')
        exit(1)


def save_links_to_csv(entries):
    """
    Creates file with 'dbname - url' pairs and saves them here in csv format.

    :param entries: List(tuple) of lists(tuples), with pairs 'dbname - url'
    :return: None
    """
    entries_df = pd.DataFrame(entries, columns=['dbname', 'url'])
    entries_df.to_csv(CSV_LINKS, mode='w', header=True, index=False)


def get_last_update_local_db():
    """
    Looks into csv with last update times and fetches last update time for meta table, if it is stored.
    If such file doesn't exits, creates it.

    :return: Datetime.datetime of last update or None
    """
    query = ("select update_time"
             "from Sources"
             "where dbname = 'meta'")
    update_time = None

    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute(query)
            update_time = cur.fetchone()
            print(update_time)
        return update_time
    except pymysql.err.OperationalError:
        print('Wikiprojects update checker: failure, please use only in Toolforge environment')
        exit(1)



def get_last_update_local():
    """
    Looks into csv with last update times and fetches last update time for meta table, if it is stored.
    If such file doesn't exits, creates it.

    :return: Datetime.datetime of last update or None
    """
    if os.path.exists(CSV_UPDATE_TIME):
        df = pd.read_csv(CSV_UPDATE_TIME)
        if 'meta' in df.values:
            update_time = df.loc[df['dbname'] == 'meta', 'update_time'].iloc[0]
            return update_time
        return None
    else:
        with open(CSV_UPDATE_TIME, "w") as file:
            file.write('dbname,update_time\n')
        return None


def update_local_db(update_time):
    """
    Saves new update time for meta table, creating corresponding row if needed.

    :param update_time: Datetime.datetime, time of last update for meta table
    :return: None
    """
    df = pd.read_csv(CSV_UPDATE_TIME)
    if 'meta' in df.values:
        df.loc[df['dbname'] == 'meta', 'update_time'] = update_time
        df.to_csv(CSV_UPDATE_TIME, mode='w', header=True, index=False)
    else:
        update_time_df = pd.DataFrame([['meta', update_time]], columns=['dbname', 'update_time'])
        update_time_df.to_csv(CSV_UPDATE_TIME, mode='a', header=False, index=False)


def update_checker():
    wiki_db_update_time = get_creation_date_from_db()
    print('Wikiprojects update checker: time of last update fetched from database')
    local_db_update_time = get_last_update_local()
    get_last_update_local_db()
    print('Wikiprojects update checker: local time of last update fetched')
    if local_db_update_time is not None:
        if wiki_db_update_time == local_db_update_time:
            print('Wikiprojects update checker: update not needed')
            return

    db_info = get_wikipages_from_db()
    print('Wikiprojects update checker: wikilinks info fetched from db')
    save_links_to_db(db_info)
    print('Wikiprojects update checker: wikipages links updated in db')
    save_links_to_csv(db_info)
    print('Wikiprojects update checker: wikipages links updated')
    update_local_db(wiki_db_update_time)
    print('Wikiprojects update checker: update finished')


if __name__ == '__main__':
    update_checker()

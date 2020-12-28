import toolforge
import pandas as pd
import pymysql
import argparse


DATABASE_NAME = 's54588__data'


def save_to_db(entries, db, user_db_port=None, user=None, password=None):
    query = ("insert into Scripts(dbname, page_id, title, in_database) "
             "             values(%s, %s, %s, %s)\n"
             "on duplicate key update in_database = %s"
             )
    try:
        if user_db_port:
            conn = pymysql.connect(host='127.0.0.1', port=user_db_port,
                                   user=user, password=password)
        else:
            conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute("use " + DATABASE_NAME)
            for index, elem in entries.iterrows():
                cur.execute(query,
                            [db, elem['page_id'], elem['page_title'], 1, 1])
        conn.commit()
        conn.close()
    except pymysql.err.OperationalError:
        print('Failure: failure, please establish connection to Toolforge')
        exit(1)


def encode_if_necessary(b):
    if type(b) is bytes:
        return b.decode('utf8')
    return b


def get_dbs(user_db_port=None, user=None, password=None):
    try:
        if user_db_port:
            conn = pymysql.connect(host='127.0.0.1', port=user_db_port,
                                   user=user, password=password)
        else:
            conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute("use " + DATABASE_NAME)
            cur.execute("select dbname from Sources where url is not NULL")  # all, except 'meta'
            ret = [db[0] for db in cur]
        conn.close()
        return ret
    except pymysql.err.OperationalError as err:
        print('Failure: failure, please establish connection to Toolforge')
        exit(1)


def get_data(dbs, replicas_port=None, user_db_port=None, user=None, password=None):
    ## Get all pages
    for db in dbs:
        try:
            ## Connect
            if replicas_port:
                conn = pymysql.connect(host='127.0.0.1', port=replicas_port,
                                       user=user, password=password)
            else:
                conn = toolforge.connect(dbname=db)
            with conn.cursor() as cur:
                ## Query
                cur.execute("USE " + db + '_p')
                SQL_Query = pd.read_sql_query("SELECT page_id,page_title FROM page \
                    WHERE page_content_model='Scribunto' AND page_namespace=828", conn)
                df_page = pd.DataFrame(SQL_Query, columns=['page_id', 'page_title']).applymap(encode_if_necessary)

                # Saving to db
                save_to_db(df_page, db, user_db_port, user, password)
                print('Finished loading scripts from ', db)
            conn.close()
        except Exception as err:
            print('Error loading pages from db: ', db, '\nError:', err)

    print("Done loading from databases.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Updates wiki info stored in database in Toolforge. "
                    "To use from local PC, use flag --local and all the additional flags needed for Ad"
                    "establishing connection through ssh tunneling."
                    "More help available at "
                    "https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#SSH_tunneling_for_local_testing_which_makes_use_of_Wiki_Replica_databases"
    )
    parser.add_argument("--local", "-l", action="store_true",
                        help="Connection is initiated from local pc.")
    local_data = parser.add_argument_group(title="Info for connecting to Toolforge from local pc.")
    local_data.add_argument("--replicas-port", "-r", type=int,
                            help="Port for connecting to meta table through ssh tunneling, if used.")
    local_data.add_argument("--user-db-port", "-udb", type=int,
                            help="Port for connecting to local Sources table through ssh tunneling, if used.")
    local_data.add_argument("--user", "-u", type=str,
                            help="Toolforge username of the tool.")
    local_data.add_argument("--password", "-p", type=str,
                            help="Toolforge password of the tool.")
    args = parser.parse_args()

    if not args.local:
        dbs = get_dbs()
        get_data(dbs)
    else:
        dbs = get_dbs(args.user_db_port, args.user, args.password)
        get_data(dbs, args.replicas_port, args.user_db_port, args.user, args.password)

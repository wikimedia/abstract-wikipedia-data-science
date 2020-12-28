import toolforge
import pandas as pd
import pymysql

DATABASE_NAME = 's54588__data'


def save_to_db(entries, db):
    query = ("insert into Scripts(dbname, page_id, title, in_database) "
             "             values(%s, %s, %s, %s)\n"
             "on duplicate key update in_database = %s"
             )
    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            for index, elem in entries.iterrows():
                cur.execute(query,
                            [db, elem['page_id'], elem['page_title'], 1, 1])
        conn.commit()
        conn.close()
    except pymysql.err.OperationalError:
        print('Failure: please use only in Toolforge environment')
        exit(1)


def encode_if_necessary(b):
    if type(b) is bytes:
        return b.decode('utf8')
    return b


def get_dbs():
    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute("select dbname from Sources where url is not NULL")    # all, except 'meta'
            ret = [db[0] for db in cur]
        conn.close()
        return ret
    except pymysql.err.OperationalError as err:
        print('Failure: please use only in Toolforge environment')
        exit(1)


def get_data(dbs):
    ## Get all pages
    for db in dbs:
        try:
            ## Connect
            conn = toolforge.connect(dbname=db)
            with conn.cursor() as cur:
                ## Query
                cur.execute("USE "+db+'_p')
                SQL_Query = pd.read_sql_query("SELECT page_id, page_title, page_is_redirect, page_is_new FROM page \
                    WHERE page_content_model='Scribunto' AND page_namespace=828", conn)
                df_page = pd.DataFrame(SQL_Query).applymap(encode_if_necessary)

                # Saving to db
                save_to_db(df_page, db)
                print('Finished loading scripts from ', db)
            conn.close()
        except Exception as err:
                print('Error loading pages from db: ', db, '\nError:', err)

    print("Done loading from databases.")

if __name__ == "__main__":
    
    dbs = get_dbs()
    get_data(dbs)
    
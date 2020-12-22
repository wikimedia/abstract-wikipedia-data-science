import toolforge
import pandas as pd
import pymysql

DATABASE_NAME = 's54588__data'


def save_to_db(entries):
    query = ("if not exists ("
             "select 1 from Scripts where page_id = %s)"
             "begin"
             "insert into Scripts(dbname, page_id, title, touched, in_database)"
             "             values(%s, %s, %s, %s, %s)"
             "end"
             "else"
             "begin"
             "update Scripts set in_database = %s where page_id = %s"
             "end"
             "endif;")
    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            for elem in entries:
                cur.execute(query, elem['page_id'],
                            elem['db'], elem['page_id'], elem['page_title'], elem['page_touched'], 1,
                            1, elem['page_id'])
        conn.commit()
        conn.close()
    except pymysql.err.OperationalError:
        print('Wikiprojects update checker: failure, please use only in Toolforge environment')
        exit(1)


def encode_if_necessary(b):
    if type(b) is bytes:
        return b.decode('utf8')
    return b

## Connect
conn = toolforge.toolsdb(DATABASE_NAME)

## List databases
dbs = []
with conn.cursor() as cur:
    cur.execute("select dbnames from Sources where url is not NULL")    # all, except 'meta'
    for db in cur:
        dbs.append(db[0])

## Get all pages
with conn.cursor() as cur:
    for db in dbs:
        cur.execute("use "+db)
        try:
            SQL_Query = pd.read_sql_query("select page_id, page_title, page_touched from page where page_content_model='Scribunto'", conn)
            df_page = pd.DataFrame(SQL_Query, columns=['page_id', 'page_title', 'page_touched'])\
                .applymap(encode_if_necessary)
            df_page['db'] = db
            df_page.to_csv('wiki_pages_db.csv', mode='a', header=False, index=False)

            # saving to db
            save_to_db()
        except:
            print('Error loading pages from db: ', db)
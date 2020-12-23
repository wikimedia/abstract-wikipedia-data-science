import toolforge
import pandas as pd
import pymysql

DATABASE_NAME = 's54588__data'


def save_to_db(entries):
    query = ("insert into Scripts(dbname, page_id, title, touched, in_database) "
             "             values(%s, %s, %s, %s, %s)\n"
             "on duplicate key update in_database = %s"
             )
    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            for index, elem in entries.iterrows():
                cur.execute(query,
                            [elem['db'], elem['page_id'], elem['page_title'], elem['page_touched'], 1, 1])
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
    cur.execute("select dbname from Sources where url is not NULL")    # all, except 'meta'
    for db in cur:
        dbs.append(db[0])

conn = toolforge.connect('meta')
## Get all pages
with conn.cursor() as cur:
    for db in dbs:
        cur.execute("use " + db +"_p")
        try:
            SQL_Query = pd.read_sql_query("select page_id, page_title, page_touched from page where page_content_model='Scribunto'", conn)
            df_page = pd.DataFrame(SQL_Query, columns=['page_id', 'page_title', 'page_touched'])\
                .applymap(encode_if_necessary)
            df_page['db'] = db
            df_page.to_csv('wiki_pages_db.csv', mode='a', header=False, index=False)

            # saving to db
            save_to_db(df_page)
            print('Finished loading scripts from ', db)
        except Exception as err:
            print('Error loading pages from db: ', db, '\nError:', err)
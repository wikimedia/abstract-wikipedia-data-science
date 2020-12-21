import toolforge
import pandas as pd

def encode_if_necessary(b):
    if type(b) is bytes:
        return b.decode('utf8')
    return b

## Connect
conn = toolforge.connect('meta')

## List databases
dbs = []
with conn.cursor() as cur:
    cur.execute("show databases")
    for db in cur:
        dbs.append(db[0])

## Get all pages
with conn.cursor() as cur:
    for db in dbs:
        cur.execute("use "+db)
        try:
            SQL_Query = pd.read_sql_query("select page_id,page_title,page_latest  from page where page_content_model='Scribunto'", conn)
            df_page = pd.DataFrame(SQL_Query, columns=['page_id','page_title','page_latest'])\
                .applymap(encode_if_necessary)
            df_page['db'] = db
            df_page.to_csv('wiki_pages_db.csv', mode='a', header=False, index=False)
        except:
            print('Error loading pages from db: ', db)
import toolforge
import datetime
import pandas as pd
import os.path

CSV_LINKS = 'wikipages.csv'
CSV_UPDATE_TIME = 'update_time.csv'


def get_wikipages_from_db():
    query = ("\n"
             "    select dbname, url\n"
             "    from wiki\n"
             "    where is_closed = 0")

    conn = toolforge.connect('meta')
    with conn.cursor() as cur:
        print(cur.fetchone())
        cur.execute(query)
        return cur.fetchall()


def get_creation_date_from_db():
    query = ("\n"
             "    select create_time\n"
             "    from INFORMATION_SCHEMA.TABLES\n"
             "    where table_name = 'wiki'")

    conn = toolforge.connect('meta')
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchone()[0]


def save_links_to_csv(entries):
    with open(CSV_LINKS, 'w') as file:
        file.write('dbname,url\n')
        for entry in entries:
            file.write(entry[0] + ',' + entry[1] + '\n')


def get_last_update_local():
    if os.path.exists(CSV_UPDATE_TIME):
        df = pd.read_csv(CSV_UPDATE_TIME)
        if 'meta' in df.values:
            update_time = df.loc[df['dbname'] == 'meta', 'update_time'].item()
            return update_time
        return None
    else:
        with open(CSV_UPDATE_TIME, "w") as file:
            file.write('dbname,update_time')
        return None



def update_checker():
    wiki_db_update_time = get_creation_date_from_db()




if __name__ == '__main__':
    get_creation_date_from_db()
    #db_info = get_wikipages_from_db()
    #save_links_to_csv(db_info)

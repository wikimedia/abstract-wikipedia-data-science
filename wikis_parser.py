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


def update_local_db(update_time):
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
    print('Wikiprojects update checker: local time of last update fetched')
    if local_db_update_time is not None:
        local_db_update_time = pd.to_datetime(local_db_update_time, yearfirst=True)
        if wiki_db_update_time == local_db_update_time:
            print('Wikiprojects update checker: update not needed')
            return

    db_info = get_wikipages_from_db()
    print('Wikiprojects update checker: wikilinks info fetched from db')
    save_links_to_csv(db_info)
    print('Wikiprojects update checker: wikipages links updated')
    update_local_db(wiki_db_update_time)
    print('Wikiprojects update checker: update finished')


if __name__ == '__main__':
    update_checker()

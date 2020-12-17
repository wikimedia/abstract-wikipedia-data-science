import toolforge

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
        print(cur.fetchone())


def save_links_to_csv(entries):
    with open(CSV_LINKS, 'w') as file:
        file.write('dbname,url\n')
        for entry in entries:
            file.write(entry[0] + ',' + entry[1] + '\n')


def update_checker():
    pass



if __name__ == '__main__':
    get_creation_date_from_db()
    #db_info = get_wikipages_from_db()
    #save_links_to_csv(db_info)

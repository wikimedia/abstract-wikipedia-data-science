import toolforge

CSV_FILENAME = 'wikipages.csv'


def get_wikipages_from_db():
    query = ("\n"
             "    select dbname, url\n"
             "    from wiki\n"
             "    where is_closed = 0")

    conn = toolforge.connect('meta')
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def save_links_to_csv(entries):
    with open(CSV_FILENAME, 'w') as file:
        file.write('dbname, url\n')
        for entry in entries:
            file.write(entry[0] + ',' + entry[1] + '\n')


if __name__ == '__main__':
    db_info = get_wikipages_from_db()
    save_links_to_csv(db_info)

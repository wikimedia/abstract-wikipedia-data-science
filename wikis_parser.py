from bs4 import BeautifulSoup
import requests
import toolforge

WIKIMEDIA_WIKIS_PAGE = 'https://meta.wikimedia.org/wiki/Special:SiteMatrix'
TEXT_FILENAME = 'wikipages.txt'
CSV_FILENAME = 'wikipages.csv'


def get_wikipages_from_db():
    query = ("\n"
             "    select dbname, url\n"
             "    from wiki\n"
             "    where is_closed = 0")

    conn = toolforge.connect('meta')
    with conn.cursor() as cur:
        cur.execute(query)
        print(cur.fetchall())


def save_links_to_csv(entries):
    with open(CSV_FILENAME, 'w') as file:
        file.write('dbname, url\n')
        for entry in entries:
            file.write(entry[0] + ',' + entry[1] + '\n')


def save_links_to_txt(links):
    with open(TEXT_FILENAME, 'w') as textfile:
        for link in links:
            textfile.write(link + '\n')


if __name__ == '__main__':
    get_wikipages_from_db()
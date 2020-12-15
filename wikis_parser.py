from bs4 import BeautifulSoup
import requests
import toolforge

WIKIMEDIA_WIKIS_PAGE = 'https://meta.wikimedia.org/wiki/Special:SiteMatrix'
TEXT_FILENAME = 'wikipages.txt'


def get_wikipages_from_db():
    query = ("\n"
             "    select dbname, url\n"
             "    from wiki\n"
             "    where is_closed = 0")

    conn = toolforge.connect('meta')
    with conn.cursor() as cur:
        cur.execute(query)
        print(cur.fetchall())



def parse_table(table):
    # all the crossed out wikis
    deleted_links = table.find_all('del')

    # all the links to wikis, which don't exist (red link)
    nonexisting_links = table.find_all('a', attrs={'class': 'new'})

    # links to "main hubs" for each type of wiki, they are in headers
    col_name_links = table.find_all('th')

    for match in deleted_links + nonexisting_links + col_name_links:
        match.decompose()

    links = []
    for elem in table.find_all('a', href=True):
        if elem.text:
            links.append('https:' + elem['href'])

    return links


def save_links_to_txt(links):
    with open(TEXT_FILENAME, 'w') as textfile:
        for link in links:
            textfile.write(link + '\n')


if __name__ == '__main__':
    get_wikipages_from_db()
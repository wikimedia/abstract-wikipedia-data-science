from bs4 import BeautifulSoup
import requests
import mwapi
import toolforge


WIKIMEDIA_WIKIS_PAGE = 'https://meta.wikimedia.org/wiki/Special:SiteMatrix'
TEXT_FILENAME = 'wikipages.txt'
USER_INFO = 'LostEnchanter'
SITENAME = 'https://meta.wikimedia.org/'


def get_tables_from_db():
    query = """
        select
        site_global_key as db_name,
        site_group as project,
        site_language as language,
        concat("https://", trim(leading "." from reverse(site_domain))) as domain
        from enwiki.sites
        where site_group in (
        'betawikiversity', 'commons', 'incubator', 'labs', 'mediawiki', 'meta', 'outreach',
        'sources', 'species', 'wikibooks', 'wikidata', 'wikinews', 'wikipedia', 'wikiquote',
        'wikisource', 'wikiversity', 'wikivoyage', 'wiktionary'
)
    """
    conn = toolforge.connect('meta')  # You can also use "enwiki_p"
    # conn is a pymysql.connection object.
    with conn.cursor() as cur:
        cur.execute(query)



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
    get_tables_from_db()
    """
    try:
        page = requests.get(WIKIMEDIA_WIKIS_PAGE)
        page.raise_for_status()                         # so it will raise exception, if status code is not OK
        soup = BeautifulSoup(page.content, 'html.parser')

        main_table = soup.find('table', attrs={'id': 'mw-sitematrix-table'})        # get first wikitable
        main_table_links = parse_table(main_table)

        add_table = soup.find('table', attrs={'id': 'mw-sitematrix-other-table'})    # other wikimedia projects table
        add_table_links = parse_table(add_table)

        save_links_to_txt(main_table_links + add_table_links)

        print('Ok')

    except requests.exceptions.ConnectionError:
        print('Network error')
        exit(1)
    except requests.exceptions.Timeout:
        print('Page timeout, try again later')
        exit(1)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)
        """

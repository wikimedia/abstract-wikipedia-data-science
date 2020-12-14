from bs4 import BeautifulSoup
import requests

WIKIMEDIA_WIKIS_PAGE = 'https://meta.wikimedia.org/wiki/Special:SiteMatrix'


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


if __name__ == '__main__':
    page = requests.get(WIKIMEDIA_WIKIS_PAGE)
    soup = BeautifulSoup(page.content, 'html.parser')

    main_table = soup.find('table', attrs={'id': 'mw-sitematrix-table'})    # get first wikitable
    main_table_links = parse_table(main_table)




    print('Ok')

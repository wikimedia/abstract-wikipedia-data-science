from bs4 import BeautifulSoup
import requests

WIKIMEDIA_WIKIS_PAGE = 'https://meta.wikimedia.org/wiki/Special:SiteMatrix'

if __name__ == '__main__':
    page = requests.get(WIKIMEDIA_WIKIS_PAGE)
    soup = BeautifulSoup(page.content, 'html.parser')

    # get first wikitable
    table = soup.find('table', attrs={'id': 'mw-sitematrix-table'})

    # removes all the crossed out wikis
    deleted_links = table.find_all('del')
    for match in deleted_links:
        match.decompose()

    links = table.find_all('a', href=True)


    print('Ok')

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

    # removes all the links to wikis, which don't exist (red link)
    nonexisting_links = table.find_all('a', attrs={'class': 'new'})
    for match in nonexisting_links:
        match.decompose()

    # removes links to "main hubs" for each type of wiki, they are in headers
    col_name_links = table.find_all('th')
    for match in col_name_links:
        match.decompose()


    links = []
    for elem in table.find_all('a', href=True):
        if elem.text:
            links.append('https:' + elem['href'])


    print('Ok')

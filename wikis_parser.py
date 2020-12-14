from bs4 import BeautifulSoup
import requests

WIKIMEDIA_WIKIS_PAGE = 'https://meta.wikimedia.org/wiki/Special:SiteMatrix'

if __name__ == '__main__':
    page = requests.get(WIKIMEDIA_WIKIS_PAGE)
    soup = BeautifulSoup(page.text, 'html.parser')

    print('Ok')

import xml.etree.ElementTree as ET
from pywebcopy import save_webpage
import requests
from bs4 import BeautifulSoup
import re
import sys

if __name__ == "__main__":
    tree = ET.parse("novinky_cz/sitemap_articles_0.xml")
    root = tree.getroot()
    print(root)
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    loc_elements = root.findall(".//ns:loc", namespaces=namespace)
    i = 0
    for loc in loc_elements:
        match = re.search(r'(\d+)(?=\D*$)', loc.text)
        if match:
            last_number = match.group(1)
        else:
            print(f"No number found in the URL {loc.text}", file=sys.stderr)
            exit(1)
        #print(last_number)
        link = f"https://diskuze.seznam.cz/v3/novinky/discussion/www.novinky.cz%2Fclanek%2F{last_number}?sentinel=ahoj"
        print(link)
        #r = requests.get(link)
        #print(r.text)
        """
        soup = BeautifulSoup(r.text, "html.parser")
        data = soup.find('div', {'class', 'ogm-discussion-timeline'})
        for div in data.find_all('div', {'class': 'g_dG'}):
            div.decompose()
        for div in data.find_all('button', {'class': 'd_Y'}):
                div.decompose()
        print(f"<a href=\"{loc.text}\"><h2>Clanek</h2></a>")
        print(f"<a href=\"{link}\"><h2>Diskuze</h2></a>")
        print(data)
        break
        """

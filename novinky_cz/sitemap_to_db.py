SITEMAP="sitemap_articles_0.xml"
import xml.etree.ElementTree as ET
import main


def insert_article(conn, url, lastmod, changefreq, priority):
    cursor = conn.cursor()
    article_id = main.get_id_from_url(url)
    cursor.execute('''
        INSERT INTO ARTICLE (article_id, url, lastmod, changefreq, priority) 
        VALUES (?,?, ?, ?, ?)
    ''', (article_id, url, lastmod, changefreq, priority))
    conn.commit()

if __name__ == "__main__":
    db = main.db_init(DB_TEST)

    tree = ET.parse(SITEMAP)
    root = tree.getroot()
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    for url in root.findall('ns:url', namespace):
        loc = url.find('ns:loc', namespace).text
        lastmod = url.find('ns:lastmod', namespace).text
        changefreq = url.find('ns:changefreq', namespace).text
        priority = float(url.find('ns:priority', namespace).text)

        insert_article(db, loc, lastmod, changefreq, priority)
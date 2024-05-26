import sqlite3
import requests
from bs4 import BeautifulSoup
import json
from print_color import print
import xml.etree.ElementTree as ET
import re
import sys

DONE_LINKS_FILE = 'done_links.txt'
COMMENTS_DATA_QUERY = """
    query CommentsData($commentIds: [ID]!, $includeUnpublishedOfUserId_in: [ID]) {
          comments(
            id_in: $commentIds
            first: 500
            status_nin: [DELETED]
            includeUnpublishedOfUserId_in: $includeUnpublishedOfUserId_in
          ) {
            edges {
              node {
                ...CommentFragment
                __typename
              }
              __typename
            }
            __typename
          }
        }

        fragment CommentFragment on CommentNode {
          id
          content
          type
          createdDate
          editedDate
          parentCommentId
          referencedCommentId
          user {
            ...UserFragment
            __typename
          }
          __typename
        }

        fragment UserFragment on UserNode {
          id
          profilImage
          profilLink
          __typename
        }
    """
REPLIES_QUERY ="""
query CommentReplies($commentId: ID!, $after: String, $first: Int, $idNin: [ID], $secondarySort: [CommentNodeSortEnum]) {
    comments(parentCommentId: $commentId
    after: $after
    first: $first
    sort: $secondarySort
    status_nin: [DELETED]id_nin: $idNin) {
        edges {
            node {
                id
                replies: childComments(first: 900
                status_nin: [DELETED]sort: [CREATED_DATE_ASC]) {
                    edges {
                        node {
                            id
                        }
                    }
                    totalCount
                }
            }
        }
    }
}
"""
def db_init(db_name):
    conn = sqlite3.connect(db_name)
    conn.execute('''CREATE TABLE IF NOT EXISTS COMMENTS
             (comment_id    TEXT    PRIMARY KEY,
             article_id    LONG,
             content    TEXT,
             type   TEXT,
             createdDate  TEXT,
             editedDate   TEXT,
             parentCommentId        TEXT,
             referencedCommentId    TEXT,
             user_id    TEXT
             );''')
    conn.execute('''CREATE TABLE IF NOT EXISTS USERS
                (user_id           TEXT   PRIMARY KEY,
                profilImage    TEXT,
                profilLink     TEXT
                );''')

    return conn

def getListOfCommentsIdsHtml(article_url):
    response = requests.get(article_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('div', class_='g_dl')
        html_comment_ids = []
        for div in articles:
            data_dot_data = div.get('data-dot-data')
            if data_dot_data:
                #print(f"{json.loads(data_dot_data).get("commentId")}")
                html_comment_ids.append(json.loads(data_dot_data).get("commentId"))
            else:
                print("Found div without data-dot-data attribute", tag_color='red', color='magenta')
                print(div, tag_color='red')
                exit(404)
        return html_comment_ids
    else:
        print(f"Response error {response.status_code}", tag='failure', tag_color='red')
        exit(response.status_code)

def saveCommentsData(article_id, database, graph_url,comm_ids):
    # call the data
    variables = {
        "commentIds": comm_ids
    }
    payload = {
        "query": COMMENTS_DATA_QUERY,
        "variables": variables
    }
    response = requests.post(graph_url, json=payload)
    if response.status_code != 200:
        print(f"saveCommentsData error {response.status_code}", tag='failure', tag_color='red')
        exit(response.status_code)
    #zpracovani stahnutych
    data = json.loads(response.text)
    comments = data['data']['comments']['edges']
    for comment_edge in comments:
        comment = comment_edge['node']
        user = comment['user']

        database.execute('''
                INSERT INTO COMMENTS (comment_id, article_id, content, createdDate, editedDate, parentCommentId, referencedCommentId, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(comment_id) DO UPDATE SET
                    content=excluded.content,
                    article_id=excluded.article_id,
                    createdDate=excluded.createdDate,
                    editedDate=excluded.editedDate,
                    parentCommentId=excluded.parentCommentId,
                    referencedCommentId=excluded.referencedCommentId,
                    user_id=excluded.user_id
            ''', (comment['id'], article_id, comment['content'], comment['createdDate'], comment.get('editedDate'),
                  comment['parentCommentId'], comment['referencedCommentId'], user['id']))

        database.execute('''
               INSERT INTO USERS (user_id, profilImage, profilLink)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   profilImage=excluded.profilImage,
                   profilLink=excluded.profilLink
           ''', (user['id'], user['profilImage'], user['profilLink']))
        database.commit()
def addCommentReplies(parent_id,graph_url,html_comm_ids, recursive=True):
    variables = {
        "commentId": parent_id,
        "first": 80
    }
    payload = {
        "query": REPLIES_QUERY,
        "variables": variables
    }
    response = requests.post(graph_url, json=payload)
    if response.status_code != 200:
        print(f"addCommentReplies error {response.status_code}", tag='failure', tag_color='red')
        exit(response.status_code)

    # zpracovani stahnutych
    data = json.loads(response.text)
    for edge in data['data']['comments']['edges']:
        html_comm_ids.add(edge['node']['id'])
        if edge['node']['replies']['totalCount'] != 0:
            addCommentReplies(edge['node']['id'], graph_url, html_comm_ids, recursive)

def split_into_chunks(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def add_to_db(article_id, database, graph_url, article_url):
    html_comm_ids = getListOfCommentsIdsHtml(article_url)
    all_ids = set(html_comm_ids)
    for comment_id in html_comm_ids:
        addCommentReplies(comment_id,graph_url, all_ids, recursive=True)

    chunks = list(split_into_chunks(list(all_ids), 10))
    for chunk in chunks:
        saveCommentsData(article_id, database, graph_url, chunk)


def getDoneLinks():
    try:
        with open(DONE_LINKS_FILE, 'r') as file:
            done_links = file.read().splitlines()
            return set(done_links)
    except FileNotFoundError:
        return set()


def addToDoneLinks(article_id):
    with open(DONE_LINKS_FILE, 'a') as file:
        file.write(f"{article_id}\n")

if __name__ == "__main__":
    # get links from list
    GRAPHQL_URL = 'https://diskuze.seznam.cz/graphql'
    ARTICLE_URL = 'https://diskuze.seznam.cz/v3/novinky/discussion/www.novinky.cz%2Fclanek%2F40472815?sentinel=lwhg1npz-4f1fce38-52c3-456d-a8a1-c837529333d0'
    DB_TEST = 'test.db'
    db = db_init(DB_TEST)

    tree = ET.parse("sitemap_articles_0.xml")
    root = tree.getroot()
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    loc_elements = root.findall(".//ns:loc", namespaces=namespace)

    done_links = getDoneLinks()
    i = 0
    for loc in loc_elements:
        if i > 5:
            break
        match = re.search(r'(\d+)(?=\D*$)', loc.text)
        if not match:
            print(f"No number found in the URL {loc.text}", file=sys.stderr)
            exit(1)
        if match.group(1) not in done_links:
            url = f"https://diskuze.seznam.cz/v3/novinky/discussion/www.novinky.cz%2Fclanek%2F{match.group(1)}?sentinel=ahoj"
            print(f"Get data from  {url}")
            add_to_db( article_id= match.group(1),database=db, graph_url= GRAPHQL_URL, article_url = url)
            addToDoneLinks(match.group(1))
            i += 1
    db.close()

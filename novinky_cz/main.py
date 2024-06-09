import inspect
import sqlite3
import requests
from bs4 import BeautifulSoup
import asyncio
import json
from print_color import print
import xml.etree.ElementTree as ET
import re
import sys
import aiofiles as aiof
from novinky_db import *

DONE_LINKS_FILE = 'done_links.txt'
SITEMAP = "sitemap.xml"
GRAPHQL_URL = 'https://diskuze.seznam.cz/graphql'

COMMENTS_DATA_QUERY = """
    query CommentsData($commentIds: [ID]!) {
          comments(
            id_in: $commentIds
            first: 5000
            status_nin: [DELETED]
          ) {
            edges {
              node {
                ...CommentFragment
              }
            }
          }
        }

        fragment CommentFragment on CommentNode {
          id
          content
          createdDate
          editedDate
          parentCommentId
          referencedCommentId
          user {
            ...UserFragment
          }
        }

        fragment UserFragment on UserNode {
          id
          profilImage
          profilLink
        }
    """
REPLIES_QUERY = """
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
DISCUSSION_QUERY = """
query DiscussionComments($id: ID!, $after: String, $first: Int, $offset: Int, $sort: [CommentNodeSortEnum] = [CREATED_DATE_DESC], $repliesLimit: Int = 1, $commentsUserId: ID) {
  comments(
    discussionId: $id
    after: $after
    first: $first
    offset: $offset
    sort: $sort
    userId: $commentsUserId
    status_nin: [DELETED]
  ) {
    edges {
      node {
        id   
        meta: childComments(first: $repliesLimit, status_nin: [DELETED]) {
          totalCount
        }
      }
    }
    totalCount
  }
}
"""


def graphql_req(payload):
    response = requests.post(GRAPHQL_URL, json=payload)
    #print(payload)
    #print(response.text)
    if response.status_code != 200:
        print(f"{inspect.stack()[1].function} error {response.status_code}", tag='failure', tag_color='red')
        exit(response.status_code)
    return json.loads(response.text)


def extract_discussion_id(soup):
    script_tag = soup.find('script', id='ima-revival-cache')
    if script_tag:
        discussion_id = re.search(r'"discussion":\{\"id":\"(.*?)\",', script_tag.string)
        if discussion_id is None:
            return None
        return discussion_id.group(1)
    print("ma-revival-cache not found", tag_color='red')
    exit(15)


def getDiscussionComments(discussionId, comm_ids):
    chunk_size = 50
    offset = 0
    comm_count = 0
    while offset == 0 or offset < comm_count:
        variables = {"id": f"{discussionId}", "first": chunk_size, "repliesLimit": 0, "offset": offset}
        payload = {"query": DISCUSSION_QUERY, "variables": variables}

        data = graphql_req(payload)
        for edge in data['data']['comments']['edges']:
            comm_ids.add(edge['node']['id'])
            if edge['node']['meta']['totalCount'] != 0:
                addCommentReplies(edge['node']['id'], comm_ids, recursive=True)
        comm_count = data['data']['comments']['totalCount']
        offset += chunk_size


def getListOfCommentsIdsHtml(article_url, comm_ids):
    response = requests.get(article_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        discussionId = extract_discussion_id(soup)
        if discussionId:
            getDiscussionComments(discussionId=discussionId, comm_ids=comm_ids)
        else:
            print(f"{article_url} is None", tag='warning', tag_color='yellow')
    else:
        print(f"Response error {response.status_code}", tag='failure', tag_color='red')
        exit(response.status_code)


def saveCommentsData(article_id, database, comm_ids):
    variables = {"commentIds": comm_ids}
    payload = {"query": COMMENTS_DATA_QUERY, "variables": variables}
    data = graphql_req(payload)

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


def addCommentReplies(parent_id, html_comm_ids, recursive=True):
    variables = {"commentId": parent_id, "first": 80}
    payload = {"query": REPLIES_QUERY, "variables": variables}

    data = graphql_req(payload)
    for edge in data['data']['comments']['edges']:
        html_comm_ids.add(edge['node']['id'])
        if edge['node']['replies']['totalCount'] != 0:
            addCommentReplies(edge['node']['id'], html_comm_ids, recursive)


def split_into_chunks(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def add_to_db(article_id, database, article_url):
    comm_ids = set()
    getListOfCommentsIdsHtml(article_url, comm_ids)
    chunks = list(split_into_chunks(list(comm_ids), 42))
    for chunk in chunks:
        saveCommentsData(article_id, database, chunk)


def getDoneLinks():
    try:
        with open(DONE_LINKS_FILE, 'r') as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()


async def addToDoneLinks(article_id):
    async with aiof.open(DONE_LINKS_FILE, 'a') as file:
        await file.write(f"{article_id}\n")
        await file.flush()


def get_id_from_url(url):
    match = re.search(r'(\d+)(?=\D*$)', url)
    if not match:
        print(f"No number found in the URL {url}", file=sys.stderr)
        exit(1)
    return match.group(1)

def update_sitemap():
    url = "https://www.novinky.cz/sitemaps/sitemap_articles_1.xml"
    response = requests.get(url)
    if response.status_code == 200:
        with open("sitemap.xml", "wb") as file:
            file.write(response.content)
        print("Sitemap saved successfully.")
    else:
        print(f"Failed to download sitemap. Status code: {response.status_code}")


if __name__ == "__main__":

    db = db_init(DB_TEST)
    update_sitemap()
    tree = ET.parse("sitemap.xml")
    root = tree.getroot()
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    done_links = getDoneLinks()

    for i, loc in enumerate(root.findall(".//ns:loc", namespaces=namespace)):
        article_id = get_id_from_url(loc.text)
        if article_id not in done_links:
            url = f"https://diskuze.seznam.cz/v3/novinky/discussion/www.novinky.cz%2Fclanek%2F{article_id}?sentinel=ahoj"
            print(f"{i}:{url}")
            add_to_db(article_id=article_id, database=db, article_url=url)
            asyncio.run(addToDoneLinks(article_id))
    db.close()
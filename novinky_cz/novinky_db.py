import sqlite3

DB_TEST = 'results.db'


def db_init(db_name):
    conn = sqlite3.connect(db_name)
    conn.execute('''CREATE TABLE IF NOT EXISTS COMMENTS
             (comment_id    TEXT    PRIMARY KEY,
             article_id    LONG,
             content    TEXT,
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
    conn.execute('''CREATE TABLE IF NOT EXISTS ARTICLE
                        (article_id INTEGER PRIMARY KEY,
                        url TEXT NOT NULL,
                        lastmod TEXT,
                        changefreq TEXT,
                        priority REAL
                        );''')
    return conn
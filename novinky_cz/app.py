from flask import Flask, request, render_template, jsonify
from flask_graphql import GraphQLView
import graphene
from schema import schema
import sqlite3
import line_profiler

DATABASE = 'test.db'
app = Flask(__name__)

app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True
    )
)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    search_term = request.form['search_term']
    results_html = search_input(search_term)
    return render_template('index.html', results=results_html)


def search_input(comment_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT comment_id, parentCommentId FROM COMMENTS WHERE comment_id = ?", (comment_id,))
    root_comment = cursor.fetchone()

    if not root_comment:
        return f"<p>Comment {comment_id} not found.</p>"
    while True:
        parent_comment_id = root_comment[1]
        if parent_comment_id is None:
            break
        cursor.execute("SELECT comment_id, parentCommentId FROM COMMENTS WHERE comment_id = ?", (parent_comment_id,))
        root_comment = cursor.fetchone()
    comments_html = ""
    comments_html = get_childrens(comments_html=comments_html, cursor=cursor, comment_id=root_comment[0], level=0)
    conn.close()
    return comments_html

def add_comment_div(comments_html, cursor, comment_id, level):

    cursor.execute("SELECT * FROM COMMENTS WHERE comment_id = ?", (comment_id,))
    comment = cursor.fetchone()

    user_id = comment[7]
    user = fetch_user(user_id)
    hidden = ""
    if not comment[4]:
        hidden = "hidden"
    comment_div = f"""
    <div class="comment" style="margin-left: {level * 20}px;">
        <div  class="row" >
            <div class="column">
                <a href="{user['profileLink']}">
                    <img src="{user['profileImage']}" alt="Profile Image" />
                </a>
            </div>
            <div class="column">
                <div class="row">
                    <div class="column"><strong>ID:</strong> {comment[0]}</div>
                    <div class="column"><strong>Created:</strong> {comment[3]}</div>
                    <div class="column" {hidden} ><strong>Edited:</strong> {comment[4]}</div>
                </div>
                <div class="row">
                    <div class="column"><strong>Content:</strong> {comment[2]}</div>
                </div>
            </div>
        </div>
    </div>
    """
    comments_html += f"{comment_div}"
    return comments_html

def get_childrens(comments_html, cursor, comment_id, level):
    comments_html = add_comment_div(comments_html, cursor, comment_id, level)
    cursor.execute("SELECT comment_id FROM COMMENTS WHERE parentCommentId = ? ORDER BY createdDate", (comment_id,))
    children = cursor.fetchall()
    #print(f"{comment_id}:{len(children)} child size")
    for child in children:
        comments_html = get_childrens(comments_html, cursor, child[0], level+1)
    #print(len(comments_html))
    return comments_html

def fetch_user(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT profilImage, profilLink FROM USERS WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    return {
        "profileImage": user[0],
        "profileLink": user[1]
    }

if __name__ == '__main__':
    app.run(debug=True)

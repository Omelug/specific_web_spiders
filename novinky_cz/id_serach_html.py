from flask import Flask, request, render_template
import sqlite3
from jinja2 import Template

def searchInput(input):
    conn = sqlite3.connect('test.db')
    conn.row_factory = sqlite3.Row

    comment_tree = get_comment_tree(conn, input)
    if not comment_tree:
        return '<p>No comments found for the given ID.</p>'

    html_content = generate_comment_html(conn, comment_tree)
    return html_content


def get_comment_tree(conn, comment_id):
    root_comment = conn.execute('''
        SELECT * FROM COMMENTS WHERE comment_id = ?
    ''', (comment_id,)).fetchone()

    if not root_comment:
        return None

    all_comments = conn.execute('''
        SELECT * FROM COMMENTS
    ''').fetchall()

    comments_by_parent = {}
    for comment in all_comments:
        parent_id = comment['parentCommentId']
        if parent_id not in comments_by_parent:
            comments_by_parent[parent_id] = []
        comments_by_parent[parent_id].append(comment)

    def get_children(comment):
        children = comments_by_parent.get(comment['comment_id'], [])
        return {**comment, 'children': [get_children(child) for child in children]}
    comment_tree = get_children(root_comment)
    return comment_tree


def generate_comment_html(conn,comment_tree):
    template_str = '''
    <div class="comment">
        <div class="comment-header">
            <img src="{{ user.profilImage }}" alt="{{ user.user_id }}">
            <a href="{{ user.profilLink }}">{{ user.user_id }}</a>
        </div>
        <div class="comment-body">
            <p>{{ comment.content }}</p>
            <p><small>{{ comment.createdDate }}</small></p>
        </div>
        <div class="comment-children">
            {% for child in comment.children %}
                {{ generate_comment_html(child) }}
            {% endfor %}
        </div>
    </div>
    '''
    template = Template(template_str)

    def recursive_render(conn,comment):
        user = conn.execute('SELECT * FROM USERS WHERE user_id = ?', (comment['user_id'],)).fetchone()
        return template.render(comment=comment, user=user, generate_comment_html=recursive_render)

    return recursive_render(conn,comment_tree)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    search_term = request.form['search_term']
    results = searchInput(search_term)
    return render_template('results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)

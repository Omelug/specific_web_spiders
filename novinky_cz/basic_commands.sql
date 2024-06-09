SELECT
    COMMENTS.content,
    concat(USERS.profilLink, '/prispevek/',COMMENTS.comment_id)
FROM COMMENTS
    INNER JOIN ARTICLE ON COMMENTS.article_id = ARTICLE.article_id
    INNER JOIN USERS ON COMMENTS.user_id = USERS.user_id
WHERE content like "%slovo%" AND LENGTH(content) < 20;
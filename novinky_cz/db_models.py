from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Comment(Base):
    __tablename__ = 'COMMENTS'
    comment_id = Column(String, primary_key=True)
    article_id = Column(Integer)
    content = Column(Text)
    createdDate = Column(String)
    editedDate = Column(String)
    parentCommentId = Column(String, nullable=True)
    referencedCommentId = Column(String, nullable=True)
    user_id = Column(String, ForeignKey('USERS.user_id'))

class User(Base):
    __tablename__ = 'USERS'
    user_id = Column(String, primary_key=True)
    profileImage = Column(String)
    profileLink = Column(String)

import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from db_models import Comment as CommentModel, User as UserModel  # Updated

class Comment(SQLAlchemyObjectType):
    class Meta:
        model = CommentModel

class User(SQLAlchemyObjectType):
    class Meta:
        model = UserModel

class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    all_comments = graphene.List(Comment)

    def resolve_all_comments(self, info):
        query = Comment.get_query(info)
        return query.all()

schema = graphene.Schema(query=Query)

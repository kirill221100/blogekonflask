from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from time import time
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app.config import Config as cfg

db = SQLAlchemy()

posts_dislikes_assotiation = db.Table('posts_dislikes',
                                      db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
                                      db.Column("post_id", db.Integer, db.ForeignKey("post.id")))

posts_likes_assotiation = db.Table('posts_likes',
                                      db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
                                      db.Column("post_id", db.Integer, db.ForeignKey("post.id")))

notific_posts_assotiation = db.Table('notific_posts_ass',
                                      db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
                                      db.Column("notific_post_id", db.Integer, db.ForeignKey("notificpost.id")))


user_to_user = db.Table('user_to_user',
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id"), primary_key=True)
)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=True)
    password_hash = db.Column(db.String)
    avatar = db.Column(db.String)
    avatar_low = db.Column(db.String)
    bio = db.Column(db.String)
    posts = db.relationship('Post', back_populates='user')
    comments = db.relationship('Comment', back_populates='user')
    disliked = db.relationship("Post", secondary=posts_dislikes_assotiation, back_populates="dislikes")
    liked = db.relationship("Post", secondary=posts_likes_assotiation, back_populates="likes")
    notific_num = db.Column(db.Integer, default=0)
    notific_posts = db.relationship('NotificPost', secondary=notific_posts_assotiation, back_populates='users')
    notific_comments = db.relationship('NotificComment', back_populates='user')
    following = db.relationship("User",
                                secondary=user_to_user,
                                primaryjoin=id == user_to_user.c.follower_id,
                                secondaryjoin=id == user_to_user.c.followed_id,
                                backref="followed_by"
                                )
    @property
    def password(self):
        raise Exception('no')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            cfg.SECRET_KEY, algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, cfg.SECRET_KEY,
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    text = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    pic = db.Column(db.String)
    pic_low = db.Column(db.String)
    hashtags = db.Column(db.String)
    dislikes = db.relationship("User", secondary=posts_dislikes_assotiation, back_populates="disliked")
    likes = db.relationship("User", secondary=posts_likes_assotiation, back_populates="liked")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='posts')
    comments = db.relationship('Comment', back_populates='post')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    text = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    pic = db.Column(db.String)
    pic_low = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='comments')
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    post = db.relationship('Post', back_populates='comments')
    is_answer = db.Column(db.Boolean)
    answers = db.relationship('Comment', remote_side=[comment_id])

class NotificPost(db.Model):
    __tablename__ = 'notificpost'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer)
    text = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    users = db.relationship('User', secondary=notific_posts_assotiation, back_populates='notific_posts')

class NotificComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer)
    comment_id = db.Column(db.Integer)
    text = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='notific_comments')
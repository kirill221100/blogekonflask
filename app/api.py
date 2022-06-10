from flask_restful import Api, Resource, reqparse, request
from app.models import User, Post
from app import app, db
import base64, werkzeug
from io import BytesIO
from PIL import Image

api = Api(app)

class Posts(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('n', type=int, help='Num of posts', location='args')
        args = parser.parse_args()
        return {"Posts": [{'id': i.id,
                           'title': i.title,
                           'text': i.text,
                           'date': str(i.date),
                           'hashtags': i.hashtags,
                           'author': i.user.name,
                           'comments': [{'author': j.user.name,
                                         'text': j.text,
                                         'pic': j.pic,
                                         'date': str(j.date),
                                         'is_answer': j.is_answer} for j in i.comments]} for i in db.session.query(Post).join(User).limit(args['n']).all()[::-1]]}
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='Nickname', location='args')
        parser.add_argument('password', type=str, help='Password', location='args')
        parser.add_argument('title', type=str, help='Title', location='args')
        parser.add_argument('text', type=str, help='Text', location='args')
        parser.add_argument('hashtags', type=str, help='Hashtags', location='args')
        parser.add_argument('media', type=werkzeug.datastructures.FileStorage, help='Picture', location='files')
        args = parser.parse_args()
        user = db.session.query(User).filter(User.name == args['name']).first()
        if user.validate_password(args['password']):
            post = Post(title=args['title'], text=args['text'], hashtags=args['hashtags'], user=user)
            post.pic = base64.b64encode(args['media'].read()).decode('utf-8')
            by = BytesIO()
            img = Image.open(args['media']).convert('RGB')
            img.save(by, quality=10, format='JPEG', optimize=True)
            post.pic_low = base64.b64encode(by.getvalue()).decode('utf-8')
            db.session.add(post)
            db.session.commit()
            return {"result": 'success'}
        return {'result': 'fail'}

api.add_resource(Posts, '/api/posts')
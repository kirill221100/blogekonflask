from flask import session, redirect, request, url_for, render_template, flash
from app.models import User, Post, Comment, NotificPost, NotificComment
from app.emails import send_password_reset_email
from app import app, db
import base64
from PIL import Image
from io import BytesIO


@app.route('/')
def index():
    notifics = None
    if session.get('name'):
        user = db.session.query(User).filter(User.name == session['name']).first()
        notifics = user.notific_num
    page = request.args.get('page', 1, type=int)
    posts = db.session.query(Post).order_by(Post.id.desc()).paginate(page, 3, False)
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', posts=list(posts.items), next_url=next_url, prev_url=prev_url, notifics=notifics)

@app.route('/subs')
def subs():
    if not session.get('name'):
        return redirect(url_for('login'))
    user = db.session.query(User).filter(User.name == session['name']).first()
    page = request.args.get('page', 1, type=int)
    posts = db.session.query(Post).join(User).order_by(Post.id.desc()).filter(User.followed_by.contains(user)).paginate(page, 3, False)
    next_url = url_for('subs', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('subs', page=posts.prev_num) if posts.has_prev else None
    return render_template('subs.html', posts=list(posts.items), next_url=next_url, prev_url=prev_url, user=user)

@app.route('/rate/<int:post_id>/<string:rating>')
def rate(post_id, rating):
    post = db.session.query(Post).filter(Post.id == post_id).first()
    user = db.session.query(User).filter(User.name == session['name']).first()
    if rating == 'like':
        if user in post.dislikes:
            post.dislikes.remove(user)
        post.likes.append(user)

    elif rating == 'dislike':
        if user in post.likes:
            post.likes.remove(user)
        post.dislikes.append(user)

    elif rating == 'remove_like':
        post.likes.remove(user)

    elif rating == 'remove_dislike':
        post.dislikes.remove(user)

    db.session.commit()
    return redirect(url_for('post', id=post_id))

@app.route('/search', methods=["GET", "POST"])
def search():
    notifics = None
    if session.get('name'):
        user = db.session.query(User).filter(User.name == session['name']).first()
        notifics = user.notific_num
    if request.method == 'POST':
        posts = db.session.query(Post).filter(Post.hashtags.contains(request.form['search'].strip())).all()[::-1]
        return render_template('search.html', posts=posts, notifics=notifics)
    return render_template('search.html', notifics=notifics)

@app.route('/search_users', methods=["GET", "POST"])
def search_users():
    notifics = None
    if session.get('name'):
        user = db.session.query(User).filter(User.name == session['name']).first()
        notifics = user.notific_num
    if request.method == 'POST':
        users = db.session.query(User).filter(User.name.contains(request.form['search'].strip())).all()
        return render_template('search_users.html', users=users, notifics=notifics)
    return render_template('search_users.html', notifics=notifics)

@app.route('/answer/<int:post_id>/<int:id_ans>', methods=["POST"])
def answer(post_id, id_ans):
    if not session.get('name'):
        return redirect(url_for('login'))
    comment = db.session.query(Comment).filter(Comment.id == id_ans).first()
    user = db.session.query(User).filter(User.name == session['name']).first()
    post = db.session.query(Post).filter(Post.id == post_id).first()
    answer = Comment(user=user, is_answer=True, text=request.form['text'], post=post)
    if request.files.get('img'):
        if not request.files['img'].content_type == 'image/jpeg':
            flash('This file is not jpg')
            return redirect(url_for('post', id=post_id))
        answer.pic = base64.b64encode(request.files['img'].read()).decode("utf-8")
        by = BytesIO()
        img = Image.open(request.files['img'].stream)
        img.save(by, quality=35, format='JPEG', optimize=True)
        answer.pic_low = base64.b64encode(by.getvalue()).decode('utf-8')
    notific_com = NotificComment(post_id=post.id, user=comment.user,
                                 text=f'{user.name} answered you')
    comment.user.notific_num += 1
    db.session.add(comment, notific_com)
    notific_com.comment_id = comment.id
    db.session.add(answer)
    comment.answers.append(answer)
    db.session.commit()
    return redirect(url_for('post', id=post_id))

@app.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    if not session.get('name'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        user = db.session.query(User).filter(User.name == session['name']).first()
        post = db.session.query(Post).filter(Post.id == id).first()
        comment = Comment(text=request.form['text'], user=user, post=post)
        if request.files.get('img'):
            if not request.files['img'].content_type == 'image/jpeg':
                flash('This file is not jpg')
                return redirect(url_for('post', id=id))
            comment.pic = base64.b64encode(request.files['img'].read()).decode("utf-8")
            by = BytesIO()
            img = Image.open(request.files['img'].stream)
            img.save(by, quality=35, format='JPEG', optimize=True)
            comment.pic_low = base64.b64encode(by.getvalue()).decode('utf-8')
        notific_com = NotificComment(post_id=id, comment_id=comment.id, user=post.user, text=f'New comment from {user.name}')
        post.user.notific_num += 1
        db.session.add(comment, notific_com)
        notific_com.comment_id = comment.id
        db.session.commit()
        return redirect(url_for('post', id=id))
    return render_template('post.html', post=db.session.query(Post).filter(Post.id == id).first(), id=id, user=db.session.query(User).filter(User.name == session['name']).first())

@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    if not session.get('name'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        user = db.session.query(User).filter(User.name == session.get('name')).first()
        post = Post(title=request.form['subject'],
                    text=request.form['content'],
                    user=db.session.query(User).filter(User.name == session.get('name')).first())
        if request.form['hashtags']:
            post.hashtags = request.form['hashtags'].strip()
        if request.files.get('img'):
            if not request.files['img'].content_type == 'image/jpeg':
                flash('This file is not jpg')
                return redirect(url_for('newpost'))
            post.pic = base64.b64encode(request.files['img'].read()).decode("utf-8")
            by = BytesIO()
            img = Image.open(request.files['img'].stream)
            img.save(by, quality=35, format='JPEG', optimize=True)
            post.pic_low = base64.b64encode(by.getvalue()).decode('utf-8')
        db.session.add(post)
        if user.followed_by:
            notific_post = NotificPost(post_id=post.id, text=f'{user.name} created post')
            db.session.add(notific_post)
            for i in user.followed_by:
                i.notific_num += 1
                i.notific_posts.append(notific_post)
        db.session.commit()
        return redirect(url_for('post', id=post.id))
    return render_template('newpost.html', notifics=db.session.query(User).filter(User.name == session.get('name')).first().notific_num)

@app.route('/profile/<string:name>')
def profile(name):
    if not session.get('name'):
        return redirect(url_for('login'))
    user = db.session.query(User).filter(User.name == name).first()
    user1 = db.session.query(User).filter(User.name == session['name']).first()
    posts = db.session.query(Post).join(User).filter(User.name == name).all()
    return render_template('profile.html', user=user, posts=posts, user1=user1, name=name)

@app.route('/notific')
def notific():
    if not session.get('name'):
        return redirect(url_for('login'))
    user = db.session.query(User).filter(User.name == session.get('name')).first()
    user.notific_num = 0
    db.session.commit()
    return render_template('notific.html', user=user)

@app.route('/account', methods=['POST', 'GET'])
def account():
    if not session.get('name'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        req = request.form
        user = db.session.query(User).filter(User.name == session['name']).first()
        if request.files.get('img'):
            if not request.files['img'].content_type == 'image/jpeg':
                flash('This file is not jpg')
                return redirect(url_for('account'))
            user.avatar = base64.b64encode(request.files['img'].read()).decode("utf-8")
            by = BytesIO()
            img = Image.open(request.files['img'].stream)
            img.save(by, quality=10, format='JPEG', optimize=True)
            user.avatar_low = base64.b64encode(by.getvalue()).decode('utf-8')
        if req.get('username'):
            if db.session.query(User).filter(User.name == req['username']).first():
                flash('This username is registered')
                return redirect(url_for('account'))
            user.name = req['username']
            session['name'] = req['username']
        if req.get('bio'):
            user.bio = req['bio']
        if req.get('password'):
            user.password = req['password']
        db.session.commit()
        return redirect(url_for('account'))

    return render_template('account.html', user=db.session.query(User).filter(User.name == session.get('name')).first(), posts=db.session.query(Post).join(User).filter(User.name == session['name'])[::-1])

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if session.get('name'):
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = db.session.query(User).filter(User.name == request.form['username']).first()
        if user is None:
            flash("Incorrect nickname")
            return redirect(url_for('login'))
        if user.validate_password(request.form['password']):
            session['name'] = request.form['username']
            session['user_id'] = user.id
            return redirect(url_for('index'))
        flash("Incorrect password")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if session.get('name'):
        return redirect(url_for('index'))
    if request.method == 'POST':
        if db.session.query(User).filter(User.name == request.form['username']).first():
            flash('This username is registered')
            return redirect(url_for('signup'))
        if request.form['email'] and db.session.query(User).filter(User.email == request.form['email']).first():
            flash('This email is used')
            return redirect(url_for('signup'))
        usr = User(name=request.form['username'], password=request.form['password'], email=request.form['email'])
        session['name'] = request.form['username']
        session['user_id'] = usr.id
        db.session.add(usr)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('signup.html')

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if session.get('name'):
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if not user:
            flash('This email is not registered')
            return redirect(url_for('reset_password_request'))
        send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if session.get('name'):
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user.password = request.form['password']
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html')

@app.route('/logout')
def logout():
    if not session.get('name'):
        return redirect(url_for('login'))
    session.pop('name')
    session.pop('user_id')
    return redirect(url_for('login'))

@app.route('/pic')
def pic():
    return render_template('pic.html', pict=request.args.get('pict'))

@app.route('/sub/<user>/<user1>')
def sub(user, user1):

    usr = db.session.query(User).filter(User.name == user).first()
    usr1 = db.session.query(User).filter(User.name == user1).first()
    usr1.following.append(usr)
    db.session.commit()
    if request.args.get('post_id'):
        return redirect(url_for('post', id=request.args.get('post_id')))
    elif request.args.get('user_name'):
        return redirect(url_for('profile', name=request.args.get('user_name')))

@app.route('/unsub/<user>/<user1>')
def unsub(user, user1):
    usr = db.session.query(User).filter(User.name == user).first()
    usr1 = db.session.query(User).filter(User.name == user1).first()
    usr1.following.remove(usr)
    db.session.commit()
    if request.args.get('post_id'):
        return redirect(url_for('post', id=request.args.get('post_id')))
    elif request.args.get('user_name'):
        return redirect(url_for('profile', name=request.args.get('user_name')))

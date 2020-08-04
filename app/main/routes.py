from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from guess_language import guess_language
from app import db
import random
from app.main.forms import EditProfileForm, EmptyForm, PostForm
from app.models import User, Post
from app.translate import translate
from app.main import bp
from werkzeug.utils import secure_filename
import os
import boto3, botocore

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


def upload_file(file, bucket, filename, acl="public-read"):

    s3_client = boto3.client(
        's3',
        aws_access_key_id=current_app.config["S3_KEY"],
        aws_secret_access_key=current_app.config["S3_SECRET"])

    s3_client.upload_fileobj(
        file,
        bucket,
        filename,
        ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )

    return "{}{}".format(current_app.config["S3_LOCATION"], filename)

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():

        language = guess_language(form.post.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''


        if isinstance(form.filename.data, str):
            default_photos = ['black','blue','brown','green','orange', 'pink', 'purple', 'red', 'yellow']
            output = "http://grapeful-yes.s3.ap-northeast-2.amazonaws.com/default_photos/{}.jpg".format(default_photos[random.randint(1,len(default_photos)-1)])

            #s3.bucket("mycollection").objects(prefix:'photos/2017/', delimiter: '').collect(&:key)

            #https://grapeful-yes.s3.ap-northeast-2.amazonaws.com/default_photos/black.jpg
        else:
            filename = secure_filename(form.filename.data.filename)

            #f = request.files['file']
            #f.save(os.path.join(UPLOAD_FOLDER, f.filename))
            #upload_file(f"uploads/{f.filename}", BUCKET)
            #f = form.filename.data
            #f.save(os.path.join(current_app.config["UPLOAD_FOLDER"], f.filename))
            #upload_file(f"uploads/{f.filename}", current_app.config["S3_BUCKET"])
            #form.filename.data.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

            file = form.filename.data

            output = upload_file(file, current_app.config["S3_BUCKET"], filename)


        post = Post(title = form.title.data, body=form.post.data, author=current_user,
                    language=language, file_url=output)



        db.session.add(post)
        db.session.commit()


        flash(_('your post is now live!'))
        flash(_('some files (such as .heic) are currently not supported so may not appear'))

        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)

    posts = current_user.followed_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None

    return render_template('index.html', title=_('home'), form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)

    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None

    flash(_("click on other people's grapes to stalk on their accounts, click on your own to delete em"))
    return render_template('index.html', title=_('explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):

    user = User.query.filter_by(username=username).first_or_404()

    page = request.args.get('page', 1, type=int)

    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()

    return render_template('user.html', user=user, posts=posts.items, title=username,
                           next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('your changes have been saved'))
        return redirect(url_for('main.edit_profile'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    flash(_("here are your own grapes and the grapes of the accounts you follow"))
    return render_template('edit_profile.html', title=_('edit profile'),
                           form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('user %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('you cannot follow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(_('you are following %(username)s!', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('user %(username)s not found', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('you cannot unfollow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(_('you are not following %(username)s', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    p = Post.query.filter_by(id=id).first()
    db.session.delete(p)
    db.session.commit()
    return redirect(url_for('main.index'))

import os
import datetime
import json
from flask import Flask, render_template, redirect, request, flash, session, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import check_email, categories_change_json


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///videomemo.db"
app.config["SECRET_KEY"] = os.urandom(24)
app.config["JSON_AS_ASCII"] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

# データベース
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, nullable=False, unique=True)
    hash = db.Column(db.String, nullable=False)
    videos = db.relationship("Videos", back_populates="user")
    categories = db.relationship("Categories", back_populates="user")
    memos = db.relationship("Memos", back_populates="user")


class Videos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    videotitle = db.Column(db.String, nullable=False)
    url = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    categorie_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    user = db.relationship("Users", back_populates="videos")
    categorie = db.relationship("Categories", back_populates="video")
    memos = db.relationship("Memos", back_populates="video")


class Categories(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    categorie = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("Users", back_populates="categories")
    video = db.relationship("Videos", back_populates="categorie")


class Memos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    memotitle = db.Column(db.String, nullable=False)
    memo = db.Column(db.String)
    timestamp = db.Column(db.Integer, nullable=False)
    updatetime = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey("videos.id"), nullable=False)
    user = db.relationship("Users", back_populates="memos")
    video = db.relationship("Videos", back_populates="memos")


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@app.route("/", methods=["GET", "POST"])
def home():
    # sessionがない場合はlogin.htmlに移動
    if not session:
        return render_template("login.html")
    # session情報の取得
    user_id = session["user_id"]

    # マイページ
    if request.method == "GET":
        # userが保持してるカテゴリをすべて取得
        categories = db.session.query(Categories.id, Categories.categorie).filter_by(user_id=user_id).all()
        # カテゴリーをjsonに適した形に変換
        categories_json = categories_change_json(categories)
        # userが保持してるvideoをすべて取得
        videos = db.session.query(Videos.id, Videos.videotitle, Videos.url, Videos.categorie_id).filter_by(user_id=user_id).all()
        # memoをupdatetime順に並べ替え
        memos = db.session.query(Memos.video_id, Memos.updatetime).order_by(Memos.updatetime.desc()).all()
        # メモが存在する場合はvideo_idをキーとして最新順に保存
        updatetimes = {}
        # memos_countでメモの数を追跡
        memos_count = {}
        for memo in memos:
            if memo.video_id not in updatetimes:
                updatetimes[memo.video_id] = memo.updatetime
                memos_count[memo.video_id] = 1
            else:
                memos_count[memo.video_id] += 1
        # メモが存在しない場合はupdatetimeはNoneとして保存 memos_countは0にする
        for video in videos:
            if video.id not in updatetimes:
                updatetimes[video.id] = None
                memos_count[video.id] = 0
        return render_template("home.html", videos=videos, categories=categories, categories_json=categories_json, updatetimes=updatetimes, memos_count=memos_count)

    # 動画登録機能
    else:
        # userからタイトル・URL・カテゴリーを受け取る
        videotitle = request.form.get("videotitle")
        url = request.form.get("url")
        categorie = request.form.get("categorie")
        # エラー処理
        if not videotitle:
            flash("メモタイトルを入力してください")
            return render_template("create.html")
        if not url or len(url) != 28:
            flash("正しいurlを入力してください")
            return render_template("create.html")
        if not categorie:
            flash("ジャンルを入力してください")
            return render_template("create.html")

        # urlからyoutubeのidを取得
        url = url[17:28]

        # categorieが存在しない場合は新たに作成し追加する
        if not Categories.query.filter_by(categorie=categorie, user_id=user_id).first():
            new_categorie = Categories(categorie=categorie, user_id=user_id)
            db.session.add(new_categorie)
            db.session.commit()

        # 新たなvideoを作成しdbに追加
        # dbから該当するCategoriesの主キーを取得
        categorie = db.session.query(Categories.id).filter_by(categorie=categorie, user_id=user_id).first()
        new_video = Videos(videotitle=videotitle, url=url, user_id=user_id, categorie_id=categorie.id)
        db.session.add(new_video)
        db.session.commit()
        return redirect(url_for("home"))

# メニューからの動画登録用のルーティング
@app.route("/create")
@login_required
def create():
    user_id = session["user_id"]
    categories = db.session.query(Categories.categorie).filter_by(user_id=user_id).all()
    return render_template("create.html", categories=categories)

# 新規登録
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    else:
        # userからemailとpasswordを受け取る
        email = request.form.get("email")
        main_password = request.form.get("mainpassword")
        sub_password = request.form.get("subpassword")

        # emailやpasswordの入力がない場合などのエラー処理
        if not email or not check_email(email):
            flash("emailを入力してください")
            return render_template("register.html")
        if not main_password:
            flash("パスワードを入力してください")
            return render_template("register.html")
        if not sub_password:
            flash("パスワードを入力してください")
            return render_template("register.html")
        if main_password != sub_password:
            flash("同じパスワードを入力してください")
            return render_template("register.html")

        # hashの作成
        hash = generate_password_hash(main_password, method="sha512", salt_length=1000)
        new_user = Users(email=email, hash=hash)

        # usersテーブルに登録
        try:
            db.session.add(new_user)
            db.session.commit()
        # 登録できなかった場合
        except:
            flash("既にuserが存在します")
            return render_template("register.html")

        return redirect(url_for("login"))

# ログイン機能
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        # userからemailとpasswordを受け取る
        email = request.form.get("email")
        password = request.form.get("password")
        # エラー処理
        if not email or not check_email(email):
            flash("メールアドレスを入力してください。")
            return render_template("login.html")        
        if not password:
            flash("パスワードを入力してください。")
            return render_template("login.html")

        # データベースからuserのデータを取得
        user = Users.query.filter_by(email=email).first()

        # user が存在しないまたは保存されたhashとpasswordのhashが違う場合
        if not user or not check_password_hash(user.hash, password):
            flash("メールアドレスもしくはパスワードが間違っています。")
            return render_template("login.html")

        login_user(user)
        # sessionにuser_idを保持
        session["user_id"] = user.id
        return redirect(url_for("home"))

# ログアウト機能
@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("home"))

# 動画の詳細機能
@app.route("/detail/<int:id>")
@login_required
def detail(id):
    user_id = session["user_id"]
    # 動画の情報を取得
    video = Videos.query.get(id)
    video_url = "https://www.youtube.com/embed/" + video.url
    # 動画のカテゴリを取得
    categorie = Categories.query.get(video.categorie_id)
    # 動画と紐づくメモの取得
    memos = db.session.query(Memos.id, Memos.memotitle).filter_by(user_id=user_id, video_id=video.id).all()
    # メモが存在する場合はメモの情報を渡す
    if memos:
        return render_template("detail.html", video=video, categorie=categorie, video_url=video_url, memos=memos)
    # メモが存在しない場合はメモの情報は渡さない
    return render_template("detail.html", video=video, video_url=video_url, categorie=categorie)

# 動画のタイトル変更、ジャンル変更
@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    video = Videos.query.get(id)
    if request.method == "GET":    
        categorie = Categories.query.get(video.categorie_id)
        return render_template("edit.html", video=video, categorie=categorie)
    else:
        user_id = session["user_id"]
        videotitle = request.form.get("videotitle")
        categorie = request.form.get("categorie")
        
        if not videotitle:
            return render_template("edit.html")
        if not categorie:
            return render_template("edit.html")
        
        # カテゴリーが存在しない場合
        if not Categories.query.filter_by(categorie=categorie, user_id=user_id).first():
            new_categorie = Categories(categorie=categorie, user_id=user_id)
            db.session.add(new_categorie)
            db.session.commit()

        # videotitleとcategorieの変更の反映
        categorie = Categories.query.filter_by(categorie=categorie, user_id=user_id).first()
        tmp = video.categorie_id
        video.videotitle = videotitle
        video.categorie_id = categorie.id
        db.session.commit()

        # カテゴリーに含まれるvideoがなくなった時の処理
        if not Videos.query.filter_by(categorie_id=tmp, user_id=user_id).first():
            categorie = Categories.query.filter_by(id=tmp).first()
            db.session.delete(categorie)
            db.session.commit()
        return redirect("/")


# メモの詳細機能
@app.route("/detail/<int:id>/<int:memo_id>", methods=["GET", "POST"])
@login_required
def memodetail(id, memo_id):
    video = Videos.query.get(id)
    # 現在のメモ情報を取得(主キー)
    now_memo = Memos.query.get(memo_id)
    
    # 各メモを動画とともに表示する
    if request.method == "GET":
        user_id = session["user_id"]
        memos = Memos.query.filter_by(user_id=user_id, video_id=video.id).all()
        now_memo = Memos.query.get(memo_id)
        categorie = Categories.query.get(video.categorie_id)
        # メモのタイムスタンプの時間を秒に変換する
        memo_time = str(int(datetime.timedelta(hours=int(now_memo.timestamp[0:2]), minutes=int(now_memo.timestamp[3:5]), seconds=int(now_memo.timestamp[6:8])).total_seconds()))
        # メモのタイムスタンプとYoutubeのリンクを組み合わせる
        video_url = "https://www.youtube.com/embed/" + video.url + "?start=" + memo_time
        return render_template("movie.html", video=video, categorie=categorie, video_url=video_url, now_memo=now_memo, memos=memos)
    
    # メモのテキストを受け取り、それを保存していく
    else:
        memotext = request.form.get("memotext")
        now_memo.memo = memotext
        db.session.commit()
        return redirect(url_for("memodetail", id=video.id, memo_id=now_memo.id))

# メモの削除機能
@app.route("/delete/<int:id>/<int:memo_id>")
def memodelete(id, memo_id):
    memo = Memos.query.get(memo_id)
    db.session.delete(memo)
    db.session.commit()
    return redirect(url_for("detail", id=id))

# 動画の削除機能
@app.route("/delete/<int:id>")
@login_required
def delete(id):
    user_id = session["user_id"]
    video = Videos.query.get(id)
    memos = Memos.query.filter_by(user_id=user_id, video_id=video.id).all()
    # memoの削除
    for memo in memos:
        db.session.delete(memo)
    count = Videos.query.filter_by(categorie_id=video.categorie_id).count()
    if count == 1:
    # カテゴリーに登録されているのが削除するものだけの場合はカテゴリーも削除する
        categorie = Categories.query.get(video.categorie_id)
        db.session.delete(categorie)
    # videoの削除
    db.session.delete(video)
    db.session.commit()
    return redirect("/")

# メモのタイトルとタイムスタンプの変更機能
@app.route("/memoedit/<int:memo_id>", methods=["GET", "POST"])
@login_required
def memoedit(memo_id):
    memo = Memos.query.get(memo_id)
    if request.method == "GET":
        return render_template("memoedit.html", memo=memo)
    else:
        memotitle = request.form.get("memotitle")
        timestamp = request.form.get("timestamp")
        if not memotitle:
            flash("メモタイトルを入力してください。")
            return render_template("memoedit.html", memo=memo)
        if len(timestamp) != 8:
            flash("タイムスタンプを入力してください。")
            return render_template("memoedit.html", memo=memo)
        
        memo.memotitle = memotitle
        memo.timestamp = timestamp
        db.session.commit()
        return redirect(url_for("memodetail", id=memo.video_id, memo_id=memo.id))

# メモのタイムスタンプの登録機能
@app.route("/memo/<int:id>", methods=["GET", "POST"])
@login_required
def memo(id):
    video = Videos.query.get(id)
    if request.method == "GET":
        return render_template("memo.html", video=video)
    else:
        memotitle = request.form.get("memotitle")
        timestamp = request.form.get("timestamp")
        if len(timestamp) != 8:
            return render_template("memo.html", video=video)
        user_id = session["user_id"]
        video_id = video.id
        memo = ""
        updatetime = datetime.datetime.now()
        new_memo = Memos(memotitle=memotitle, memo=memo, timestamp=timestamp, updatetime=updatetime, user_id=user_id, video_id=video_id)
        db.session.add(new_memo)
        db.session.commit()
        return redirect(url_for("detail", id=video_id))
import os
from flask import Flask, render_template, redirect, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///videomemo.db"
app.config["SECRET_KEY"] = os.urandom(24)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

# データベース
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, nullable=False, unique=True)
    hash = db.Column(db.String, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("register.html")

# 新規登録
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        email = request.form.get("email")
        main_password = request.form.get("mainpassword")
        sub_password = request.form.get("subpassword")
        # usernameやpasswordの入力がない場合など
        if not email:
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

        try:
            db.session.add(new_user)
            db.session.commit()
        except:
            return render_template("register.html")

        flash("登録成功")
        return redirect("/login")

# ログイン機能
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        email = request.form.get("email")
        password = request.form.get("password")

        # email, passwordの入力がない場合
        if not email:
            flash("emailを入力してください")
            return render_template("login.html")
        if not password:
            flash("パスワードを入力してください")
            return render_template("login.html")

        # データベースからユーザーのデータを取得
        user = Users.query.filter_by(username=username).first()

        # 保存されたhashとpasswordのhashが同じか確認する
        if not check_password_hash(user.hash, password):
            flash("passwordが間違っています")
            return render_template("login.html")

        login_user(user)
        flash("ログイン成功")
        return redirect("/")

# ログアウト機能
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


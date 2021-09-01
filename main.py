import MySQLdb
from flask import Flask,render_template,redirect,request,url_for,session
from flask.globals import session
from flask.helpers import flash
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,BooleanField
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.utils import secure_filename
import os
from flask_images import Images
from flask import send_from_directory
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash(message="Bu sayfayı görüntülemek için giriş yapın!",category="danger")
            return redirect(url_for("login"))    
    return decorated_function
class PhotosForm(Form):
    name = StringField("Makalenizin adı")
    comment = StringField("Anahtar Kelimeler")
    content = TextAreaField("İçerik")
class RegisterForm(Form):
    username = StringField("Kullanıcı Adı")
    email = StringField("E mail",[validators.Email(message="Lütfen düzgün bir e-mail adresi girin.")])
    password = PasswordField("Parola",[validators.EqualTo("confirm.",message="Parolalar uyuşmuyor...")])
    confirm = PasswordField("Parola Doğrula")
    accept_tos = BooleanField("Sözleşme olmamasını kabul ediyorum :)",[validators.DataRequired()])

class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")
    accept_tos2 = BooleanField("Beni Hatırla")
app = Flask(__name__)
mysql = MySQL(app)
images = Images(app)
app.secret_key=("phocoo")
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root" 
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "phocoo"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/about")
def about():
    return render_template("about.html")
#KAYIT OLMA    
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST":
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        query = "INSERT INTO users(username,email,password) VALUES(%s,%s,%s)"
        cursor.execute(query,(username,email,password))
        mysql.connection.commit()
        cursor.close()
        flash(message="Kayıt Başarılı",category="success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)

#GİRİŞ YAPMA 
@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM  users WHERE username  = %s "
        result = cursor.execute(query,(username,))
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                
                session["logged_in"] = True
                session["username"] = username
                flash(message="Giriş Başarılı",category="success")
                return redirect(url_for("index"))
            else:
                flash(message="Kullanıcı adı veya parola yanlış",category="danger")
                return redirect(url_for("login"))
        else:
            flash(message="Kullanıcı Bulunamadı",category="danger")
            return redirect(url_for("login"))    
        
    else:
        return render_template("login.html",form=form)
@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash(message="Çıkış Başarılı",category="success")
    return redirect(url_for("index"))
@app.route("/articles",methods = ["GET","POST"])
def photos():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM photos"
    result = cursor.execute(query)
    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else:    
        return render_template("articles.html")
@app.route("/article/<string:id>")
@login_required
def photo(id):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM photos WHERE id = %s"
    result = cursor.execute(query,(id,))
    if result > 0 :
        photo = cursor.fetchone()
        return render_template("article.html",photo =photo)
    else:   
        return render_template("/articles.html")    
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM photos WHERE whose = %s"
    result = cursor.execute(query,(session["username"],))
    if result >0:
        photos = cursor.fetchall()
        return render_template("dashboard.html",photos=photos)
    else:
        return render_template("dashboard.html")          
@app.route("/upload",methods = ["GET","POST"])
@login_required
def upload():
    form = PhotosForm(request.form)
    cursor = mysql.connection.cursor()
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == "POST":
        name = form.name.data
        comment = form.comment.data
        content = form.content.data
        query = "INSERT INTO photos (name,comment,content,whose) VALUES(%s,%s,%s,%s)"
        cur.execute(query,(name,comment,content,session["username"]))
        mysql.connection.commit()
        cursor.close()
        flash(message="Makaleniz başarıyla yüklendi",category="success")
        return redirect(url_for("dashboard"))
    else:
        return render_template("upload.html",form = form)
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM photos where whose = %s and id =%s"
    delete = cursor.execute(query,(session["username"],id))
    if delete > 0 :
        result = "DELETE FROM photos where id = %s"
        cursor.execute(result,(id,))
        mysql.connection.commit()
        flash(message="Makaleniz başarıyla silinmiştir",category="success")
        return redirect(url_for("dashboard"))
    else:
        flash(message="Bunu yapmaya yetkiniz yok!",category="danger")
        return redirect(url_for("dashboard"))                
if __name__ == "__main__":
    app.run(debug=True)
from MySQLdb import cursors
from flask import  Flask, render_template,flash,redirect,url_for,session,request
import flask
from flask.templating import _render
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField, form,validators
from passlib.hash import sha256_crypt
from functools import wraps
import os
import sqlite3

#kullanıcı girişi decoratorları

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #if "logged_in" in session:
        if session["username"] == "Çağan Kılınç":
            return f(*args, **kwargs)
        elif "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Sayfayı Görüntülemek İçin Admin İzni Gerekmekte")
            return redirect(url_for("index"))

    return decorated_function

class RegisterForm(Form):
    name = StringField("İsim", validators = [validators.length(min=2, max= 25 )])
    username = StringField("Kullanıcı Adı", validators = [validators.length(min=6)])
    password = PasswordField("Parola", validators = [validators.DataRequired(message="Lütfen Bir Parola Belirleyin"),validators.EqualTo(fieldname= "confirm",message="Parolanız Uyuşmuyor")])
    confirm = PasswordField("Parolanızı Tektar Girin")

class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")

picFolder = os.path.join('static','pics')
voiFolder = os.path.join('static','song')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = picFolder
app.config['UPLOAD_FOLDERv'] = voiFolder

app.secret_key= "ckblog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ckblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app = app)

@app.route("/")
def index():

    song = os.path.join(app.config['UPLOAD_FOLDERv'],'Indila - Dernière Danse (Clip Officiel).mp3')
    return render_template("index.html",song = song)

@app.route("/about")
def about():
    pic1 = os.path.join(app.config['UPLOAD_FOLDER'],'IMG_20211010_231645_798.jpg')
    pic2 = os.path.join(app.config['UPLOAD_FOLDER'],'IMG_20210901_000218_426.jpg')

    return render_template("aboutme.html", user_image = pic1, user_image2 = pic2 )

@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles where author = %s"

    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template ("dashboard.html", articles = articles)

    else:
        return render_template("dashboard.html")
    


#Kayıt Ol
@app.route('/register', methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    
    if request.method  == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        sorgu = "Select * From users where username = %s"
        sorgu2 = "Select * From users where email = %s"

        result = cursor.execute(sorgu,(username,))
        result2 = cursor.execute(sorgu2,(email,))

        if result > 0:
            flash("Bu kullanıcı adına ait mevcut bir hesap bulunmakta!","danger")
            return redirect(url_for("register"))

        if result2 > 0:
            flash("Bu email hesabına ait mevcut bir hesap bulunmakta!","danger")
            return redirect(url_for("register"))
        

        sorgu = "Insert Into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        

        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()

        cursor.close()
        flash("Kayıt Oldunuz, Tebrikler!","success")

        return redirect(url_for("login"))
    
    else:
        return render_template("register.html", form = form)    
@app.route("/login",methods = ["GET","POST"])   
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM USERS WHERE username = %s"

        cursor.execute(sorgu,(username,))

        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
    
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Giriş Başarılı Oldu","success")
                session["logged_in"] = True
                session["username"] = username


            
                return redirect(url_for("index"))
            else:
                flash("Parolanızı Yanlış girdiniz","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle Bir Kullanıcı Bulunmuyor","danger")
            return redirect(url_for("login"))

    return render_template("login.html", form= form)


#Makale Detayları

@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where id = %s"
    result = cursor.execute(sorgu,(id,))
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article=article)
    else:
        return render_template("article.html")



#logout

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#makale ekleme

@app.route("/addarticle", methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()

        sorgu = "Insert Into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()

        cursor.close()

        flash("Makale Başarıyla Eklendi")

        return redirect(url_for("dashboard"))
    return render_template("addarticle.html", form = form)


#makale sayfası
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles"

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()

        return render_template("articles.html", articles = articles)
    else:
        return render_template("articles.html")

#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles where author = %s and id = %s"
    
    result = cursor.execute(sorgu,(session["username"],id,))

    
    if result > 0:
        sorgu2 = "Delete from articles where id = %s"

        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))

    else:
        flash("Böyle Bir Makale Yok | Bu İşleme Yetkiniz Yok")
        return redirect(url_for("index"))

#Makale Güncelleme
@app.route("/edit/<string:id>", methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sorgu = "Select * from articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))
        
        if result == 0:
            flash("Böyle Bir Makale Yok | Bu İşleme Yetkiniz Yok","danger")
            return redirect(url_for("index"))

        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html", form = form)

    else:
        #POST REQUEST
        form = ArticleForm(request.form)

        new_title = form.title.data
        new_content = form.content.data

        sorgu2 = "Update articles Set title = %s,content = %s where id = %s"

        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(new_title,new_content,id))

        mysql.connection.commit()
        flash("Makale başarıyla Güncellendi!","success")
        return redirect(url_for("dashboard"))

#Makale Form

class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators=[validators.Length(min=5 , max=100)])
    content = TextAreaField("Makale İçeriği", validators=[validators.Length(min=10)])
####################################################################################################################
class CommentForm(Form):
        title = StringField("Paylaşım Başlığı", validators=[validators.Length(min=5 , max=100)])
        content = TextAreaField("Paylaşım İçeriği", validators=[validators.Length(min=3)])


@app.route("/commentboard")
@login_required
def commentboard():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From comments where user = %s"

    result = cursor.execute(sorgu,(session["username"],))
    if (session["username"]) == "Çağan Kılınç":
        sorgu = "Select * From comments"
        result = cursor.execute(sorgu)
    else:
        pass
       

    if result > 0:
        comments = cursor.fetchall()
        return render_template ("commentboard.html", comments = comments)

    else:
        return render_template("commentboard.html")



@app.route("/comments")
def comments():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From comments"

    result = cursor.execute(sorgu)

    if result > 0:
        comments = cursor.fetchall()

        return render_template("comments.html", comments = comments)
    else:
        return render_template("comments.html")
    
@app.route("/comment/<string:id>")
def comment(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from comments where id = %s"
    result = cursor.execute(sorgu,(id,))
    if result > 0:
        comment = cursor.fetchone()
        return render_template("comment.html", comment=comment)
    else:
        return render_template("comment.html")


@app.route("/addcomment", methods = ["GET","POST"])
def addcomment():
    form2 = CommentForm(request.form)

    if request.method == "POST" and form2.validate():
        title = form2.title.data
        content = form2.content.data
        cursor = mysql.connection.cursor()

        sorgu = "Insert Into comments(title,user,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()

        cursor.close()

        flash("Paylaşım Başarıyla Eklendi")

        return redirect(url_for("commentboard"))
    return render_template("addcomments.html", form2 = form2)

@app.route("/deletec/<string:id>")
@login_required
def deletec(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * From comments where user = %s and id = %s"
    
    result = cursor.execute(sorgu,(session["username"],id,))
    if (session["username"]) == "Çağan Kılınç":
        sorgu = "Select * From comments"
        result = cursor.execute(sorgu)
    else:
        pass
       
    
    if result > 0:
        
        sorgu2 = "Delete from comments where id = %s"

        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        return redirect(url_for("commentboard"))

    else:
        flash("Böyle Bir Makale Yok veya  Bu İşleme Yetkiniz Yok")
        return redirect(url_for("index"))

@app.route("/editc/<string:id>", methods = ["GET","POST"])
@login_required
def updatec(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sorgu = "Select * from comments where id = %s and user = %s"
        result = cursor.execute(sorgu,(id,session["username"]))
        
        if result == 0:
            flash("Böyle Bir Makale Yok veya  Bu İşleme Yetkiniz Yok","danger")
            return redirect(url_for("index"))

        else:
            article = cursor.fetchone()
            form2 = CommentForm()

            form2.title.data = article["title"]
            form2.content.data = article["content"]
            return render_template("updatec.html", form2 = form2)

    else:
        #POST REQUEST
        form2 = CommentForm(request.form)

        new_title = form2.title.data
        new_content = form2.content.data

        sorgu2 = "Update comments Set title = %s,content = %s where id = %s"

        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(new_title,new_content,id))

        mysql.connection.commit()
        flash("Makale başarıyla Güncellendi!","success")
        return redirect(url_for("commentboard"))

@app.route("/searchc",methods = ["GET","POST"])
def searchc():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword1 = request.form.get("keyword1")

        cursor = mysql.connection.cursor()

        sorgu = f"Select * from comments where title like '%{keyword1}%'"

        result = cursor.execute(sorgu)
        if result == 0:
            flash("Aranan Kelimeye Uygun Makale Bulunamadı","warning")
            return redirect(url_for("comments"))
        else:
            comments = cursor.fetchall()
            return render_template("comments.html", comments = comments)      

#########################################################################################################################33

#arama url
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()

        sorgu = f"Select * from articles where title like '%{keyword}%'"

        result = cursor.execute(sorgu)
        if result == 0:
            flash("Aranan Kelimeye Uygun Makale Bulunamadı","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html", articles = articles)            

if __name__ == "__main__":
    app.run(debug=True)

    





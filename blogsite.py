from flask import Flask,render_template,session,flash,redirect,url_for,request,jsonify
from wtforms import Form,StringField,PasswordField,TextAreaField,validators
from flask_pymongo import PyMongo
from bson import ObjectId
from bson.json_util import dumps
import os
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime
# from flask import json

app = Flask(__name__)

# Configurations
app.config['MONGO2_DBNAME'] = 'blogsite'
app.config["MONGO_DBNAME"] = "blogsite"
app.config["MONGO_URI"] = "mongodb://localhost/blogsite"
app.secret_key = os.urandom(24)
# Initialiazing mongodb
mongo = PyMongo(app)



# Articles = Articles()

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/articles')
def articles():
	article = mongo.db.Articles
	articles = article.find()
	if articles:
		return render_template('articles.html',articles=articles)
	else:
		msg = 'No Article Found'
		return render_template('articles.html',msg)

@app.route('/article/<string:title>/')
def article(title):
	articles = mongo.db.Articles
	article = articles.find_one({"title":title})
	return render_template('article.html',article=article)

class Registration(Form):
	name = StringField('Name',[validators.Length(min=8,max=40)])
	username = StringField('Username',[validators.Length(min=1,max=20)])
	email = StringField('Email',[validators.Length(min=9,max=50)])
	password = PasswordField('Password',[
			validators.DataRequired(),
			validators.EqualTo('confirm',message='Password Must Match')
		])
	confirm = PasswordField('Repeat Password')

@app.route('/register',methods=['GET','POST'])
def register():
	form = Registration(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		username = form.username.data
		email = form.email.data
		password = sha256_crypt.encrypt(str(form.password.data))

		user = mongo.db.users
		user.insert_one({"name":name,"username":username,"email":email,"password":password})
		flash('You are now registered', 'success')
		return redirect(url_for('index'))
	return render_template('/register.html',form=form)
@app.route('/login',methods=['GET','POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password_candidate = request.form['password']

		user = mongo.db.users
		login_user = user.find({"username":username})
		if login_user:
			result = user.find_one()
			password = result['password']
			if sha256_crypt.verify(password_candidate, password):
				session['logged_in'] = True
				session['username'] = username
				flash('You are now logged in','success')
				return redirect(url_for('dashboard'))
			else:
				error = 'Invalid login'
			return render_template('login.html',error=error)
		else:
			error = 'Username not found'
			return render_template('login.html',error=error)
	return render_template('/login.html')

def is_logged_in(f):
	@wraps(f)
	def wrap(*args,**kwargs):
		if 'logged_in' in session:
			return f(*args,**kwargs)
		else:
			flash('Unauthorized, Please Log in', 'danger')
			return redirect(url_for('login'))
	return wrap
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are now logged out','success')
	return redirect(url_for('login'))


@app.route('/dashboard')
@is_logged_in
def dashboard():
	article = mongo.db.Articles
	articles = article.find({},{'_id':0})
	if articles:
		return render_template('dashboard.html',articles=articles)
	else:
		msg = 'No Article Found'
		return render_template('dashboard.html',msg)
	

class ArticleForm(Form):
	title = StringField('Title',[validators.Length(min=1,max=200)])
	body = TextAreaField('Body',[validators.Length(min=30)])
# Adding Article Route
@app.route('/add_article',methods=['POST','GET'])
@is_logged_in
def add_article():
	form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data
		article = mongo.db.Articles
		article.insert_one({'title':title,'body':body,'author':session['username'],'date':datetime.now()})
		flash('Article Created','success')
		return redirect(url_for('dashboard'))
	return render_template('add_article.html',form=form)

@app.route('/edit_article/<string:title>',methods=['POST','GET'])
@is_logged_in
def edit_article(title):
	article = mongo.db.Articles
	article_title = article.find_one({"title":title})
	updated_title = article_title['title']
	form = ArticleForm(request.form)
	form.title.data = article_title['title']
	form.body.data = article_title['body']
	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body = request.form['body']
		
		article.update_one({'title':updated_title},{'$set':{'title':title,'body':body,'date':datetime.now()}})
		flash('Article Updated','success')
		return redirect(url_for('dashboard'))
	return render_template('add_article.html',form=form)

@app.route('/delete_article/<string:title>',methods=['POST'])
@is_logged_in
def delete_article(title):
	deleting = mongo.db.Articles
	# title_delete = deleting['title']
	# Deleting a field
	deleting.delete_one({'title':title})
	flash('Article Deleted','success')
	return redirect(url_for('dashboard'))

if __name__ == '__main__':
	app.run(debug=True,port=8000)

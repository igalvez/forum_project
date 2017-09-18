from flask import Flask, render_template, request, redirect, url_for, session,flash
app = Flask(__name__)
app.secret_key = 'teste'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Sub, User, Post, Comment
import sqlalchemy.orm.exc
from wtforms import Form, validators, StringField, PasswordField, SubmitField

admins = ['gri']

engine = create_engine('sqlite:///reddit.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
dbsession = DBSession()


# FORMS ------------------------------------

class registrationForm(Form):
	username = StringField("Username",[validators.Required()])
	password = PasswordField("Password",[validators.Required(),validators.Length(min=8,max=30,message="Minimum password length is 8")])
	confirm = PasswordField("Confirm Password",[validators.Length(max=30),validators.EqualTo('password',message="Passwords should match")])
	email = StringField("Email",[validators.Email(message="Wrong email format")])
	submit = SubmitField("Register")

#---------------------------------------------------------

def get_comments(pid,cid):
	clist = dbsession.query(Comment).filter_by(post_id=pid).filter_by(parent_id=cid).all()
	return clist

def get_author(uid):
	if uid==0:
		return ''
	user = dbsession.query(User).filter_by(id=uid).first()
	print ' user obj %s'%str(user)
	print "id = " + str(uid)
	if not user:
		return ''
	return user.username 

#------------------------------------------------------------
@app.route('/')
def main():
	subs = dbsession.query(Sub).all()
	return render_template('index.html',subs=subs)
	

@app.route('/dashboard')
def dashboard():
	if 'uid' not in session:
		return 'Login required to access this feature'
	uid = session['uid']
	user = dbsession.query(User).filter_by(id=uid).one()
	return redirect(url_for('show_user',user_id=user.id))


@app.route('/signup', methods=['GET','POST'])
def new_user():
	if 'uid' in session:
		return redirect(url_for('main'))
	form = registrationForm(request.form)
	if request.method == 'POST' and form.validate():
		isuser = dbsession.query(User).filter_by(username=form.username.data).first()
		if isuser:
			flash("Username already exists")
			return render_template('signup.html',form=form)

		try:
			newUser = User(username=request.form['username'], password=request.form['password'], email=request.form['email'])		
			dbsession.add(newUser)
			dbsession.commit()
			session['uid'] = newUser.id
			session['username'] = newUser.username
			session['loggedin'] = True
			return redirect(url_for('main'))
		except:
			flash("Error: Could not register user")
			return render_template('signup.html',form=form)
	else:
		return render_template('signup.html',form=form)

@app.route('/login/', methods=['GET','POST'])
def login():
	if request.method == 'POST':
		try:
			user = dbsession.query(User).filter_by(username=request.form['username']).one()
		except sqlalchemy.orm.exc.NoResultFound:
			flash("Wrong username or password")
			#return render_template('login.html')
		else:
			if user.verify_password(request.form['password']):
				session['uid'] = user.id
				session['username'] = user.username
				session['loggedin'] = True
				return redirect(url_for('main'))
			else:
				flash("Wrong username or password")
	else:
		if 'loggedin' in session:
			return 'User already logged in'
	return render_template('login.html')

@app.route('/logout/')
def logout():
	#if 'username' in session:
	session.pop('uid',None)
	session.pop('loggedin',None)
	session.pop('username',None)
	return redirect(url_for('login'))



@app.route('/createsub/',methods=['GET','POST'])
def create_sub():
	if 'uid' not in session:
		return redirect(url_for('login'))

	if request.method == 'POST':
		newSub = Sub(name=request.form['subname'], descr=request.form['desc'],admin_id=int(session['uid']))
		dbsession.add(newSub)
		dbsession.commit()
		return redirect(url_for('show_sub',sid=newSub.id))
	return render_template('create_sub.html')



@app.route('/sub/<int:sid>')
def show_sub(sid):
	sub = dbsession.query(Sub).filter_by(id=sid).one()
	posts = dbsession.query(Post).filter_by(sub_id=sid)	
	return render_template('show_sub.html', posts=posts, sub=sub)

@app.route('/sub/<int:sid>/create_post',methods=['GET','POST'])
def create_post(sid):
	if 'uid' not in session:
		return redirect(url_for('login'))
	
	sub = dbsession.query(Sub).filter_by(id=sid).one()
	if request.method == 'POST':
		newPost = Post(title=request.form['title'], message=request.form['message'], sub_id=sid, user_id=int(session['uid']))
		dbsession.add(newPost)
		dbsession.commit()
		return redirect(url_for('show_post',sid=sub.id,pid=newPost.id))
	return render_template('create_post.html', sub=sub)	


@app.route('/sub/<int:sid>/post/<int:pid>',methods=['GET','POST'])
def show_post(sid,pid):
	if request.method == "POST":
		newComment = Comment(message=request.form['message'], user_id=session['uid'], post_id=pid, parent_id=int(request.form["cid"]))
		print " message is %s"%request.form["message"]
		dbsession.add(newComment)
		dbsession.commit()
		return newComment.id
	sub = dbsession.query(Sub).filter_by(id=sid).one()
	post = dbsession.query(Post).filter_by(id=pid).one()
	comments = dbsession.query(Comment).filter_by(post_id=post.id).filter_by(parent_id=0)
	print "comments objs %s"%str(comments)
	#print "comment author: %s"%post.user.username
	#print "user obj: %s"%str(post.user)
	#user = dbsession.query(User).filter_by(id=session['uid']).one()
	return render_template('show_post.html',sub=sub, post=post, comments=comments, get_comments=get_comments, get_author=get_author) #, username=user.username )


@app.route('/sub/<int:sid>/post/<int:pid>/<int:cid>/writecomment/',methods=['GET','POST'])
def write_comment(sid,pid,cid):
	if 'uid' not in session:
		return redirect(url_for('login'))

	if request.method == 'POST':
		newComment = Comment(message=request.form['message'], user_id=session['uid'], post_id=pid, parent_id=cid)
		dbsession.add(newComment)
		dbsession.commit()
		return redirect(url_for('show_post',sid=sid,pid=pid))
	
	if cid!=0:
		element = dbsession.query(Comment).filter_by(id=cid).one()
	else:
		element = dbsession.query(Post).filter_by(id=pid).one()
	return render_template('write_comment.html',element=element, sid=sid, pid=pid, cid=cid)

@app.route('/sub/<int:sid>/post/<int:pid>/<int:cid>/deletecomment/')
def delete_comment(sid,pid,cid):
	if 'uid' not in session: return redirect(url_for('show_post', sid=sid,pid=pid))

	comment= dbsession.query(Comment).filter_by(id=cid).one()
	sub = dbsession.query(Sub).filter_by(id=sid).first()

	if session['uid']==comment.user_id or session['uid']==sub.admin_id:
		comment.message = '[deleted]'
		comment.user_id = 0
		#dbsession.delete(comment)
		dbsession.commit()
	return redirect(url_for('show_post', sid=sid,pid=pid))	


@app.route('/sub/<int:sid>/post/<int:pid>/<int:cid>/postcomment/',methods=['GET','POST'])
def post_comment(sid,pid,cid):
	print "IN POST COMMENT"
	if 'uid' not in session:
		return redirect(url_for('login'))

	print "ok"
	if request.method == 'POST':
		newComment = Comment(message=request.form['message'], user_id=session['uid'], post_id=pid, parent_id=cid)
		print " message is %s"%request.form["message"]
		dbsession.add(newComment)
		dbsession.commit()
		return newComment.id
	print "this is A GET request"
	return redirect(url_for("show_posts"))

@app.errorhandler(404)
def page_not_found(err):
	return "oh noo! This is not the page you are looking for! " + str(err)









@app.route('/admin/allusers')
def show_users():
	users = dbsession.query(User).all()
	return render_template('show_users.html',users=users)

@app.route('/admin/user/delete/<int:user_id>/')
def delete_user(user_id):
	user = dbsession.query(User).filter_by(id=user_id).one()
	user.username = ''
	user.email = ''
	user.password = ''
	#dbsession.delete(user)
	dbsession.commit()
	return redirect(url_for('show_users'))

@app.route('/admin/user/edit/<int:user_id>/', methods=['GET','POST'])
def edit_user(user_id,msg=''):
	user = dbsession.query(User).filter_by(id=user_id).one()
	return render_template('edit_user.html',user=user)

@app.route('/admin/user/update_email/<int:user_id>/', methods=['POST'])
def update_email(user_id):
	user = dbsession.query(User).filter_by(id=user_id).one()
	if not user.verify_password(request.form['password']):
		return redirect(url_for('edit_user',user_id=user.id,msg='Wrong password'))
	user.email = request.form['email']
	dbsession.add(user)
	dbsession.commit()
	return "<html><body>Email updated <br/><br/> <a href=%s>back</a></body></html>"%url_for('edit_user',user_id=user.id)

@app.route('/admin/user/update_pass/<int:user_id>/', methods=['POST'])
def update_password(user_id):
	user = dbsession.query(User).filter_by(id=user_id).one()
	if request.form['newpass']!=request.form['newpass2']:
		return redirect(url_for('edit_user',user_id=user.id,msg="Passwords don't match"))
	if not user.update_password(request.form['password'],request.form['newpass']):
		return redirect(url_for('edit_user',user_id=user.id,msg='Wrong password'))	 
	dbsession.add(user)
	dbsession.commit()
	return "<html><body>Password updated <br/><br/> <a href=%s>back</a></body></html>"%url_for('edit_user',user_id=user.id)

@app.route('/admin/user/show/<int:user_id>/', methods=['GET','POST'])
def show_user(user_id):
	user = dbsession.query(User).filter_by(id=user_id).one()
	if request.method == 'POST':
		return redirect(url_for('show_users'))
	else:
		return render_template('user_details.html',user=user)
if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=8080)

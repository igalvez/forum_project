import sys
from sqlalchemy import String, Integer, Text, Time, ForeignKey, Column, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

import md5

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'
	id = Column(Integer, primary_key=True)
	username = Column(String(20), nullable=False)
	password = Column(String(20), nullable=False)
	email = Column(String(50))

	def __init__(self,username,password,email):
		self.username = username
		self.email = email
		self.password = md5.new(password).hexdigest()

	def verify_password(self,password):
		return md5.new(password).hexdigest()==self.password

	def update_password(self,old_password,new_password):
		if self.verify_password(old_password):
			self.password = md5.new(new_password).hexdigest()
			return True
		return False


class Sub(Base):
	__tablename__ = 'sub'
	id = Column(Integer, primary_key=True)
	name = Column(String(80),nullable=False)
	descr = Column(Text)
	wiki = Column(Text)
	admin_id = Column(Integer, ForeignKey('user.id'))
	admin = relationship(User)

class Post(Base):
	__tablename__ = 'post'
	title = Column(String(80),nullable=False)
	id = Column(Integer, primary_key=True)
	message = Column(Text)
	date = Column(Time)
	upvotes = Column(Integer,default=0)
	user_id = Column(Integer,ForeignKey('user.id'))
	sub_id = Column(Integer,ForeignKey('sub.id'))
	user = relationship(User,uselist=True)
	sub = relationship(Sub)


class Comment(Base):
	__tablename__ = 'comment'
	id = Column(Integer, primary_key=True)
	message = Column(Text)
	date = Column(Time)
	upvotes = Column(Integer, default=0)
	user_id = Column(Integer,ForeignKey('user.id'))
	post_id = Column(Integer,ForeignKey('post.id'))
	parent_id = Column(Integer,ForeignKey('comment.id'))
	user = relationship(User)
	post = relationship(Post)


engine = create_engine('sqlite:///reddit.db')

Base.metadata.create_all(engine)
	

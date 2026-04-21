from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Manager(UserMixin, db.Model):
    __tablename__ = 'managers'
    id = db.Column(db.Integer, primary_key=True) 
    manager_name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False) # NEW COLUMN
    users = db.relationship('User', backref='manager', lazy=True)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False) # NEW COLUMN
    manager_id = db.Column(db.Integer, db.ForeignKey('managers.id'), nullable=False)
    applications = db.relationship('Application', backref='user', lazy=True)

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(200), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
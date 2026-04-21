from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Initialize the database tool
db = SQLAlchemy()

class Manager(UserMixin, db.Model):
    __tablename__ = 'managers'
    id = db.Column(db.Integer, primary_key=True) 
    manager_name = db.Column(db.String(100), nullable=False)
    
    # Relationship: A manager has many users
    users = db.relationship('User', backref='manager', lazy=True)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    
    # Foreign Key: Link to the specific manager
    manager_id = db.Column(db.Integer, db.ForeignKey('managers.id'), nullable=False)
    
    # Relationship: A user has many travel applications
    applications = db.relationship('Application', backref='user', lazy=True)

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(200), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, or Rejected
    
    # Foreign Key: Link to the user who submitted it
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
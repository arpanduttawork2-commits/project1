from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class TravelAdmin(UserMixin, db.Model):
    __tablename__ = 'travel_admins'
    id = db.Column(db.String(50), primary_key=True)  # <-- Changed to String
    admin_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Manager(UserMixin, db.Model):
    __tablename__ = 'managers'
    id = db.Column(db.String(50), primary_key=True)  # <-- Changed to String
    manager_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    users = db.relationship('User', backref='manager', lazy=True)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(50), primary_key=True)  # <-- Changed to String
    user_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    base_location = db.Column(db.String(100), nullable=False) 
    manager_id = db.Column(db.String(50), db.ForeignKey('managers.id'), nullable=False) # <-- Changed to String
    applications = db.relationship('Application', backref='user', lazy=True)

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True) # Keep this integer (Auto-generates 1, 2, 3...)
    destination = db.Column(db.String(100), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    manager_status = db.Column(db.String(20), default='Pending')
    admin_status = db.Column(db.String(20), default='Pending')
    
    ticket_to_blob = db.Column(db.LargeBinary, nullable=True)
    ticket_from_blob = db.Column(db.LargeBinary, nullable=True)
    
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False) # <-- Changed to String
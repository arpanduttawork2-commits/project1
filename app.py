import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Manager, Application

app = Flask(__name__)

# --- Configuration ---
database_url = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
if database_url.startswith("mysql://"):
    database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
    if "?" in database_url:
        database_url = database_url.split("?")[0]

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-key-123' 

if "mysql" in database_url:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'ssl': {}}}

db.init_app(app)

# --- Login Manager Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    # This checks both tables for the user ID
    user = User.query.get(int(user_id))
    if user:
        return user
    return Manager.query.get(int(user_id))

with app.app_context():
    db.create_all()

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if role == 'manager':
            user = Manager.query.filter_by(manager_name=username, password=password).first()
        else:
            user = User.query.filter_by(user_name=username, password=password).first()
            
        if user:
            login_user(user)
            return redirect(url_for('manager_home' if role == 'manager' else 'user_home'))
        
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- User Routes ---

@app.route('/user/home')
@login_required
def user_home():
    return render_template('user_home.html')

@app.route('/user/apply', methods=['GET', 'POST'])
@login_required
def user_apply():
    if request.method == 'POST':
        destination = request.form.get('destination')
        reason = request.form.get('reason')
        new_app = Application(destination=destination, reason=reason, user_id=current_user.id)
        db.session.add(new_app)
        db.session.commit()
        flash('Application submitted!', 'success')
        return redirect(url_for('user_home'))
    return render_template('user_apply.html')

@app.route('/user/view')
@login_required
def user_view():
    apps = Application.query.filter_by(user_id=current_user.id).all()
    return render_template('user_view.html', apps=apps)

# --- Manager Routes ---

@app.route('/manager/home')
@login_required
def manager_home():
    return render_template('manager_home.html')

@app.route('/manager/review')
@login_required
def manager_review():
    # Manager sees applications from all users assigned to them
    apps = Application.query.join(User).filter(User.manager_id == current_user.id, Application.status == 'Pending').all()
    return render_template('manager_review.html', apps=apps)

@app.route('/manager/update/<int:app_id>', methods=['POST'])
@login_required
def update_status(app_id):
    decision = request.form.get('decision')
    app_to_update = Application.query.get(app_id)
    if app_to_update:
        app_to_update.status = decision
        db.session.commit()
    return redirect(url_for('manager_review'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
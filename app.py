import os
from flask import Flask, render_template, request, redirect, url_for
from models import db, User, Manager, Application

app = Flask(__name__)

# --- Configuration ---
# 1. Get the URL from the environment (Render or Codespaces)
# If it's not found, it defaults to a local sqlite file so the app doesn't crash
database_url = os.environ.get('DATABASE_URL', 'sqlite:///local.db')

# 2. Fix the Aiven URL (Aiven gives 'mysql://', but SQLAlchemy needs 'mysql+pymysql://')
if database_url.startswith("mysql://"):
    database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
    if "?" in database_url:
        database_url = database_url.split("?")[0]

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-key-123' # You can change this to a secure string later

# Initialize the database with the app
db.init_app(app)

# Create the tables in Aiven automatically
with app.app_context():
    db.create_all()

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Temporary logic: Route based on the dropdown selection
        role = request.form.get('role')
        if role == 'manager':
            return redirect(url_for('manager_home'))
        return redirect(url_for('user_home'))
    return render_template('login.html')

@app.route('/user/home')
def user_home():
    return render_template('user_home.html')

@app.route('/user/apply')
def user_apply():
    return render_template('user_apply.html')

@app.route('/user/view')
def user_view():
    return render_template('user_view.html')

@app.route('/manager/home')
def manager_home():
    return render_template('manager_home.html')

@app.route('/manager/review')
def manager_review():
    return render_template('manager_review.html')

if __name__ == "__main__":
    # Render provides a PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
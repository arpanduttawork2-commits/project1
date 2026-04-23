import os
from app import app, db
from models import User, Manager, TravelAdmin, Application

# Standard Aiven URL Fix
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("mysql://"):
    database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
    if "?" in database_url:
        database_url = database_url.split("?")[0]

with app.app_context():
    print("\n--- 🛠️ TRAVEL ADMINS ---")
    admins = TravelAdmin.query.all()
    for a in admins:
        print(f"ID: {a.id} | Name: {a.admin_name} | Email: {a.email} | Pass: {a.password}")

    print("\n--- 👔 MANAGERS ---")
    managers = Manager.query.all()
    for m in managers:
        print(f"ID: {m.id} | Name: {m.manager_name} | Email: {m.email} | Pass: {m.password}")

    print("\n--- 👥 USERS ---")
    users = User.query.all()
    for u in users:
        print(f"ID: {u.id} | Name: {u.user_name} | Email: {u.email} | Pass: {u.password} | Manager ID: {u.manager_id}")

    print("\n--- 📝 APPLICATIONS ---")
    apps = Application.query.all()
    if not apps:
        print("No applications found yet. (This is normal right now!)")
    for a in apps:
        print(f"App ID: {a.id} | User ID: {a.user_id} | Dest: {a.destination} | Mgr Status: {a.manager_status} | Admin Status: {a.admin_status}")
    
    print("\n--- EXTRACTION COMPLETE ---\n")
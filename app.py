import os
from datetime import datetime
import io
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask import send_file
from models import db, User, Manager, TravelAdmin, Application

app = Flask(__name__)
app.secret_key = "super_secret_session_key"

# --- Database Setup ---
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("mysql://"):
    database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
    if "?" in database_url:
        database_url = database_url.split("?")[0]

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- FLASK-MAIL SETUP (Gmail Configuration) ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') # systemadmin114@gmail.com
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD') # Your 16-char App Password
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')

mail = Mail(app)

# --- Login Manager Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(user_id)
    if user: return user
    admin = TravelAdmin.query.get(user_id)
    if admin: return admin
    manager = Manager.query.get(user_id)
    if manager: return manager
    return None

# --- AUTHENTICATION ROUTES ---

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if isinstance(current_user, User): return redirect(url_for('user_home'))
        if isinstance(current_user, TravelAdmin): return redirect(url_for('admin_home'))

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')

        user = User.query.get(user_id)
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('user_home'))

        admin = TravelAdmin.query.get(user_id)
        if admin and admin.password == password:
            login_user(admin)
            return redirect(url_for('admin_home'))

        manager = Manager.query.get(user_id)
        if manager and manager.password == password:
            login_user(manager)
            flash("Managers approve via email links, but welcome!", "info")
            return redirect(url_for('login')) 

        flash('Invalid Login ID or Password. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# --- USER PORTAL ROUTES ---

@app.route('/user/home')
@login_required
def user_home():
    if not isinstance(current_user, User): return redirect(url_for('login'))
    return render_template('user/user_home.html')

@app.route('/download/<int:app_id>/<direction>')
@login_required
def download_ticket(app_id, direction):
    # Security: Ensure it is a User downloading
    if not isinstance(current_user, User):
        return redirect(url_for('login'))

    app_record = Application.query.get_or_404(app_id)

    # Security: Ensure users can only download their OWN tickets
    if app_record.user_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('user_view'))

    # Serve the correct ticket based on which button they clicked
    if direction == 'to' and app_record.ticket_to_blob:
        return send_file(
            io.BytesIO(app_record.ticket_to_blob), 
            download_name=f"Ticket_To_{app_record.destination}.pdf", 
            as_attachment=True
        )
    elif direction == 'return' and app_record.ticket_from_blob:
        return send_file(
            io.BytesIO(app_record.ticket_from_blob), 
            download_name=f"Ticket_Return_From_{app_record.destination}.pdf", 
            as_attachment=True
        )
    
    flash("Ticket not found in the database.", "warning")
    return redirect(url_for('user_view'))

@app.route('/user/apply', methods=['GET', 'POST'])
@login_required
def user_apply():
    if not isinstance(current_user, User): return redirect(url_for('login'))

    if request.method == 'POST':
        destination = request.form.get('destination')
        reason = request.form.get('reason')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()

        # 1. Save to Database
        new_app = Application(
            destination=destination,
            reason=reason,
            start_date=start_date,
            end_date=end_date,
            user_id=current_user.id
        )
        db.session.add(new_app)
        db.session.commit()

        # 2. FIRE THE EMAIL TO THE MANAGER
        try:
            manager = Manager.query.get(current_user.manager_id)
            decision_link = url_for('manager_decision', app_id=new_app.id, _external=True)

            msg = Message(f"ACTION REQUIRED: Travel Request from {current_user.user_name}",
                          recipients=[manager.email])
            
            msg.body = f"""
Hello {manager.manager_name},

{current_user.user_name} has submitted a new travel request.

Details:
- Destination: {destination}
- Dates: {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}
- Reason: {reason}

Please review this request and make a decision by clicking the secure link below:
{decision_link}

Thank you,
Enterprise Travel System
"""
            mail.send(msg)
            flash("Travel request submitted successfully! Your manager has been emailed.", "success")
            
        except Exception as e:
            print(f"Email Error: {str(e)}")
            flash("Request saved, but the system failed to email your manager. Please notify them manually.", "warning")

        return redirect(url_for('user_view'))

    return render_template('user/user_apply.html')

@app.route('/user/view')
@login_required
def user_view():
    if not isinstance(current_user, User): return redirect(url_for('login'))
    my_apps = Application.query.filter_by(user_id=current_user.id).order_by(Application.start_date.desc()).all()
    return render_template('user/user_view.html', applications=my_apps)


# --- MANAGER ACTION ROUTE ---

@app.route('/manager/decision/<int:app_id>', methods=['GET', 'POST'])
def manager_decision(app_id):
    application = Application.query.get_or_404(app_id)
    
    if request.method == 'POST':
        action = request.form.get('action') 

        if action == 'approve':
            application.manager_status = 'Approved'
            db.session.commit()

            # FIRE EMAIL TO TRAVEL ADMIN
            try:
                admin = TravelAdmin.query.first() 
                msg = Message(f"TICKETS REQUIRED: Approved Travel for {application.user.user_name}",
                              recipients=[admin.email])
                
                msg.body = f"""
Hello Admin Team,

Manager {application.user.manager.manager_name} has APPROVED travel for {application.user.user_name}.

Destination: {application.destination}
Dates: {application.start_date.strftime('%b %d, %Y')} to {application.end_date.strftime('%b %d, %Y')}

Please log into the Travel Admin Portal to upload the tickets.
"""
                mail.send(msg)
            except Exception as e:
                print(f"Failed to email Admin: {str(e)}")

            return "<div style='font-family: sans-serif; text-align: center; margin-top: 50px;'><h2>✅ Travel Approved!</h2><p>The Admin team has been notified. You can close this tab.</p></div>"

        elif action == 'reject':
            application.manager_status = 'Rejected'
            application.admin_status = 'Rejected'
            db.session.commit()
            return "<div style='font-family: sans-serif; text-align: center; margin-top: 50px; color: red;'><h2>❌ Travel Rejected.</h2><p>The user can see this in their portal. You can close this tab.</p></div>"
            
    return render_template('manager/decision.html', app=application)


# --- ADMIN PORTAL ROUTES ---

@app.route('/admin/dashboard')
@login_required
def admin_home():
    if not isinstance(current_user, TravelAdmin):
        flash("Access Denied. Travel Admins only.", "danger")
        return redirect(url_for('login'))
    
    pending_tickets = Application.query.filter_by(
        manager_status='Approved', 
        admin_status='Pending'
    ).order_by(Application.start_date.asc()).all()

    return render_template('admin/admin_home.html', applications=pending_tickets)

@app.route('/admin/upload/<int:app_id>', methods=['GET', 'POST'])
@login_required
def upload_tickets(app_id):
    if not isinstance(current_user, TravelAdmin):
        return redirect(url_for('login'))

    application = Application.query.get_or_404(app_id)

    if request.method == 'POST':
        ticket_to_file = request.files.get('ticket_to')
        ticket_from_file = request.files.get('ticket_from')

        if ticket_to_file and ticket_from_file:
            # Save to Database
            application.ticket_to_blob = ticket_to_file.read()
            application.ticket_from_blob = ticket_from_file.read()
            
            application.admin_status = 'Approved'
            db.session.commit()

            # FIRE FINAL EMAIL TO THE USER (WITH ATTACHMENTS!)
            try:
                msg = Message(f"TICKETS CONFIRMED: Your Trip to {application.destination}",
                              recipients=[application.user.email])
                
                msg.body = f"""
Hello {application.user.user_name},

Great news! The Travel Admin team has booked your tickets to {application.destination}.
Your travel dates are {application.start_date.strftime('%b %d, %Y')} to {application.end_date.strftime('%b %d, %Y')}.

Your tickets are attached to this email. You can also log into the Employee Travel Portal at any time to view them.

Safe travels!
"""
                # Attach the actual files directly to the email!
                msg.attach(
                    filename=f"To_{application.destination}_{ticket_to_file.filename}",
                    content_type=ticket_to_file.content_type,
                    data=application.ticket_to_blob
                )
                msg.attach(
                    filename=f"Return_{application.user.base_location}_{ticket_from_file.filename}",
                    content_type=ticket_from_file.content_type,
                    data=application.ticket_from_blob
                )

                mail.send(msg)
                flash("Tickets uploaded and emailed to the user successfully!", "success")
            except Exception as e:
                print(f"Email Error: {str(e)}")
                flash("Tickets saved, but we failed to email the user.", "warning")

            return redirect(url_for('admin_home'))

    return render_template('admin/upload_tickets.html', app=application)


if __name__ == '__main__':
    app.run(debug=True)
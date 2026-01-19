from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message as MailMessage
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from dotenv import load_dotenv

# Load the variables from .env
load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# --- APP CONFIGURATION ---
app.secret_key = os.getenv('SECRET_KEY')

# Handle Database Path
basedir = os.path.abspath(os.path.dirname(__file__))
# Fallback to local sqlite if DATABASE_URL isn't found
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'studio.db'))

# uri = os.environ.get("DATABASE_URL") 

# if uri:
#     # Fix the 'postgres://' vs 'postgresql://' issue
#     if uri.startswith("postgres://"):
#         uri = uri.replace("postgres://", "postgresql://", 1)
#     # Ensure there are no hidden spaces or quotes
#     app.config['SQLALCHEMY_DATABASE_URI'] = uri.strip().replace("'", "").replace('"', "")
# else:
#     # Fallback for local development
#     basedir = os.path.abspath(os.path.dirname(__file__))
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'studio.db')

# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- EMAIL SETTINGS ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

db = SQLAlchemy(app)
mail = Mail(app)

@app.context_processor
def inject_now():
    # This makes 'now' (the current date/time) available in all HTML files
    return {'now': datetime.utcnow()}

# Ensure the folder exists on your computer
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- DATABASE MODELS ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    tag = db.Column(db.String(50))
    desc = db.Column(db.Text)
    span = db.Column(db.String(50), default="col-span-1")
    live_link = db.Column(db.String(255), nullable=True) 
    repo_link = db.Column(db.String(255), nullable=True) 

class Social(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50)) 
    url = db.Column(db.String(255))

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    subject = db.Column(db.String(200))
    body = db.Column(db.Text)

# --- UPDATED ABOUT MODEL ---
class About(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), default="Samuel Peprah. (Atom-De-Legend)")
    logo_url = db.Column(db.String(255))
    profile_img = db.Column(db.String(255))
    bio_content = db.Column(db.Text)
    stack_list = db.Column(db.String(500)) # Comma separated
    completed = db.Column(db.Integer, default=0)
    progress = db.Column(db.Integer, default=0)
    hosted = db.Column(db.Integer, default=0)

# with app.app_context():
#     db.create_all()
#     # Check for Admin User
#     existing_user = User.query.filter_by(username='Atom-Dev-Studios').first()
#     if not existing_user:
#         admin_user = User(username='Atom-Dev-Studios', password='samuelkofipeprah1')
#         db.session.add(admin_user)
#         db.session.commit()
#         print(">>> SECURITY: Production Admin user created.")

# --- INITIALIZE LOGIN MANAGER ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirects here if not logged in

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_founder():
    # This makes 'f' available in every template without passing it manually
    return dict(f=About.query.first())

# --- LOGIN/LOGOUT ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('admin'))
        flash("ACCESS_DENIED: Invalid Credentials", "error")
        
    # Pass 'f' into the template here
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- ROUTES ---
@app.route('/')
def home():
    projects = Project.query.all()
    socials = Social.query.all()
    founder = About.query.first()
    return render_template('index.html', projects=projects, socials=socials, f=founder)


# --- CONTACT ROUTE ---
@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message_body = request.form.get('message')

    # 1. Save to Database
    new_msg = ContactMessage(name=name, email=email, subject=subject, body=message_body)
    db.session.add(new_msg)
    db.session.commit()

    # 2. Send Email Alert
    try:
        msg = MailMessage(subject=f"STUDIO INQUIRY: {subject}",
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[app.config['MAIL_USERNAME']], # Send to yourself
                          body=f"From: {name} ({email})\n\nMessage:\n{message_body}")
        mail.send(msg)
        flash("COMMUNICATION_ESTABLISHED: Message sent successfully.", "success")
    except Exception as e:
       flash("SYSTEM_ERROR: Message saved but email failed to transmit.", "error")

    return redirect(url_for('home'))

# @app.route('/admin', methods=['GET', 'POST'])
# def admin():
#     if request.method == 'POST':
#         if 'update_about' in request.form:
#             f = About.query.first() or About()
#             f.stack_list = request.form['stack_list']
#             f.projects_completed = int(request.form['completed'])
#             f.projects_in_progress = int(request.form['progress'])
#             f.projects_hosted = int(request.form['hosted'])
#             db.session.add(f)
#             db.session.commit()
#         new_p = Project(
#             title=request.form['title'],
#             tag=request.form['tag'],
#             desc=request.form['desc'],
#             span=request.form['span'],
#             live_link=request.form.get('live_link'),
#             repo_link=request.form.get('repo_link')
#         )
#         db.session.add(new_p)
#         db.session.commit()
#         return redirect(url_for('admin'))
    
#     projects = Project.query.all()
#     return render_template('admin.html', projects=projects)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        # 1. Handle About/System Calibration
        if 'update_about' in request.form:
            f = About.query.first() or About()
            
            if 'profile_file' in request.files:
                file = request.files['profile_file']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    f.profile_img = f"/static/uploads/{filename}"

            if 'logo_file' in request.files:
                file = request.files['logo_file']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    f.logo_url = f"/static/uploads/{filename}"

            f.stack_list = request.form.get('stack_list')
            f.completed = int(request.form.get('completed') or 0)
            f.progress = int(request.form.get('progress') or 0)
            f.hosted = int(request.form.get('hosted') or 0)
            f.bio_content = request.form.get('bio_content')
            
            db.session.add(f)
            flash("SYSTEM_SYNC: Calibration data secured.", "success")

        # 2. Handle New Project (THIS WAS MISSING)
        elif 'title' in request.form:
            new_p = Project(
                title=request.form['title'],
                tag=request.form['tag'],
                desc=request.form['desc'],
                span=request.form['span'],
                live_link=request.form.get('live_link'),
                repo_link=request.form.get('repo_link')
            )
            db.session.add(new_p)
            flash("PROJECT_DEPLOYED: Archive entry created.", "success")

        # 3. Handle New Social Link
        elif 'platform' in request.form:
            new_s = Social(
                platform=request.form['platform'], 
                url=request.form['url']
            )
            db.session.add(new_s)
            flash("LINK_ESTABLISHED: Social channel secured.", "success")
            
        # Final Commit for all POST actions
        db.session.commit()
        return redirect(url_for('admin'))
    
    # GET Request logic
    return render_template('admin.html', 
                           projects=Project.query.all(), 
                           socials=Social.query.all(), 
                           f=About.query.first(),
                           messages=ContactMessage.query.all())
@app.route('/project/delete/<int:id>')
def delete_project(id):
    p = Project.query.get(id)
    if p:
        db.session.delete(p)
        db.session.commit()
    return redirect(url_for('admin'))

# @app.route('/project/<int:id>')
# def project_detail(id):
#     project = Project.query.get_or_404(id)
#     return render_template('project.html', p=project)

@app.route('/project/<int:id>')
def project_detail(id):
    project = Project.query.get_or_404(id)
    return render_template('project.html', p=project)

# Logic to calculate total projects for the bars
@app.context_processor
def utility_processor():
    def get_total_projects(f):
        return f.projects_completed + f.projects_in_progress
    return dict(get_total_projects=get_total_projects)

# --- ADD THIS ROUTE ---
@app.route('/about')
def about_page():
    founder = About.query.first()
    socials = Social.query.all()

    if not founder:
        founder = About(full_name="Atom De Legend", completed=0, progress=0, hosted=0)

    return render_template('about.html', f=founder, socials=socials)

@app.route('/social/delete/<int:id>')
def delete_social(id):
    s = Social.query.get(id)
    if s:
        db.session.delete(s)
        db.session.commit()
        flash("LINK_TERMINATED: Social connection severed.", "success")
    return redirect(url_for('admin'))

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('.', 'sw.js')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # FIX: Explicitly check if the username exists before trying to add it
        existing_user = User.query.filter_by(username='Atom-Dev-Studios').first()
        
        if not existing_user:
            admin_user = User(username='Atom-Dev-Studios', password='samuelkofipeprah1')
            db.session.add(admin_user)
            db.session.commit()
            print(">>> SECURITY: Admin user created.")
        else:
            print(">>> SECURITY: Admin user already exists. Skipping creation.")
    # app.run(host='0.0.0.0', port=7860)
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from functools import wraps
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv
from io import StringIO

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'vaanyan-home-tuition-secret-key-2025')

# Database Configuration - PostgreSQL for production, SQLite for local
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # PostgreSQL for Railway production
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # SQLite for local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vaanyan_tuition.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session Configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'mahapatravinayak@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'wrdb okdi macb zxim')
app.config['ADMIN_EMAIL'] = os.environ.get('ADMIN_EMAIL', 'mahapatravinayak@gmail.com')

# Initialize database
db = SQLAlchemy(app)

# ===== DATABASE MODELS =====

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, lazy=True)
    teacher_profile = db.relationship('TeacherProfile', backref='user', uselist=False, lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    grade = db.Column(db.String(20), nullable=False)
    board = db.Column(db.String(50), nullable=False)
    subjects = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)


class TeacherProfile(db.Model):
    __tablename__ = 'teacher_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    qualification = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.String(50), nullable=False)
    subjects = db.Column(db.Text, nullable=False)
    teaching_mode = db.Column(db.Text, nullable=False)
    hourly_rate = db.Column(db.Integer, nullable=False)
    bio = db.Column(db.Text)
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, default=5.0)
    total_students = db.Column(db.Integer, default=0)
    total_classes = db.Column(db.Integer, default=0)
    total_earnings = db.Column(db.Integer, default=0)
    is_verified = db.Column(db.Boolean, default=False)


class TutorRequest(db.Model):
    __tablename__ = 'tutor_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('User', foreign_keys=[student_id], backref='sent_requests')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='received_requests')


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')


class Class(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('tutor_requests.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    scheduled_at = db.Column(db.String(100), nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    status = db.Column(db.String(20), default='scheduled')
    meeting_link = db.Column(db.String(500))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ClassSession(db.Model):
    __tablename__ = 'class_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('tutor_requests.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    duration_hours = db.Column(db.Float, default=1.0)
    hourly_rate = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='completed')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('User', foreign_keys=[student_id], backref='student_sessions')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='teacher_sessions')


class PaymentCycle(db.Model):
    __tablename__ = 'payment_cycles'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    total_classes = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Integer, default=0)
    commission = db.Column(db.Integer, default=0)
    teacher_earning = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')
    payment_screenshot = db.Column(db.String(500))
    payment_verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('User', foreign_keys=[student_id], backref='student_payments')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='teacher_payments')


# ===== HELPER FUNCTIONS =====

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


def send_admin_notification(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = app.config['ADMIN_EMAIL']
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent: {subject}")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False


# ===== MAIN ROUTES =====

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/choose-role')
def choose_role():
    return render_template('choose_role.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('No account found with this email address', 'error')
            return redirect(url_for('login'))
        
        if not user.check_password(password):
            flash('Incorrect password. Please try again', 'error')
            return redirect(url_for('login'))
        
        if not user.is_active:
            flash('Your account has been deactivated', 'error')
            return redirect(url_for('login'))
        
        session['user_id'] = user.id
        session['user_role'] = user.role
        session.permanent = True
        
        flash(f'Welcome back, {user.first_name}!', 'success')
        
        if user.role == 'student':
            return redirect(url_for('student_dashboard'))
        elif user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('teacher_dashboard'))
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('home'))


# ===== STUDENT REGISTRATION =====

@app.route('/student/register', methods=['GET', 'POST'])
def student_registration():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        grade = request.form.get('grade')
        board = request.form.get('board')
        city = request.form.get('city')
        address = request.form.get('address')
        subjects = request.form.getlist('subjects')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('student_registration'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('student_registration'))
        
        user = User(
            role='student',
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()
        
        student_profile = StudentProfile(
            user_id=user.id,
            grade=grade,
            board=board,
            subjects=','.join(subjects),
            city=city,
            address=address
        )
        
        db.session.add(student_profile)
        db.session.commit()
        
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #6366f1;">🎓 New Student Registration!</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr><td style="padding: 8px; font-weight: bold;">Name:</td><td style="padding: 8px;">{first_name} {last_name}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Email:</td><td style="padding: 8px;">{email}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Phone:</td><td style="padding: 8px;">{phone}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Grade:</td><td style="padding: 8px;">{grade}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Board:</td><td style="padding: 8px;">{board}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">City:</td><td style="padding: 8px;">{city}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Subjects:</td><td style="padding: 8px;">{', '.join(subjects)}</td></tr>
            </table>
        </body>
        </html>
        """
        send_admin_notification(f"New Student: {first_name} {last_name}", email_body)
        
        flash('Registration successful! Please login', 'success')
        return redirect(url_for('login'))
    
    return render_template('student_registration.html')


# ===== TEACHER REGISTRATION =====

@app.route('/teacher/register', methods=['GET', 'POST'])
def teacher_registration():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        qualification = request.form.get('qualification')
        experience = request.form.get('experience')
        city = request.form.get('city')
        address = request.form.get('address')
        subjects = request.form.getlist('subjects')
        teaching_mode = request.form.getlist('teaching_mode')
        hourly_rate = request.form.get('hourly_rate')
        bio = request.form.get('bio', '')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('teacher_registration'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('teacher_registration'))
        
        user = User(
            role='teacher',
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()
        
        teacher_profile = TeacherProfile(
            user_id=user.id,
            qualification=qualification,
            experience=experience,
            subjects=','.join(subjects),
            teaching_mode=','.join(teaching_mode),
            hourly_rate=int(hourly_rate),
            bio=bio,
            city=city,
            address=address
        )
        
        db.session.add(teacher_profile)
        db.session.commit()
        
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #6366f1;">👨‍🏫 New Teacher Registration!</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr><td style="padding: 8px; font-weight: bold;">Name:</td><td style="padding: 8px;">{first_name} {last_name}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Email:</td><td style="padding: 8px;">{email}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Phone:</td><td style="padding: 8px;">{phone}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Qualification:</td><td style="padding: 8px;">{qualification}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Experience:</td><td style="padding: 8px;">{experience}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">City:</td><td style="padding: 8px;">{city}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Subjects:</td><td style="padding: 8px;">{', '.join(subjects)}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Teaching Mode:</td><td style="padding: 8px;">{', '.join(teaching_mode)}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Hourly Rate:</td><td style="padding: 8px;">₹{hourly_rate}</td></tr>
            </table>
        </body>
        </html>
        """
        send_admin_notification(f"New Teacher: {first_name} {last_name}", email_body)
        
        flash('Registration successful! Please login', 'success')
        return redirect(url_for('login'))
    
    return render_template('teacher_registration.html')


# ===== STUDENT DASHBOARD =====

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    user = get_current_user()
    
    if user.role != 'student':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    if user.student_profile:
        tutors = User.query.join(TeacherProfile).filter(
            User.role == 'teacher',
            TeacherProfile.city == user.student_profile.city
        ).limit(6).all()
    else:
        tutors = []
    
    classes = []
    
    unread_messages = Message.query.filter_by(
        recipient_id=user.id,
        is_read=False
    ).count()
    
    # Admin messages
    admin_users = User.query.filter_by(role='admin').all()
    admin_ids = [admin.id for admin in admin_users]
    
    admin_messages = Message.query.filter(
        Message.recipient_id == user.id,
        Message.sender_id.in_(admin_ids)
    ).order_by(Message.created_at.desc()).limit(10).all()
    
    return render_template('student_dashboard.html', 
                         current_user=user,
                         tutors=tutors,
                         classes=classes,
                         messages=range(unread_messages),
                         admin_messages=admin_messages)


# ===== TEACHER DASHBOARD =====

@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    user = get_current_user()
    
    if user.role != 'teacher':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    pending_requests = TutorRequest.query.filter_by(
        teacher_id=user.id,
        status='pending'
    ).all()
    
    accepted_request_ids = [req.id for req in TutorRequest.query.filter_by(
        teacher_id=user.id,
        status='accepted'
    ).all()]
    
    students = []
    if accepted_request_ids:
        student_ids = [req.student_id for req in TutorRequest.query.filter(
            TutorRequest.id.in_(accepted_request_ids)
        ).all()]
        students = User.query.filter(User.id.in_(student_ids)).all()
    
    classes = []
    monthly_earnings = user.teacher_profile.total_earnings if user.teacher_profile else 0
    
    unread_messages = Message.query.filter_by(
        recipient_id=user.id,
        is_read=False
    ).count()
    
    # Admin messages
    admin_users = User.query.filter_by(role='admin').all()
    admin_ids = [admin.id for admin in admin_users]
    
    admin_messages = Message.query.filter(
        Message.recipient_id == user.id,
        Message.sender_id.in_(admin_ids)
    ).order_by(Message.created_at.desc()).limit(10).all()
    
    return render_template('teacher_dashboard.html',
                         current_user=user,
                         pending_requests=pending_requests,
                         students=students,
                         classes=classes,
                         monthly_earnings=monthly_earnings,
                         messages=range(unread_messages),
                         admin_messages=admin_messages)


# ===== PROFILE EDIT ROUTES =====

@app.route('/student/edit-profile', methods=['GET', 'POST'])
@login_required
def student_edit_profile():
    user = get_current_user()
    
    if user.role != 'student':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        
        if user.student_profile:
            user.student_profile.grade = request.form.get('grade')
            user.student_profile.board = request.form.get('board')
            user.student_profile.subjects = ','.join(request.form.getlist('subjects'))
            user.student_profile.city = request.form.get('city')
            user.student_profile.address = request.form.get('address')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student_dashboard'))
    
    return render_template('student_edit_profile.html', current_user=user)


@app.route('/teacher/edit-profile', methods=['GET', 'POST'])
@login_required
def teacher_edit_profile():
    user = get_current_user()
    
    if user.role != 'teacher':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        
        if user.teacher_profile:
            user.teacher_profile.qualification = request.form.get('qualification')
            user.teacher_profile.experience = request.form.get('experience')
            user.teacher_profile.subjects = ','.join(request.form.getlist('subjects'))
            user.teacher_profile.teaching_mode = ','.join(request.form.getlist('teaching_mode'))
            user.teacher_profile.hourly_rate = int(request.form.get('hourly_rate'))
            user.teacher_profile.bio = request.form.get('bio')
            user.teacher_profile.city = request.form.get('city')
            user.teacher_profile.address = request.form.get('address')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))
    
    return render_template('teacher_edit_profile.html', current_user=user)


# ===== FIND TUTORS =====

@app.route('/find-tutors')
@login_required
def find_tutors():
    city = request.args.get('city', '')
    subject = request.args.get('subject', '')
    mode = request.args.get('mode', '')
    max_price = request.args.get('max_price', '')
    
    query = User.query.join(TeacherProfile).filter(User.role == 'teacher')
    
    if city:
        query = query.filter(TeacherProfile.city.ilike(f'%{city}%'))
    
    if subject:
        query = query.filter(TeacherProfile.subjects.ilike(f'%{subject}%'))
    
    if mode:
        query = query.filter(TeacherProfile.teaching_mode.ilike(f'%{mode}%'))
    
    if max_price:
        query = query.filter(TeacherProfile.hourly_rate <= int(max_price))
    
    tutors = query.all()
    
    return render_template('find_tutors.html', tutors=tutors)


# ===== TUTOR REQUEST =====

@app.route('/request-tutor/<int:teacher_id>')
@login_required
def request_tutor_page(teacher_id):
    teacher = User.query.get_or_404(teacher_id)
    
    if teacher.role != 'teacher':
        flash('Invalid teacher ID', 'error')
        return redirect(url_for('find_tutors'))
    
    return render_template('request_tutor.html', teacher=teacher, current_user=get_current_user())


@app.route('/send-tutor-request', methods=['POST'])
@login_required
def send_tutor_request():
    teacher_id = request.form.get('teacher_id')
    subject = request.form.get('subject')
    message = request.form.get('message', '')
    
    user = get_current_user()
    
    existing_request = TutorRequest.query.filter_by(
        student_id=user.id,
        teacher_id=teacher_id,
        status='pending'
    ).first()
    
    if existing_request:
        flash('You already have a pending request with this tutor!', 'error')
        return redirect(url_for('student_dashboard'))
    
    if not message:
        message = f"Hi! I'm interested in learning {subject}. Can you help?"
    
    tutor_request = TutorRequest(
        student_id=user.id,
        teacher_id=teacher_id,
        subject=subject,
        message=message,
        status='pending'
    )
    
    db.session.add(tutor_request)
    db.session.commit()
    
    flash('Request sent successfully! The tutor will respond soon.', 'success')
    return redirect(url_for('student_dashboard'))


@app.route('/handle-request', methods=['POST'])
@login_required
def handle_request():
    request_id = request.form.get('request_id')
    action = request.form.get('action')
    
    tutor_request = TutorRequest.query.get(request_id)
    
    if not tutor_request:
        flash('Request not found', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    if action == 'accept':
        tutor_request.status = 'accepted'
        flash('Request accepted!', 'success')
    elif action == 'reject':
        tutor_request.status = 'rejected'
        flash('Request declined', 'success')
    
    db.session.commit()
    return redirect(url_for('teacher_dashboard'))


# ===== CHAT ROUTES =====

@app.route('/chat')
@app.route('/chat/<int:partner_id>')
@login_required
def chat(partner_id=None):
    user = get_current_user()
    
    if user.role == 'student':
        accepted_requests = TutorRequest.query.filter_by(
            student_id=user.id,
            status='accepted'
        ).all()
        conversation_partners = [req.teacher for req in accepted_requests]
    else:
        accepted_requests = TutorRequest.query.filter_by(
            teacher_id=user.id,
            status='accepted'
        ).all()
        conversation_partners = [req.student for req in accepted_requests]
    
    conversations = []
    seen_partners = set()
    
    for partner in conversation_partners:
        if partner.id in seen_partners:
            continue
        seen_partners.add(partner.id)
        
        last_msg = Message.query.filter(
            ((Message.sender_id == user.id) & (Message.recipient_id == partner.id)) |
            ((Message.sender_id == partner.id) & (Message.recipient_id == user.id))
        ).order_by(Message.created_at.desc()).first()
        
        unread_count = Message.query.filter_by(
            sender_id=partner.id,
            recipient_id=user.id,
            is_read=False
        ).count()
        
        conversations.append({
            'partner': partner,
            'last_message': last_msg.message if last_msg else 'No messages yet',
            'last_message_time': last_msg.created_at if last_msg else None,
            'unread_count': unread_count,
            'id': partner.id
        })
    
    partner = None
    messages = []
    if partner_id:
        partner = User.query.get(partner_id)
        if partner:
            messages = Message.query.filter(
                ((Message.sender_id == user.id) & (Message.recipient_id == partner_id)) |
                ((Message.sender_id == partner_id) & (Message.recipient_id == user.id))
            ).order_by(Message.created_at.asc()).all()
            
            Message.query.filter_by(
                sender_id=partner_id,
                recipient_id=user.id,
                is_read=False
            ).update({'is_read': True})
            db.session.commit()
    
    return render_template('chat.html',
                         current_user=user,
                         conversations=conversations,
                         partner=partner,
                         messages=messages,
                         active_conversation_id=partner_id)


@app.route('/send-message', methods=['POST'])
@login_required
def send_message():
    recipient_id = request.form.get('recipient_id')
    message_text = request.form.get('message')
    
    user = get_current_user()
    
    if not message_text or not recipient_id:
        flash('Message cannot be empty', 'error')
        return redirect(url_for('chat'))
    
    message = Message(
        sender_id=user.id,
        recipient_id=recipient_id,
        message=message_text,
        is_read=False
    )
    
    db.session.add(message)
    db.session.commit()
    
    return redirect(url_for('chat', partner_id=recipient_id))


# ===== TERMS AND CONDITIONS =====

@app.route('/terms-and-conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')


@app.route('/terms-student')
def terms_student():
    return render_template('terms_student.html')


@app.route('/terms-teacher')
def terms_teacher():
    return render_template('terms_teacher.html')


# ===== PAYMENT SYSTEM ROUTES =====

@app.route('/teacher/log-class', methods=['GET', 'POST'])
@login_required
def teacher_log_class():
    user = get_current_user()
    
    if user.role != 'teacher':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    accepted_requests = TutorRequest.query.filter_by(
        teacher_id=user.id,
        status='accepted'
    ).all()
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        request_id = request.form.get('request_id')
        duration = float(request.form.get('duration', 1))
        notes = request.form.get('notes', '')
        class_date = request.form.get('class_date')
        
        hourly_rate = user.teacher_profile.hourly_rate
        amount = int(duration * hourly_rate)
        
        session_record = ClassSession(
            student_id=student_id,
            teacher_id=user.id,
            request_id=request_id,
            date=datetime.strptime(class_date, '%Y-%m-%d').date(),
            duration_hours=duration,
            hourly_rate=hourly_rate,
            amount=amount,
            notes=notes
        )
        db.session.add(session_record)
        
        cycle = PaymentCycle.query.filter_by(
            student_id=student_id,
            teacher_id=user.id,
            status='active'
        ).first()
        
        if not cycle:
            cycle = PaymentCycle(
                student_id=student_id,
                teacher_id=user.id,
                start_date=datetime.utcnow().date()
            )
            db.session.add(cycle)
        
        cycle.total_classes += 1
        cycle.total_amount += amount
        cycle.commission = int(cycle.total_amount * 0.10)
        cycle.teacher_earning = cycle.total_amount - cycle.commission
        
        if cycle.total_classes >= 25:
            cycle.status = 'pending_payment'
            cycle.end_date = datetime.utcnow().date()
        
        db.session.commit()
        flash(f'Class logged! ₹{amount} added to billing.', 'success')
        return redirect(url_for('teacher_log_class'))
    
    today = datetime.utcnow().strftime('%Y-%m-%d')
    return render_template('teacher_log_class.html', 
                         current_user=user, 
                         accepted_requests=accepted_requests,
                         today=today)


@app.route('/teacher/my-earnings')
@login_required
def teacher_earnings():
    user = get_current_user()
    
    if user.role != 'teacher':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    cycles = PaymentCycle.query.filter_by(teacher_id=user.id).order_by(PaymentCycle.created_at.desc()).all()
    
    total_earned = sum(c.teacher_earning for c in cycles if c.status == 'paid')
    pending_amount = sum(c.teacher_earning for c in cycles if c.status in ['pending_payment', 'pending_verification'])
    
    return render_template('teacher_earnings.html',
                         current_user=user,
                         cycles=cycles,
                         total_earned=total_earned,
                         pending_amount=pending_amount)


@app.route('/student/my-classes')
@login_required
def student_classes():
    user = get_current_user()
    
    if user.role != 'student':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    sessions = ClassSession.query.filter_by(student_id=user.id).order_by(ClassSession.date.desc()).all()
    
    active_cycles = PaymentCycle.query.filter_by(
        student_id=user.id,
        status='active'
    ).all()
    
    pending_payments = PaymentCycle.query.filter(
        PaymentCycle.student_id == user.id,
        PaymentCycle.status.in_(['pending_payment', 'pending_verification'])
    ).all()
    
    return render_template('student_classes.html',
                         current_user=user,
                         sessions=sessions,
                         active_cycles=active_cycles,
                         pending_payments=pending_payments)


@app.route('/student/pay/<int:cycle_id>', methods=['GET', 'POST'])
@login_required
def student_pay(cycle_id):
    user = get_current_user()
    
    if user.role != 'student':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    cycle = PaymentCycle.query.get_or_404(cycle_id)
    
    if cycle.student_id != user.id:
        flash('Access denied', 'error')
        return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        if 'screenshot' in request.files:
            file = request.files['screenshot']
            if file.filename:
                payments_dir = os.path.join('static', 'payments')
                os.makedirs(payments_dir, exist_ok=True)
                
                filename = f"payment_{cycle_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.png"
                filepath = os.path.join(payments_dir, filename)
                file.save(filepath)
                
                cycle.payment_screenshot = filepath
                cycle.status = 'pending_verification'
                db.session.commit()
                
                send_admin_notification(
                    f"Payment Received - {user.first_name} {user.last_name}",
                    f"""
                    <h2>💰 Payment Screenshot Uploaded</h2>
                    <p><strong>Student:</strong> {user.first_name} {user.last_name}</p>
                    <p><strong>Email:</strong> {user.email}</p>
                    <p><strong>Amount:</strong> ₹{cycle.total_amount}</p>
                    <p><strong>Teacher:</strong> {cycle.teacher.first_name} {cycle.teacher.last_name}</p>
                    <p><strong>Classes:</strong> {cycle.total_classes}</p>
                    <br>
                    <p>Please verify in admin panel.</p>
                    """
                )
                
                flash('Payment screenshot uploaded! We will verify and confirm soon.', 'success')
                return redirect(url_for('student_classes'))
    
    return render_template('student_pay.html',
                         current_user=user,
                         cycle=cycle,
                         upi_id='9012977681@ybl')


# ===== ADMIN ROUTES =====

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email, role='admin').first()
        
        if not user:
            flash('Invalid admin credentials', 'error')
            return redirect(url_for('admin_login'))
        
        if not user.check_password(password):
            flash('Incorrect password', 'error')
            return redirect(url_for('admin_login'))
        
        session['user_id'] = user.id
        session['user_role'] = user.role
        session.permanent = True
        
        flash('Welcome Admin!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_login.html')


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    user = get_current_user()
    
    if user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    total_students = User.query.filter_by(role='student').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_connections = TutorRequest.query.filter_by(status='accepted').count()
    total_messages = Message.query.count()
    
    recent_students = User.query.filter_by(role='student').order_by(User.created_at.desc()).limit(5).all()
    recent_teachers = User.query.filter_by(role='teacher').order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin_dashboard.html',
                         current_user=user,
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_connections=total_connections,
                         total_messages=total_messages,
                         recent_students=recent_students,
                         recent_teachers=recent_teachers)


@app.route('/admin/students')
@login_required
def admin_students():
    user = get_current_user()
    
    if user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    students = User.query.filter_by(role='student').all()
    
    student_data = []
    for student in students:
        accepted_requests = TutorRequest.query.filter_by(
            student_id=student.id,
            status='accepted'
        ).all()
        
        teachers = [req.teacher for req in accepted_requests]
        total_classes = len(accepted_requests)
        
        student_data.append({
            'student': student,
            'teachers': teachers,
            'total_classes': total_classes
        })
    
    return render_template('admin_students.html',
                         current_user=user,
                         student_data=student_data)


@app.route('/admin/teachers')
@login_required
def admin_teachers():
    user = get_current_user()
    
    if user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    teachers = User.query.filter_by(role='teacher').all()
    
    teacher_data = []
    for teacher in teachers:
        accepted_requests = TutorRequest.query.filter_by(
            teacher_id=teacher.id,
            status='accepted'
        ).all()
        
        students = [req.student for req in accepted_requests]
        total_earnings = teacher.teacher_profile.total_earnings if teacher.teacher_profile else 0
        commission = int(total_earnings * 0.10)
        
        teacher_data.append({
            'teacher': teacher,
            'students': students,
            'total_students': len(students),
            'total_earnings': total_earnings,
            'commission': commission
        })
    
    return render_template('admin_teachers.html',
                         current_user=user,
                         teacher_data=teacher_data)


@app.route('/admin/user/<int:user_id>')
@login_required
def admin_user_detail(user_id):
    admin = get_current_user()
    
    if admin.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    
    if user.role == 'student':
        connections = TutorRequest.query.filter_by(
            student_id=user.id,
            status='accepted'
        ).all()
        connected_users = [req.teacher for req in connections]
    else:
        connections = TutorRequest.query.filter_by(
            teacher_id=user.id,
            status='accepted'
        ).all()
        connected_users = [req.student for req in connections]
    
    messages = Message.query.filter(
        ((Message.sender_id == admin.id) & (Message.recipient_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.recipient_id == admin.id))
    ).order_by(Message.created_at.asc()).all()
    
    return render_template('admin_user_detail.html',
                         current_user=admin,
                         user=user,
                         connected_users=connected_users,
                         messages=messages)


@app.route('/admin/send-message/<int:user_id>', methods=['POST'])
@login_required
def admin_send_message(user_id):
    admin = get_current_user()
    
    if admin.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    message_text = request.form.get('message')
    
    if message_text:
        message = Message(
            sender_id=admin.id,
            recipient_id=user_id,
            message=message_text,
            is_read=False
        )
        db.session.add(message)
        db.session.commit()
        flash('Message sent!', 'success')
    
    return redirect(url_for('admin_user_detail', user_id=user_id))


@app.route('/admin/payments')
@login_required
def admin_payments():
    user = get_current_user()
    
    if user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    pending = PaymentCycle.query.filter_by(status='pending_verification').all()
    completed = PaymentCycle.query.filter_by(status='paid').order_by(PaymentCycle.payment_verified_at.desc()).limit(20).all()
    
    total_commission = sum(c.commission for c in PaymentCycle.query.filter_by(status='paid').all())
    
    return render_template('admin_payments.html',
                         current_user=user,
                         pending=pending,
                         completed=completed,
                         total_commission=total_commission)


@app.route('/admin/verify-payment/<int:cycle_id>', methods=['POST'])
@login_required
def admin_verify_payment(cycle_id):
    user = get_current_user()
    
    if user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    cycle = PaymentCycle.query.get_or_404(cycle_id)
    action = request.form.get('action')
    
    if action == 'approve':
        cycle.status = 'paid'
        cycle.payment_verified_at = datetime.utcnow()
        
        if cycle.teacher.teacher_profile:
            cycle.teacher.teacher_profile.total_earnings += cycle.teacher_earning
        
        new_cycle = PaymentCycle(
            student_id=cycle.student_id,
            teacher_id=cycle.teacher_id,
            start_date=datetime.utcnow().date()
        )
        db.session.add(new_cycle)
        
        flash(f'Payment verified! Teacher will receive ₹{cycle.teacher_earning}', 'success')
        
    elif action == 'reject':
        cycle.status = 'pending_payment'
        cycle.payment_screenshot = None
        flash('Payment rejected. Student will need to re-upload screenshot.', 'error')
    
    db.session.commit()
    return redirect(url_for('admin_payments'))


# ===== EXPORT ROUTES =====

@app.route('/admin/export-students')
def export_students():
    students = User.query.filter_by(role='student').all()
    
    si = StringIO()
    writer = csv.writer(si)
    
    writer.writerow(['Name', 'Email', 'Phone', 'Grade', 'Board', 'City', 'Subjects', 'Registered'])
    
    for student in students:
        if student.student_profile:
            writer.writerow([
                f"{student.first_name} {student.last_name}",
                student.email,
                student.phone,
                student.student_profile.grade,
                student.student_profile.board,
                student.student_profile.city,
                student.student_profile.subjects,
                student.created_at.strftime('%Y-%m-%d %H:%M')
            ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=vaanyan_students.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route('/admin/export-teachers')
def export_teachers():
    teachers = User.query.filter_by(role='teacher').all()
    
    si = StringIO()
    writer = csv.writer(si)
    
    writer.writerow(['Name', 'Email', 'Phone', 'Qualification', 'Experience', 'City', 'Subjects', 'Rate', 'Registered'])
    
    for teacher in teachers:
        if teacher.teacher_profile:
            writer.writerow([
                f"{teacher.first_name} {teacher.last_name}",
                teacher.email,
                teacher.phone,
                teacher.teacher_profile.qualification,
                teacher.teacher_profile.experience,
                teacher.teacher_profile.city,
                teacher.teacher_profile.subjects,
                teacher.teacher_profile.hourly_rate,
                teacher.created_at.strftime('%Y-%m-%d %H:%M')
            ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=vaanyan_teachers.csv"
    output.headers["Content-type"] = "text/csv"
    return output


# ===== CONTEXT PROCESSOR =====

@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())


# ===== INITIALIZE DATABASE =====

def create_sample_data():
    if User.query.first():
        return
    
    print("Creating admin user...")
    
    admin = User(
        role='admin',
        first_name='Vinayak',
        last_name='Mahapatra',
        email='mohapatravinayak26@gmail.com',
        phone='+91 9012977681'
    )
    admin.set_password('Nitin@123')
    db.session.add(admin)
    db.session.commit()
    
    print("✅ Admin user created!")


# ===== RUN APP =====

# Create tables on startup (important for Railway)
with app.app_context():
    db.create_all()
    create_sample_data()

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Vaanyan Home Tuition Server Starting...")
    print("="*50)
    print("\n📧 Admin Account:")
    print("   Email: mohapatravinayak26@gmail.com")
    print("   Password: Nitin@123")
    print("\n🌐 Open: http://127.0.0.1:8000")
    print("🌐 Live: https://vaanyan.com")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=8000)from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from functools import wraps
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv
from io import StringIO

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'vaanyan-home-tuition-secret-key-2025')

# Database Configuration - PostgreSQL for production, SQLite for local
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # PostgreSQL for Railway production
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # SQLite for local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vaanyan_tuition.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session Configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'mahapatravinayak@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'wrdb okdi macb zxim')
app.config['ADMIN_EMAIL'] = os.environ.get('ADMIN_EMAIL', 'mahapatravinayak@gmail.com')

# Initialize database
db = SQLAlchemy(app)

# ===== DATABASE MODELS =====

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, lazy=True)
    teacher_profile = db.relationship('TeacherProfile', backref='user', uselist=False, lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    grade = db.Column(db.String(20), nullable=False)
    board = db.Column(db.String(50), nullable=False)
    subjects = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)


class TeacherProfile(db.Model):
    __tablename__ = 'teacher_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    qualification = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.String(50), nullable=False)
    subjects = db.Column(db.Text, nullable=False)
    teaching_mode = db.Column(db.Text, nullable=False)
    hourly_rate = db.Column(db.Integer, nullable=False)
    bio = db.Column(db.Text)
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, default=5.0)
    total_students = db.Column(db.Integer, default=0)
    total_classes = db.Column(db.Integer, default=0)
    total_earnings = db.Column(db.Integer, default=0)
    is_verified = db.Column(db.Boolean, default=False)


class TutorRequest(db.Model):
    __tablename__ = 'tutor_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('User', foreign_keys=[student_id], backref='sent_requests')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='received_requests')


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')


class Class(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('tutor_requests.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    scheduled_at = db.Column(db.String(100), nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    status = db.Column(db.String(20), default='scheduled')
    meeting_link = db.Column(db.String(500))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ClassSession(db.Model):
    __tablename__ = 'class_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('tutor_requests.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    duration_hours = db.Column(db.Float, default=1.0)
    hourly_rate = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='completed')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('User', foreign_keys=[student_id], backref='student_sessions')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='teacher_sessions')


class PaymentCycle(db.Model):
    __tablename__ = 'payment_cycles'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    total_classes = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Integer, default=0)
    commission = db.Column(db.Integer, default=0)
    teacher_earning = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')
    payment_screenshot = db.Column(db.String(500))
    payment_verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('User', foreign_keys=[student_id], backref='student_payments')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='teacher_payments')


# ===== HELPER FUNCTIONS =====

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


def send_admin_notification(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = app.config['ADMIN_EMAIL']
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent: {subject}")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False


# ===== MAIN ROUTES =====

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/choose-role')
def choose_role():
    return render_template('choose_role.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('No account found with this email address', 'error')
            return redirect(url_for('login'))
        
        if not user.check_password(password):
            flash('Incorrect password. Please try again', 'error')
            return redirect(url_for('login'))
        
        if not user.is_active:
            flash('Your account has been deactivated', 'error')
            return redirect(url_for('login'))
        
        session['user_id'] = user.id
        session['user_role'] = user.role
        session.permanent = True
        
        flash(f'Welcome back, {user.first_name}!', 'success')
        
        if user.role == 'student':
            return redirect(url_for('student_dashboard'))
        elif user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('teacher_dashboard'))
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('home'))


# ===== STUDENT REGISTRATION =====

@app.route('/student/register', methods=['GET', 'POST'])
def student_registration():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        grade = request.form.get('grade')
        board = request.form.get('board')
        city = request.form.get('city')
        address = request.form.get('address')
        subjects = request.form.getlist('subjects')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('student_registration'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('student_registration'))
        
        user = User(
            role='student',
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()
        
        student_profile = StudentProfile(
            user_id=user.id,
            grade=grade,
            board=board,
            subjects=','.join(subjects),
            city=city,
            address=address
        )
        
        db.session.add(student_profile)
        db.session.commit()
        
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #6366f1;">🎓 New Student Registration!</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr><td style="padding: 8px; font-weight: bold;">Name:</td><td style="padding: 8px;">{first_name} {last_name}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Email:</td><td style="padding: 8px;">{email}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Phone:</td><td style="padding: 8px;">{phone}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Grade:</td><td style="padding: 8px;">{grade}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Board:</td><td style="padding: 8px;">{board}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">City:</td><td style="padding: 8px;">{city}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Subjects:</td><td style="padding: 8px;">{', '.join(subjects)}</td></tr>
            </table>
        </body>
        </html>
        """
        send_admin_notification(f"New Student: {first_name} {last_name}", email_body)
        
        flash('Registration successful! Please login', 'success')
        return redirect(url_for('login'))
    
    return render_template('student_registration.html')


# ===== TEACHER REGISTRATION =====

@app.route('/teacher/register', methods=['GET', 'POST'])
def teacher_registration():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        qualification = request.form.get('qualification')
        experience = request.form.get('experience')
        city = request.form.get('city')
        address = request.form.get('address')
        subjects = request.form.getlist('subjects')
        teaching_mode = request.form.getlist('teaching_mode')
        hourly_rate = request.form.get('hourly_rate')
        bio = request.form.get('bio', '')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('teacher_registration'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('teacher_registration'))
        
        user = User(
            role='teacher',
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()
        
        teacher_profile = TeacherProfile(
            user_id=user.id,
            qualification=qualification,
            experience=experience,
            subjects=','.join(subjects),
            teaching_mode=','.join(teaching_mode),
            hourly_rate=int(hourly_rate),
            bio=bio,
            city=city,
            address=address
        )
        
        db.session.add(teacher_profile)
        db.session.commit()
        
        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #6366f1;">👨‍🏫 New Teacher Registration!</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr><td style="padding: 8px; font-weight: bold;">Name:</td><td style="padding: 8px;">{first_name} {last_name}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Email:</td><td style="padding: 8px;">{email}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Phone:</td><td style="padding: 8px;">{phone}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Qualification:</td><td style="padding: 8px;">{qualification}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Experience:</td><td style="padding: 8px;">{experience}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">City:</td><td style="padding: 8px;">{city}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Subjects:</td><td style="padding: 8px;">{', '.join(subjects)}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Teaching Mode:</td><td style="padding: 8px;">{', '.join(teaching_mode)}</td></tr>
                <tr><td style="padding: 8px; font-weight: bold;">Hourly Rate:</td><td style="padding: 8px;">₹{hourly_rate}</td></tr>
            </table>
        </body>
        </html>
        """
        send_admin_notification(f"New Teacher: {first_name} {last_name}", email_body)
        
        flash('Registration successful! Please login', 'success')
        return redirect(url_for('login'))
    
    return render_template('teacher_registration.html')


# ===== STUDENT DASHBOARD =====

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    user = get_current_user()
    
    if user.role != 'student':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    if user.student_profile:
        tutors = User.query.join(TeacherProfile).filter(
            User.role == 'teacher',
            TeacherProfile.city == user.student_profile.city
        ).limit(6).all()
    else:
        tutors = []
    
    classes = []
    
    unread_messages = Message.query.filter_by(
        recipient_id=user.id,
        is_read=False
    ).count()
    
    # Admin messages
    admin_users = User.query.filter_by(role='admin').all()
    admin_ids = [admin.id for admin in admin_users]
    
    admin_messages = Message.query.filter(
        Message.recipient_id == user.id,
        Message.sender_id.in_(admin_ids)
    ).order_by(Message.created_at.desc()).limit(10).all()
    
    return render_template('student_dashboard.html', 
                         current_user=user,
                         tutors=tutors,
                         classes=classes,
                         messages=range(unread_messages),
                         admin_messages=admin_messages)


# ===== TEACHER DASHBOARD =====

@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    user = get_current_user()
    
    if user.role != 'teacher':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    pending_requests = TutorRequest.query.filter_by(
        teacher_id=user.id,
        status='pending'
    ).all()
    
    accepted_request_ids = [req.id for req in TutorRequest.query.filter_by(
        teacher_id=user.id,
        status='accepted'
    ).all()]
    
    students = []
    if accepted_request_ids:
        student_ids = [req.student_id for req in TutorRequest.query.filter(
            TutorRequest.id.in_(accepted_request_ids)
        ).all()]
        students = User.query.filter(User.id.in_(student_ids)).all()
    
    classes = []
    monthly_earnings = user.teacher_profile.total_earnings if user.teacher_profile else 0
    
    unread_messages = Message.query.filter_by(
        recipient_id=user.id,
        is_read=False
    ).count()
    
    # Admin messages
    admin_users = User.query.filter_by(role='admin').all()
    admin_ids = [admin.id for admin in admin_users]
    
    admin_messages = Message.query.filter(
        Message.recipient_id == user.id,
        Message.sender_id.in_(admin_ids)
    ).order_by(Message.created_at.desc()).limit(10).all()
    
    return render_template('teacher_dashboard.html',
                         current_user=user,
                         pending_requests=pending_requests,
                         students=students,
                         classes=classes,
                         monthly_earnings=monthly_earnings,
                         messages=range(unread_messages),
                         admin_messages=admin_messages)


# ===== PROFILE EDIT ROUTES =====

@app.route('/student/edit-profile', methods=['GET', 'POST'])
@login_required
def student_edit_profile():
    user = get_current_user()
    
    if user.role != 'student':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        
        if user.student_profile:
            user.student_profile.grade = request.form.get('grade')
            user.student_profile.board = request.form.get('board')
            user.student_profile.subjects = ','.join(request.form.getlist('subjects'))
            user.student_profile.city = request.form.get('city')
            user.student_profile.address = request.form.get('address')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student_dashboard'))
    
    return render_template('student_edit_profile.html', current_user=user)


@app.route('/teacher/edit-profile', methods=['GET', 'POST'])
@login_required
def teacher_edit_profile():
    user = get_current_user()
    
    if user.role != 'teacher':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        
        if user.teacher_profile:
            user.teacher_profile.qualification = request.form.get('qualification')
            user.teacher_profile.experience = request.form.get('experience')
            user.teacher_profile.subjects = ','.join(request.form.getlist('subjects'))
            user.teacher_profile.teaching_mode = ','.join(request.form.getlist('teaching_mode'))
            user.teacher_profile.hourly_rate = int(request.form.get('hourly_rate'))
            user.teacher_profile.bio = request.form.get('bio')
            user.teacher_profile.city = request.form.get('city')
            user.teacher_profile.address = request.form.get('address')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))
    
    return render_template('teacher_edit_profile.html', current_user=user)


# ===== FIND TUTORS =====

@app.route('/find-tutors')
@login_required
def find_tutors():
    city = request.args.get('city', '')
    subject = request.args.get('subject', '')
    mode = request.args.get('mode', '')
    max_price = request.args.get('max_price', '')
    
    query = User.query.join(TeacherProfile).filter(User.role == 'teacher')
    
    if city:
        query = query.filter(TeacherProfile.city.ilike(f'%{city}%'))
    
    if subject:
        query = query.filter(TeacherProfile.subjects.ilike(f'%{subject}%'))
    
    if mode:
        query = query.filter(TeacherProfile.teaching_mode.ilike(f'%{mode}%'))
    
    if max_price:
        query = query.filter(TeacherProfile.hourly_rate <= int(max_price))
    
    tutors = query.all()
    
    return render_template('find_tutors.html', tutors=tutors)


# ===== TUTOR REQUEST =====

@app.route('/request-tutor/<int:teacher_id>')
@login_required
def request_tutor_page(teacher_id):
    teacher = User.query.get_or_404(teacher_id)
    
    if teacher.role != 'teacher':
        flash('Invalid teacher ID', 'error')
        return redirect(url_for('find_tutors'))
    
    return render_template('request_tutor.html', teacher=teacher, current_user=get_current_user())


@app.route('/send-tutor-request', methods=['POST'])
@login_required
def send_tutor_request():
    teacher_id = request.form.get('teacher_id')
    subject = request.form.get('subject')
    message = request.form.get('message', '')
    
    user = get_current_user()
    
    existing_request = TutorRequest.query.filter_by(
        student_id=user.id,
        teacher_id=teacher_id,
        status='pending'
    ).first()
    
    if existing_request:
        flash('You already have a pending request with this tutor!', 'error')
        return redirect(url_for('student_dashboard'))
    
    if not message:
        message = f"Hi! I'm interested in learning {subject}. Can you help?"
    
    tutor_request = TutorRequest(
        student_id=user.id,
        teacher_id=teacher_id,
        subject=subject,
        message=message,
        status='pending'
    )
    
    db.session.add(tutor_request)
    db.session.commit()
    
    flash('Request sent successfully! The tutor will respond soon.', 'success')
    return redirect(url_for('student_dashboard'))


@app.route('/handle-request', methods=['POST'])
@login_required
def handle_request():
    request_id = request.form.get('request_id')
    action = request.form.get('action')
    
    tutor_request = TutorRequest.query.get(request_id)
    
    if not tutor_request:
        flash('Request not found', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    if action == 'accept':
        tutor_request.status = 'accepted'
        flash('Request accepted!', 'success')
    elif action == 'reject':
        tutor_request.status = 'rejected'
        flash('Request declined', 'success')
    
    db.session.commit()
    return redirect(url_for('teacher_dashboard'))


# ===== CHAT ROUTES =====

@app.route('/chat')
@app.route('/chat/<int:partner_id>')
@login_required
def chat(partner_id=None):
    user = get_current_user()
    
    if user.role == 'student':
        accepted_requests = TutorRequest.query.filter_by(
            student_id=user.id,
            status='accepted'
        ).all()
        conversation_partners = [req.teacher for req in accepted_requests]
    else:
        accepted_requests = TutorRequest.query.filter_by(
            teacher_id=user.id,
            status='accepted'
        ).all()
        conversation_partners = [req.student for req in accepted_requests]
    
    conversations = []
    seen_partners = set()
    
    for partner in conversation_partners:
        if partner.id in seen_partners:
            continue
        seen_partners.add(partner.id)
        
        last_msg = Message.query.filter(
            ((Message.sender_id == user.id) & (Message.recipient_id == partner.id)) |
            ((Message.sender_id == partner.id) & (Message.recipient_id == user.id))
        ).order_by(Message.created_at.desc()).first()
        
        unread_count = Message.query.filter_by(
            sender_id=partner.id,
            recipient_id=user.id,
            is_read=False
        ).count()
        
        conversations.append({
            'partner': partner,
            'last_message': last_msg.message if last_msg else 'No messages yet',
            'last_message_time': last_msg.created_at if last_msg else None,
            'unread_count': unread_count,
            'id': partner.id
        })
    
    partner = None
    messages = []
    if partner_id:
        partner = User.query.get(partner_id)
        if partner:
            messages = Message.query.filter(
                ((Message.sender_id == user.id) & (Message.recipient_id == partner_id)) |
                ((Message.sender_id == partner_id) & (Message.recipient_id == user.id))
            ).order_by(Message.created_at.asc()).all()
            
            Message.query.filter_by(
                sender_id=partner_id,
                recipient_id=user.id,
                is_read=False
            ).update({'is_read': True})
            db.session.commit()
    
    return render_template('chat.html',
                         current_user=user,
                         conversations=conversations,
                         partner=partner,
                         messages=messages,
                         active_conversation_id=partner_id)


@app.route('/send-message', methods=['POST'])
@login_required
def send_message():
    recipient_id = request.form.get('recipient_id')
    message_text = request.form.get('message')
    
    user = get_current_user()
    
    if not message_text or not recipient_id:
        flash('Message cannot be empty', 'error')
        return redirect(url_for('chat'))
    
    message = Message(
        sender_id=user.id,
        recipient_id=recipient_id,
        message=message_text,
        is_read=False
    )
    
    db.session.add(message)
    db.session.commit()
    
    return redirect(url_for('chat', partner_id=recipient_id))


# ===== TERMS AND CONDITIONS =====

@app.route('/terms-and-conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')


@app.route('/terms-student')
def terms_student():
    return render_template('terms_student.html')


@app.route('/terms-teacher')
def terms_teacher():
    return render_template('terms_teacher.html')


# ===== PAYMENT SYSTEM ROUTES =====

@app.route('/teacher/log-class', methods=['GET', 'POST'])
@login_required
def teacher_log_class():
    user = get_current_user()
    
    if user.role != 'teacher':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    accepted_requests = TutorRequest.query.filter_by(
        teacher_id=user.id,
        status='accepted'
    ).all()
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        request_id = request.form.get('request_id')
        duration = float(request.form.get('duration', 1))
        notes = request.form.get('notes', '')
        class_date = request.form.get('class_date')
        
        hourly_rate = user.teacher_profile.hourly_rate
        amount = int(duration * hourly_rate)
        
        session_record = ClassSession(
            student_id=student_id,
            teacher_id=user.id,
            request_id=request_id,
            date=datetime.strptime(class_date, '%Y-%m-%d').date(),
            duration_hours=duration,
            hourly_rate=hourly_rate,
            amount=amount,
            notes=notes
        )
        db.session.add(session_record)
        
        cycle = PaymentCycle.query.filter_by(
            student_id=student_id,
            teacher_id=user.id,
            status='active'
        ).first()
        
        if not cycle:
            cycle = PaymentCycle(
                student_id=student_id,
                teacher_id=user.id,
                start_date=datetime.utcnow().date()
            )
            db.session.add(cycle)
        
        cycle.total_classes += 1
        cycle.total_amount += amount
        cycle.commission = int(cycle.total_amount * 0.10)
        cycle.teacher_earning = cycle.total_amount - cycle.commission
        
        if cycle.total_classes >= 25:
            cycle.status = 'pending_payment'
            cycle.end_date = datetime.utcnow().date()
        
        db.session.commit()
        flash(f'Class logged! ₹{amount} added to billing.', 'success')
        return redirect(url_for('teacher_log_class'))
    
    today = datetime.utcnow().strftime('%Y-%m-%d')
    return render_template('teacher_log_class.html', 
                         current_user=user, 
                         accepted_requests=accepted_requests,
                         today=today)


@app.route('/teacher/my-earnings')
@login_required
def teacher_earnings():
    user = get_current_user()
    
    if user.role != 'teacher':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    cycles = PaymentCycle.query.filter_by(teacher_id=user.id).order_by(PaymentCycle.created_at.desc()).all()
    
    total_earned = sum(c.teacher_earning for c in cycles if c.status == 'paid')
    pending_amount = sum(c.teacher_earning for c in cycles if c.status in ['pending_payment', 'pending_verification'])
    
    return render_template('teacher_earnings.html',
                         current_user=user,
                         cycles=cycles,
                         total_earned=total_earned,
                         pending_amount=pending_amount)


@app.route('/student/my-classes')
@login_required
def student_classes():
    user = get_current_user()
    
    if user.role != 'student':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    sessions = ClassSession.query.filter_by(student_id=user.id).order_by(ClassSession.date.desc()).all()
    
    active_cycles = PaymentCycle.query.filter_by(
        student_id=user.id,
        status='active'
    ).all()
    
    pending_payments = PaymentCycle.query.filter(
        PaymentCycle.student_id == user.id,
        PaymentCycle.status.in_(['pending_payment', 'pending_verification'])
    ).all()
    
    return render_template('student_classes.html',
                         current_user=user,
                         sessions=sessions,
                         active_cycles=active_cycles,
                         pending_payments=pending_payments)


@app.route('/student/pay/<int:cycle_id>', methods=['GET', 'POST'])
@login_required
def student_pay(cycle_id):
    user = get_current_user()
    
    if user.role != 'student':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    cycle = PaymentCycle.query.get_or_404(cycle_id)
    
    if cycle.student_id != user.id:
        flash('Access denied', 'error')
        return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        if 'screenshot' in request.files:
            file = request.files['screenshot']
            if file.filename:
                payments_dir = os.path.join('static', 'payments')
                os.makedirs(payments_dir, exist_ok=True)
                
                filename = f"payment_{cycle_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.png"
                filepath = os.path.join(payments_dir, filename)
                file.save(filepath)
                
                cycle.payment_screenshot = filepath
                cycle.status = 'pending_verification'
                db.session.commit()
                
                send_admin_notification(
                    f"Payment Received - {user.first_name} {user.last_name}",
                    f"""
                    <h2>💰 Payment Screenshot Uploaded</h2>
                    <p><strong>Student:</strong> {user.first_name} {user.last_name}</p>
                    <p><strong>Email:</strong> {user.email}</p>
                    <p><strong>Amount:</strong> ₹{cycle.total_amount}</p>
                    <p><strong>Teacher:</strong> {cycle.teacher.first_name} {cycle.teacher.last_name}</p>
                    <p><strong>Classes:</strong> {cycle.total_classes}</p>
                    <br>
                    <p>Please verify in admin panel.</p>
                    """
                )
                
                flash('Payment screenshot uploaded! We will verify and confirm soon.', 'success')
                return redirect(url_for('student_classes'))
    
    return render_template('student_pay.html',
                         current_user=user,
                         cycle=cycle,
                         upi_id='9012977681@ybl')


# ===== ADMIN ROUTES =====

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email, role='admin').first()
        
        if not user:
            flash('Invalid admin credentials', 'error')
            return redirect(url_for('admin_login'))
        
        if not user.check_password(password):
            flash('Incorrect password', 'error')
            return redirect(url_for('admin_login'))
        
        session['user_id'] = user.id
        session['user_role'] = user.role
        session.permanent = True
        
        flash('Welcome Admin!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_login.html')


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    user = get_current_user()
    
    if user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    total_students = User.query.filter_by(role='student').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_connections = TutorRequest.query.filter_by(status='accepted').count()
    total_messages = Message.query.count()
    
    recent_students = User.query.filter_by(role='student').order_by(User.created_at.desc()).limit(5).all()
    recent_teachers = User.query.filter_by(role='teacher').order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin_dashboard.html',
                         current_user=user,
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_connections=total_connections,
                         total_messages=total_messages,
                         recent_students=recent_students,
                         recent_teachers=recent_teachers)


@app.route('/admin/students')
@login_required
def admin_students():
    user = get_current_user()
    
    if user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    students = User.query.filter_by(role='student').all()
    
    student_data = []
    for student in students:
        accepted_requests = TutorRequest.query.filter_by(
            student_id=student.id,
            status='accepted'
        ).all()
        
        teachers = [req.teacher for req in accepted_requests]
        total_classes = len(accepted_requests)
        
        student_data.append({
            'student': student,
            'teachers': teachers,
            'total_classes': total_classes
        })
    
    return render_template('admin_students.html',
                         current_user=user,
                         student_data=student_data)


@app.route('/admin/teachers')
@login_required
def admin_teachers():
    user = get_current_user()
    
    if user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    teachers = User.query.filter_by(role='teacher').all()
    
    teacher_data = []
    for teacher in teachers:
        accepted_requests = TutorRequest.query.filter_by(
            teacher_id=teacher.id,
            status='accepted'
        ).all()
        
        students = [req.student for req in accepted_requests]
        total_earnings = teacher.teacher_profile.total_earnings if teacher.teacher_profile else 0
        commission = int(total_earnings * 0.10)
        
        teacher_data.append({
            'teacher': teacher,
            'students': students,
            'total_students': len(students),
            'total_earnings': total_earnings,
            'commission': commission
        })
    
    return render_template('admin_teachers.html',
                         current_user=user,
                         teacher_data=teacher_data)


@app.route('/admin/user/<int:user_id>')
@login_required
def admin_user_detail(user_id):
    admin = get_current_user()
    
    if admin.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    
    if user.role == 'student':
        connections = TutorRequest.query.filter_by(
            student_id=user.id,
            status='accepted'
        ).all()
        connected_users = [req.teacher for req in connections]
    else:
        connections = TutorRequest.query.filter_by(
            teacher_id=user.id,
            status='accepted'
        ).all()
        connected_users = [req.student for req in connections]
    
    messages = Message.query.filter(
        ((Message.sender_id == admin.id) & (Message.recipient_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.recipient_id == admin.id))
    ).order_by(Message.created_at.asc()).all()
    
    return render_template('admin_user_detail.html',
                         current_user=admin,
                         user=user,
                         connected_users=connected_users,
                         messages=messages)


@app.route('/admin/send-message/<int:user_id>', methods=['POST'])
@login_required
def admin_send_message(user_id):
    admin = get_current_user()
    
    if admin.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    message_text = request.form.get('message')
    
    if message_text:
        message = Message(
            sender_id=admin.id,
            recipient_id=user_id,
            message=message_text,
            is_read=False
        )
        db.session.add(message)
        db.session.commit()
        flash('Message sent!', 'success')
    
    return redirect(url_for('admin_user_detail', user_id=user_id))


@app.route('/admin/payments')
@login_required
def admin_payments():
    user = get_current_user()
    
    if user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    pending = PaymentCycle.query.filter_by(status='pending_verification').all()
    completed = PaymentCycle.query.filter_by(status='paid').order_by(PaymentCycle.payment_verified_at.desc()).limit(20).all()
    
    total_commission = sum(c.commission for c in PaymentCycle.query.filter_by(status='paid').all())
    
    return render_template('admin_payments.html',
                         current_user=user,
                         pending=pending,
                         completed=completed,
                         total_commission=total_commission)


@app.route('/admin/verify-payment/<int:cycle_id>', methods=['POST'])
@login_required
def admin_verify_payment(cycle_id):
    user = get_current_user()
    
    if user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    cycle = PaymentCycle.query.get_or_404(cycle_id)
    action = request.form.get('action')
    
    if action == 'approve':
        cycle.status = 'paid'
        cycle.payment_verified_at = datetime.utcnow()
        
        if cycle.teacher.teacher_profile:
            cycle.teacher.teacher_profile.total_earnings += cycle.teacher_earning
        
        new_cycle = PaymentCycle(
            student_id=cycle.student_id,
            teacher_id=cycle.teacher_id,
            start_date=datetime.utcnow().date()
        )
        db.session.add(new_cycle)
        
        flash(f'Payment verified! Teacher will receive ₹{cycle.teacher_earning}', 'success')
        
    elif action == 'reject':
        cycle.status = 'pending_payment'
        cycle.payment_screenshot = None
        flash('Payment rejected. Student will need to re-upload screenshot.', 'error')
    
    db.session.commit()
    return redirect(url_for('admin_payments'))


# ===== EXPORT ROUTES =====

@app.route('/admin/export-students')
def export_students():
    students = User.query.filter_by(role='student').all()
    
    si = StringIO()
    writer = csv.writer(si)
    
    writer.writerow(['Name', 'Email', 'Phone', 'Grade', 'Board', 'City', 'Subjects', 'Registered'])
    
    for student in students:
        if student.student_profile:
            writer.writerow([
                f"{student.first_name} {student.last_name}",
                student.email,
                student.phone,
                student.student_profile.grade,
                student.student_profile.board,
                student.student_profile.city,
                student.student_profile.subjects,
                student.created_at.strftime('%Y-%m-%d %H:%M')
            ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=vaanyan_students.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route('/admin/export-teachers')
def export_teachers():
    teachers = User.query.filter_by(role='teacher').all()
    
    si = StringIO()
    writer = csv.writer(si)
    
    writer.writerow(['Name', 'Email', 'Phone', 'Qualification', 'Experience', 'City', 'Subjects', 'Rate', 'Registered'])
    
    for teacher in teachers:
        if teacher.teacher_profile:
            writer.writerow([
                f"{teacher.first_name} {teacher.last_name}",
                teacher.email,
                teacher.phone,
                teacher.teacher_profile.qualification,
                teacher.teacher_profile.experience,
                teacher.teacher_profile.city,
                teacher.teacher_profile.subjects,
                teacher.teacher_profile.hourly_rate,
                teacher.created_at.strftime('%Y-%m-%d %H:%M')
            ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=vaanyan_teachers.csv"
    output.headers["Content-type"] = "text/csv"
    return output


# ===== CONTEXT PROCESSOR =====

@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())


# ===== INITIALIZE DATABASE =====

def create_sample_data():
    if User.query.first():
        return
    
    print("Creating admin user...")
    
    admin = User(
        role='admin',
        first_name='Vinayak',
        last_name='Mahapatra',
        email='mohapatravinayak26@gmail.com',
        phone='+91 9012977681'
    )
    admin.set_password('Nitin@123')
    db.session.add(admin)
    db.session.commit()
    
    print("✅ Admin user created!")


# ===== RUN APP =====

# Create tables on startup (important for Railway)
with app.app_context():
    db.create_all()
    create_sample_data()

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Vaanyan Home Tuition Server Starting...")
    print("="*50)
    print("\n📧 Admin Account:")
    print("   Email: mohapatravinayak26@gmail.com")
    print("   Password: Nitin@123")
    print("\n🌐 Open: http://127.0.0.1:8000")
    print("🌐 Live: https://vaanyan.com")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=8000)
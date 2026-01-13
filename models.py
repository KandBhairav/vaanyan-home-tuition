from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from enum import Enum

db = SQLAlchemy()

class UserRole(Enum):
    STUDENT = "student"
    TEACHER = "teacher"

class RequestStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.Enum(UserRole), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.Text, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    teacher_profile = db.relationship('TeacherProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    sent_requests = db.relationship('TutorRequest', foreign_keys='TutorRequest.student_id', backref='student', cascade='all, delete-orphan')
    received_requests = db.relationship('TutorRequest', foreign_keys='TutorRequest.teacher_id', backref='teacher', cascade='all, delete-orphan')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', cascade='all, delete-orphan')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'role': self.role.value,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    grade = db.Column(db.String(10), nullable=False)  # Class 1-12, College
    board = db.Column(db.String(20), nullable=False)  # CBSE, ICSE, State, etc.
    subjects = db.Column(db.JSON, nullable=False)  # List of subjects
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'grade': self.grade,
            'board': self.board,
            'subjects': self.subjects,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TeacherProfile(db.Model):
    __tablename__ = 'teacher_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    qualification = db.Column(db.String(50), nullable=False)
    experience = db.Column(db.String(20), nullable=False)
    subjects = db.Column(db.JSON, nullable=False)  # List of subjects
    hourly_rate = db.Column(db.Float, nullable=False)
    bio = db.Column(db.Text)
    rating = db.Column(db.Float, default=0.0)
    total_students = db.Column(db.Integer, default=0)
    total_classes = db.Column(db.Integer, default=0)
    total_earnings = db.Column(db.Float, default=0.0)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'qualification': self.qualification,
            'experience': self.experience,
            'subjects': self.subjects,
            'hourly_rate': self.hourly_rate,
            'bio': self.bio,
            'rating': self.rating,
            'total_students': self.total_students,
            'total_classes': self.total_classes,
            'total_earnings': self.total_earnings,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TutorRequest(db.Model):
    __tablename__ = 'tutor_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.Enum(RequestStatus), default=RequestStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    classes = db.relationship('Class', backref='request', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'teacher_id': self.teacher_id,
            'student_name': self.student.full_name if self.student else None,
            'teacher_name': self.teacher.full_name if self.teacher else None,
            'subject': self.subject,
            'message': self.message,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Class(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('tutor_requests.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, ongoing, completed, cancelled
    meeting_link = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'title': self.title,
            'description': self.description,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'duration_minutes': self.duration_minutes,
            'status': self.status,
            'meeting_link': self.meeting_link,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'sender_name': self.sender.full_name if self.sender else None,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student_reviewer = db.relationship('User', foreign_keys=[student_id], backref='given_reviews')
    teacher_reviewed = db.relationship('User', foreign_keys=[teacher_id], backref='received_reviews')
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'teacher_id': self.teacher_id,
            'student_name': self.student_reviewer.full_name if self.student_reviewer else None,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Database helper functions
def init_db(app):
    """Initialize database with app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Add sample data if tables are empty
        if User.query.count() == 0:
            create_sample_data()

def create_sample_data():
    """Create sample users and data"""
    try:
        # Sample Teacher 1 - Mathematics & Physics
        teacher_user = User(
            role=UserRole.TEACHER,
            first_name='Rajesh',
            last_name='Sharma',
            email='rajesh@vaanyan.com',
            phone='+91 98765 43210',
            address='A-42, Sector 18, Noida, Uttar Pradesh 201301'
        )
        teacher_user.set_password('password123')
        db.session.add(teacher_user)
        db.session.flush()  # Get the ID
        
        teacher_profile = TeacherProfile(
            user_id=teacher_user.id,
            qualification='masters',
            experience='5-10',
            subjects=['mathematics', 'physics'],
            hourly_rate=500.0,
            bio='M.Sc. Mathematics from Delhi University with 8+ years of teaching experience. Specialized in JEE/NEET preparation and board exams. I believe in making mathematics fun and easy to understand through practical examples.',
            rating=4.8,
            total_students=15,
            total_classes=180,
            total_earnings=45000.0,
            is_verified=True
        )
        db.session.add(teacher_profile)
        
        # Sample Teacher 2 - Chemistry & Biology
        teacher_user2 = User(
            role=UserRole.TEACHER,
            first_name='Priya',
            last_name='Patel',
            email='priya@vaanyan.com',
            phone='+91 87654 32100',
            address='B-15, Andheri West, Mumbai, Maharashtra 400058'
        )
        teacher_user2.set_password('password123')
        db.session.add(teacher_user2)
        db.session.flush()
        
        teacher_profile2 = TeacherProfile(
            user_id=teacher_user2.id,
            qualification='phd',
            experience='10+',
            subjects=['chemistry', 'biology'],
            hourly_rate=700.0,
            bio='PhD in Organic Chemistry from IIT Bombay. 12+ years of teaching experience in medical entrance preparation. Expert in NEET, JEE Advanced, and board exam preparation.',
            rating=4.9,
            total_students=25,
            total_classes=320,
            total_earnings=78000.0,
            is_verified=True
        )
        db.session.add(teacher_profile2)
        
        # Sample Teacher 3 - English & Hindi
        teacher_user3 = User(
            role=UserRole.TEACHER,
            first_name='Anita',
            last_name='Singh',
            email='anita@vaanyan.com',
            phone='+91 76543 21098',
            address='C-301, Sector 62, Gurgaon, Haryana 122102'
        )
        teacher_user3.set_password('password123')
        db.session.add(teacher_user3)
        db.session.flush()
        
        teacher_profile3 = TeacherProfile(
            user_id=teacher_user3.id,
            qualification='masters',
            experience='3-5',
            subjects=['english', 'hindi'],
            hourly_rate=400.0,
            bio='MA in English Literature with specialization in creative writing and grammar. 5 years of experience in teaching English and Hindi to students from class 6-12.',
            rating=4.7,
            total_students=10,
            total_classes=95,
            total_earnings=28000.0,
            is_verified=True
        )
        db.session.add(teacher_profile3)
        
        # Sample Student 1 - Class 10
        student_user = User(
            role=UserRole.STUDENT,
            first_name='Rahul',
            last_name='Kumar',
            email='rahul@vaanyan.com',
            phone='+91 87654 32109',
            address='D-25, Lajpat Nagar, New Delhi 110024'
        )
        student_user.set_password('password123')
        db.session.add(student_user)
        db.session.flush()
        
        student_profile = StudentProfile(
            user_id=student_user.id,
            grade='10',
            board='cbse',
            subjects=['mathematics', 'physics', 'chemistry', 'english']
        )
        db.session.add(student_profile)
        
        # Sample Student 2 - Class 12
        student_user2 = User(
            role=UserRole.STUDENT,
            first_name='Ananya',
            last_name='Gupta',
            email='ananya@vaanyan.com',
            phone='+91 76543 21087',
            address='E-14, Bandra East, Mumbai, Maharashtra 400051'
        )
        student_user2.set_password('password123')
        db.session.add(student_user2)
        db.session.flush()
        
        student_profile2 = StudentProfile(
            user_id=student_user2.id,
            grade='12',
            board='cbse',
            subjects=['chemistry', 'biology', 'physics', 'english']
        )
        db.session.add(student_profile2)
        
        # Sample Student 3 - Class 8
        student_user3 = User(
            role=UserRole.STUDENT,
            first_name='Arjun',
            last_name='Verma',
            email='arjun@vaanyan.com',
            phone='+91 65432 10987',
            address='F-8, Koramangala, Bangalore, Karnataka 560034'
        )
        student_user3.set_password('password123')
        db.session.add(student_user3)
        db.session.flush()
        
        student_profile3 = StudentProfile(
            user_id=student_user3.id,
            grade='8',
            board='cbse',
            subjects=['mathematics', 'english', 'hindi']
        )
        db.session.add(student_profile3)
        
        # Commit all users first
        db.session.commit()
        
        # Sample Requests
        sample_request1 = TutorRequest(
            student_id=student_user.id,
            teacher_id=teacher_user.id,
            subject='mathematics',
            message='Hello sir, I need help with quadratic equations and coordinate geometry for my board exams. Can we schedule regular classes?',
            status=RequestStatus.ACCEPTED
        )
        db.session.add(sample_request1)
        
        sample_request2 = TutorRequest(
            student_id=student_user2.id,
            teacher_id=teacher_user2.id,
            subject='chemistry',
            message='Hi ma\'am, I need help with organic chemistry preparation for NEET. Looking for weekend classes.',
            status=RequestStatus.ACCEPTED
        )
        db.session.add(sample_request2)
        
        sample_request3 = TutorRequest(
            student_id=student_user3.id,
            teacher_id=teacher_user3.id,
            subject='english',
            message='Hello ma\'am, I want to improve my English grammar and writing skills. Please help.',
            status=RequestStatus.PENDING
        )
        db.session.add(sample_request3)
        
        # Sample Messages
        messages_data = [
            {
                'sender_id': teacher_user.id,
                'recipient_id': student_user.id,
                'message': 'Hello Rahul! I hope you\'re doing well. How was your practice with the quadratic equations we discussed yesterday?'
            },
            {
                'sender_id': student_user.id,
                'recipient_id': teacher_user.id,
                'message': 'Hi sir! I practiced all the problems you gave me. I\'m still struggling with the discriminant part. Can you explain it again?'
            },
            {
                'sender_id': teacher_user.id,
                'recipient_id': student_user.id,
                'message': 'Of course! The discriminant (b²-4ac) tells us about the nature of roots. Let\'s schedule a quick session tomorrow to clear your doubts.'
            },
            {
                'sender_id': teacher_user2.id,
                'recipient_id': student_user2.id,
                'message': 'Hi Ananya! Great progress in today\'s organic chemistry session. Don\'t forget to practice the reaction mechanisms we covered.'
            },
            {
                'sender_id': student_user2.id,
                'recipient_id': teacher_user2.id,
                'message': 'Thank you ma\'am! The SN1 and SN2 reactions are much clearer now. I\'ll complete the assignments you gave.'
            }
        ]
        
        for msg_data in messages_data:
            message = Message(
                sender_id=msg_data['sender_id'],
                recipient_id=msg_data['recipient_id'],
                message=msg_data['message']
            )
            db.session.add(message)
        
        # Sample Reviews
        reviews_data = [
            {
                'student_id': student_user.id,
                'teacher_id': teacher_user.id,
                'rating': 5,
                'comment': 'Excellent teacher! Mr. Sharma explains mathematics concepts very clearly. My grades have improved significantly.'
            },
            {
                'student_id': student_user2.id,
                'teacher_id': teacher_user2.id,
                'rating': 5,
                'comment': 'Dr. Priya is amazing! Her teaching methods for organic chemistry are outstanding. Highly recommended for NEET preparation.'
            }
        ]
        
        for review_data in reviews_data:
            review = Review(
                student_id=review_data['student_id'],
                teacher_id=review_data['teacher_id'],
                rating=review_data['rating'],
                comment=review_data['comment']
            )
            db.session.add(review)
        
        # Sample Classes
        from datetime import datetime, timedelta
        
        classes_data = [
            {
                'request_id': 1,  # Will be updated after requests are created
                'title': 'Mathematics - Quadratic Equations',
                'description': 'Detailed explanation of quadratic equations, discriminant, and solving methods',
                'scheduled_at': datetime.now() + timedelta(days=1, hours=2),
                'duration_minutes': 60,
                'status': 'scheduled'
            },
            {
                'request_id': 2,
                'title': 'Chemistry - Organic Reactions',
                'description': 'SN1, SN2 reaction mechanisms and their applications',
                'scheduled_at': datetime.now() + timedelta(days=2, hours=4),
                'duration_minutes': 90,
                'status': 'scheduled'
            }
        ]
        
        db.session.commit()
        
        # Now add classes with proper request IDs
        requests = TutorRequest.query.all()
        if len(requests) >= 2:
            for i, class_data in enumerate(classes_data):
                if i < len(requests):
                    class_obj = Class(
                        request_id=requests[i].id,
                        title=class_data['title'],
                        description=class_data['description'],
                        scheduled_at=class_data['scheduled_at'],
                        duration_minutes=class_data['duration_minutes'],
                        status=class_data['status']
                    )
                    db.session.add(class_obj)
        
        db.session.commit()
        print("✅ Comprehensive sample data created successfully!")
        print("\n📧 Demo Accounts:")
        print("👨‍🏫 Teachers:")
        print("   • rajesh@vaanyan.com / password123 (Math & Physics)")
        print("   • priya@vaanyan.com / password123 (Chemistry & Biology)")  
        print("   • anita@vaanyan.com / password123 (English & Hindi)")
        print("\n👨‍🎓 Students:")
        print("   • rahul@vaanyan.com / password123 (Class 10)")
        print("   • ananya@vaanyan.com / password123 (Class 12)")
        print("   • arjun@vaanyan.com / password123 (Class 8)")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating sample data: {e}")
        import traceback
        traceback.print_exc()

def get_user_by_email(email):
    """Get user by email"""
    return User.query.filter_by(email=email).first()

def get_user_by_id(user_id):
    """Get user by ID"""
    return User.query.get(user_id)

def search_teachers(subject=None, grade=None, limit=10):
    """Search teachers by subject and grade"""
    query = db.session.query(User, TeacherProfile).join(TeacherProfile).filter(
        User.role == UserRole.TEACHER,
        User.is_active == True
    )
    
    if subject:
        query = query.filter(TeacherProfile.subjects.contains(subject))
    
    return query.limit(limit).all()

def get_teacher_requests(teacher_id, status=None):
    """Get requests for teacher"""
    query = TutorRequest.query.filter_by(teacher_id=teacher_id)
    if status:
        query = query.filter_by(status=status)
    return query.order_by(TutorRequest.created_at.desc()).all()

def get_student_requests(student_id, status=None):
    """Get requests by student"""
    query = TutorRequest.query.filter_by(student_id=student_id)
    if status:
        query = query.filter_by(status=status)
    return query.order_by(TutorRequest.created_at.desc()).all()

def get_chat_messages(user1_id, user2_id, limit=50):
    """Get chat messages between two users"""
    return Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == user1_id, Message.recipient_id == user2_id),
            db.and_(Message.sender_id == user2_id, Message.recipient_id == user1_id)
        )
    ).order_by(Message.created_at.asc()).limit(limit).all()

def get_user_conversations(user_id):
    """Get all conversations for a user"""
    conversations = db.session.query(
        Message.sender_id,
        Message.recipient_id,
        db.func.max(Message.created_at).label('last_message_time')
    ).filter(
        db.or_(Message.sender_id == user_id, Message.recipient_id == user_id)
    ).group_by(
        db.case(
            (Message.sender_id == user_id, Message.recipient_id),
            else_=Message.sender_id
        )
    ).all()
    
    return conversations
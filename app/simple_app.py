from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()

# Define models here to avoid circular imports
class User(db.Model):
    """User model for storing user information"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(100))
    profile_photo = db.Column(db.String(255))
    availability = db.Column(db.String(50), default='Weekdays')
    is_public = db.Column(db.Boolean, default=True)
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Store skills as JSON strings
    _skills_offered = db.Column('skills_offered', db.Text, default='[]')
    _skills_wanted = db.Column('skills_wanted', db.Text, default='[]')
    
    # Relationships
    sent_requests = db.relationship('SwapRequest', foreign_keys='SwapRequest.requester_id', backref='requester', lazy='dynamic')
    received_requests = db.relationship('SwapRequest', foreign_keys='SwapRequest.receiver_id', backref='receiver', lazy='dynamic')
    
    @property
    def skills_offered(self):
        """Get skills offered as a list"""
        return json.loads(self._skills_offered) if self._skills_offered else []
    
    @skills_offered.setter
    def skills_offered(self, value):
        """Set skills offered from a list"""
        self._skills_offered = json.dumps(value) if value else '[]'
    
    @property
    def skills_wanted(self):
        """Get skills wanted as a list"""
        return json.loads(self._skills_wanted) if self._skills_wanted else []
    
    @skills_wanted.setter
    def skills_wanted(self, value):
        """Set skills wanted from a list"""
        self._skills_wanted = json.dumps(value) if value else '[]'
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the user's password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_email=False):
        """Convert user object to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'profile_photo': self.profile_photo,
            'skillsOffered': self.skills_offered,
            'skillsWanted': self.skills_wanted,
            'availability': self.availability,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_email:
            data['email'] = self.email
            
        return data
    
    def __repr__(self):
        return f'<User {self.email}>'

class Skill(db.Model):
    """Skill model for storing skill information"""
    
    __tablename__ = 'skills'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    status = db.Column(db.String(20), default='approved')  # approved, pending, rejected
    rejection_reason = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    creator = db.relationship('User', backref='created_skills')
    
    def to_dict(self):
        """Convert skill object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'status': self.status,
            'rejection_reason': self.rejection_reason,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Skill {self.name}>'

class SwapRequest(db.Model):
    """SwapRequest model for managing skill exchange requests"""
    
    __tablename__ = 'swap_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_offered = db.Column(db.String(100), nullable=False)
    skill_wanted = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text)  # Message from requester when sending request
    acceptance_message = db.Column(db.Text)  # Message from receiver when accepting/rejecting
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Add indexes for better query performance
    __table_args__ = (
        db.Index('idx_requester_status', 'requester_id', 'status'),
        db.Index('idx_receiver_status', 'receiver_id', 'status'),
    )
    
    def to_dict(self, include_users=True):
        """Convert swap request object to dictionary"""
        data = {
            'id': self.id,
            'requester_id': self.requester_id,
            'receiver_id': self.receiver_id,
            'skill_offered': self.skill_offered,
            'skill_wanted': self.skill_wanted,
            'message': self.message,
            'acceptance_message': self.acceptance_message,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_users:
            data['requester'] = self.requester.to_dict() if self.requester else None
            data['receiver'] = self.receiver.to_dict() if self.receiver else None
            
        return data
    
    def can_be_updated_by(self, user_id):
        """Check if the user can update this swap request"""
        return user_id in [self.requester_id, self.receiver_id]
    
    def __repr__(self):
        return f'<SwapRequest {self.id}: {self.skill_offered} for {self.skill_wanted}>'

def create_app():
    """Application factory pattern"""
    # Get the parent directory (project root) to correctly locate templates and static files
    import os
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    app = Flask(__name__, 
                template_folder=os.path.join(basedir, 'templates'),
                static_folder=os.path.join(basedir, 'static'))
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///skillswap.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # For development, set to expire in production
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, origins=[
        os.getenv('FRONTEND_URL', 'http://localhost:3000'),
        'http://127.0.0.1:5000',
        'http://localhost:5000'
    ])
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Import and register blueprints (after db is initialized)
    from app.routes.auth_routes import auth_bp
    from app.routes.user_routes import user_bp
    from app.routes.skill_routes import skill_bp
    from app.routes.swap_request_routes import swap_request_bp
    from app.routes.admin_routes import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(skill_bp, url_prefix='/api/skills')
    app.register_blueprint(swap_request_bp, url_prefix='/api/swap-requests')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Root route - serve HTML frontend
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # API info route
    @app.route('/api-info')
    def api_info():
        return {
            'message': 'Skill Swap Platform API',
            'status': 'running',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth/*',
                'users': '/api/users/*',
                'skills': '/api/skills/*',
                'swap_requests': '/api/swap-requests/*',
                'admin': '/api/admin/*'
            }
        }
    
    # API status endpoint
    @app.route('/api')
    def api_status():
        return {
            'message': 'Skill Swap Platform API is running',
            'version': '1.0.0',
            'database': 'connected' if db.engine else 'disconnected'
        }
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

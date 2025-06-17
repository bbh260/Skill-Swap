from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

# This will be injected by the app factory
db = None

def init_db(database):
    global db
    db = database

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

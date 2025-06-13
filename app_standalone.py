from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json
import re

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///skillswap.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
cors = CORS(app, origins=[os.getenv('FRONTEND_URL', 'http://localhost:3000')])

# Models
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(100))
    availability = db.Column(db.String(50), default='Weekdays')
    is_public = db.Column(db.Boolean, default=True)
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    _skills_offered = db.Column('skills_offered', db.Text, default='[]')
    _skills_wanted = db.Column('skills_wanted', db.Text, default='[]')
    
    @property
    def skills_offered(self):
        return json.loads(self._skills_offered) if self._skills_offered else []
    
    @skills_offered.setter
    def skills_offered(self, value):
        self._skills_offered = json.dumps(value) if value else '[]'
    
    @property
    def skills_wanted(self):
        return json.loads(self._skills_wanted) if self._skills_wanted else []
    
    @skills_wanted.setter
    def skills_wanted(self, value):
        self._skills_wanted = json.dumps(value) if value else '[]'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'skills_offered': self.skills_offered,
            'skills_wanted': self.skills_wanted,
            'availability': self.availability,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_email:
            data['email'] = self.email
        return data

class SwapRequest(db.Model):
    __tablename__ = 'swap_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_offered = db.Column(db.String(100), nullable=False)
    skill_wanted = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    requester = db.relationship('User', foreign_keys=[requester_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_requests')
    
    def to_dict(self, include_users=True):
        data = {
            'id': self.id,
            'requester_id': self.requester_id,
            'receiver_id': self.receiver_id,
            'skill_offered': self.skill_offered,
            'skill_wanted': self.skill_wanted,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_users:
            data['requester'] = self.requester.to_dict() if self.requester else None
            data['receiver'] = self.receiver.to_dict() if self.receiver else None
        return data

# Utility functions
def validate_email(email):
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_password(password):
    return len(password) >= 6

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api')
def api_status():
    return {
        'message': 'Skill Swap Platform API is running',
        'version': '1.0.0',
        'database': 'connected'
    }

# Authentication routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field.capitalize()} is required'
                }), 400
        
        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        location = data.get('location', '').strip()
        skills_offered = data.get('skillsOffered', [])
        skills_wanted = data.get('skillsWanted', [])
        availability = data.get('availability', 'Weekdays')
        
        # Validate email format
        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address'
            }), 400
        
        # Validate password strength
        if not validate_password(password):
            return jsonify({
                'success': False,
                'message': 'Password must be at least 6 characters long'
            }), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'message': 'User already exists with this email'
            }), 400
        
        # Validate skills
        if not skills_offered:
            return jsonify({
                'success': False,
                'message': 'At least one skill offered is required'
            }), 400
        
        if not skills_wanted:
            return jsonify({
                'success': False,
                'message': 'At least one skill wanted is required'
            }), 400
        
        # Create new user
        user = User(
            name=name,
            email=email,
            location=location,
            availability=availability,
            is_public=True
        )
        user.set_password(password)
        user.skills_offered = skills_offered
        user.skills_wanted = skills_wanted
        
        db.session.add(user)
        db.session.commit()
        
        # Generate access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'data': {
                'user': user.to_dict(include_email=True),
                'token': access_token
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Registration failed: {str(e)}'
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401
        
        # Check if user is banned
        if user.is_banned:
            return jsonify({
                'success': False,
                'message': f'Account is banned: {user.ban_reason}'
            }), 403
        
        # Generate access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': user.to_dict(include_email=True),
                'token': access_token
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Login failed: {str(e)}'
        }), 500

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(include_email=True)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get profile: {str(e)}'
        }), 500

@app.route('/api/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        data = request.get_json()
        
        # Update basic profile info
        if 'name' in data:
            user.name = data['name'].strip()
        if 'location' in data:
            user.location = data['location'].strip()
        if 'availability' in data:
            user.availability = data['availability']
        
        # Update skills
        if 'skillsOffered' in data:
            skills_offered = [skill.strip() for skill in data['skillsOffered'] if skill.strip()]
            if not skills_offered:
                return jsonify({
                    'success': False,
                    'message': 'At least one skill offered is required'
                }), 400
            user.skills_offered = skills_offered
        
        if 'skillsWanted' in data:
            skills_wanted = [skill.strip() for skill in data['skillsWanted'] if skill.strip()]
            if not skills_wanted:
                return jsonify({
                    'success': False,
                    'message': 'At least one skill wanted is required'
                }), 400
            user.skills_wanted = skills_wanted
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'data': {
                'user': user.to_dict(include_email=True)
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to update profile: {str(e)}'
        }), 500

@app.route('/api/auth/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        data = request.get_json()
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')
        
        if not current_password or not new_password:
            return jsonify({
                'success': False,
                'message': 'Both current and new passwords are required'
            }), 400
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({
                'success': False,
                'message': 'Current password is incorrect'
            }), 400
        
        # Validate new password
        if len(new_password) < 6:
            return jsonify({
                'success': False,
                'message': 'New password must be at least 6 characters long'
            }), 400
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to change password: {str(e)}'
        }), 500

# User routes
@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = User.query.filter_by(is_public=True, is_banned=False).all()
        return jsonify({
            'success': True,
            'data': [user.to_dict() for user in users]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get users: {str(e)}'
        }), 500

# Swap request routes
@app.route('/api/swap-requests', methods=['POST'])
@jwt_required()
def create_swap_request():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        receiver_id = data.get('receiverId')
        skill_offered = data.get('skillOffered', '').strip()
        skill_wanted = data.get('skillWanted', '').strip()
        message = data.get('message', '').strip()
        
        if not receiver_id or not skill_offered or not skill_wanted:
            return jsonify({
                'success': False,
                'message': 'Receiver ID, offered skill and wanted skill are required'
            }), 400
        
        if user_id == receiver_id:
            return jsonify({
                'success': False,
                'message': 'You cannot send a swap request to yourself'
            }), 400
        
        swap_request = SwapRequest(
            requester_id=user_id,
            receiver_id=receiver_id,
            skill_offered=skill_offered,
            skill_wanted=skill_wanted,
            message=message,
            status='pending'
        )
        
        db.session.add(swap_request)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Swap request sent successfully',
            'data': swap_request.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to create swap request: {str(e)}'
        }), 500

@app.route('/api/swap-requests/my-requests', methods=['GET'])
@jwt_required()
def get_my_requests():
    try:
        user_id = get_jwt_identity()
        requests = SwapRequest.query.filter_by(requester_id=user_id).order_by(SwapRequest.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [req.to_dict() for req in requests]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get requests: {str(e)}'
        }), 500

@app.route('/api/swap-requests/received', methods=['GET'])
@jwt_required()
def get_received_requests():
    try:
        user_id = get_jwt_identity()
        requests = SwapRequest.query.filter_by(receiver_id=user_id).order_by(SwapRequest.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [req.to_dict() for req in requests]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get received requests: {str(e)}'
        }), 500

# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

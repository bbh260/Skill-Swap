from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.utils.validators import validate_email, validate_password
from app.simple_app import db, User
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
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
        access_token = create_access_token(identity=str(user.id))
        
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

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
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
        access_token = create_access_token(identity=str(user.id))
        
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

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        user_id = int(get_jwt_identity())
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

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (client-side token removal)"""
    return jsonify({
        'success': True,
        'message': 'Logout successful'
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        print("=== PROFILE UPDATE REQUEST RECEIVED ===")
        user_id = int(get_jwt_identity())
        print(f"User ID from JWT: {user_id}")
        
        user = User.query.get(user_id)
        print(f"User found: {user is not None}")
        
        if not user:
            print("ERROR: User not found!")
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        data = request.get_json()
        print(f"Request data: {data}")
        
        # Update basic info if provided
        if 'name' in data:
            user.name = data['name'].strip()
            print(f"Updated name: {user.name}")
        if 'location' in data:
            user.location = data['location'].strip()
            print(f"Updated location: {user.location}")
        if 'availability' in data:
            user.availability = data['availability']
            print(f"Updated availability: {user.availability}")
        
        # Update skills if provided
        if 'skillsOffered' in data:
            user.skills_offered = data['skillsOffered']
            print(f"Updated skills offered: {user.skills_offered}")
        if 'skillsWanted' in data:
            user.skills_wanted = data['skillsWanted']
            print(f"Updated skills wanted: {user.skills_wanted}")
        
        print("Committing changes to database...")
        db.session.commit()
        print("Changes committed successfully!")
        
        result_data = {
            'success': True,
            'message': 'Profile updated successfully',
            'data': {
                'user': user.to_dict(include_email=True)
            }
        }
        print(f"Returning success response: {result_data}")
        return jsonify(result_data)
        
    except Exception as e:
        print(f"ERROR in update_profile: {str(e)}")
        print(f"Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to update profile: {str(e)}'
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        print("=== PASSWORD CHANGE REQUEST RECEIVED ===")
        user_id = int(get_jwt_identity())
        print(f"User ID from JWT: {user_id}")
        
        user = User.query.get(user_id)
        print(f"User found: {user is not None}")
        
        if not user:
            print("ERROR: User not found!")
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        data = request.get_json()
        print(f"Request data keys: {list(data.keys()) if data else 'None'}")
        
        # Validate required fields
        if not data.get('currentPassword') or not data.get('newPassword'):
            return jsonify({
                'success': False,
                'message': 'Current password and new password are required'
            }), 400
        
        current_password = data['currentPassword']
        new_password = data['newPassword']
        
        print("Checking current password...")
        # Verify current password
        if not user.check_password(current_password):
            print("ERROR: Current password is incorrect!")
            return jsonify({
                'success': False,
                'message': 'Current password is incorrect'
            }), 400
        
        # Validate new password
        if not validate_password(new_password):
            return jsonify({
                'success': False,
                'message': 'New password must be at least 6 characters long'
            }), 400
        
        print("Setting new password...")
        # Update password
        user.set_password(new_password)
        
        print("Committing changes to database...")
        db.session.commit()
        print("Password changed successfully!")
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        print(f"ERROR in change_password: {str(e)}")
        print(f"Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to change password: {str(e)}'
        }), 500

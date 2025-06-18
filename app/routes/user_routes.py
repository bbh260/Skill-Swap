from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.simple_app import db, User
from app.utils.validators import validate_email, sanitize_string
from sqlalchemy import or_

user_bp = Blueprint('users', __name__)

@user_bp.route('', methods=['GET'])
def get_users():
    """Get all public users with optional skill filtering"""
    try:
        skill = request.args.get('skill')
        search = request.args.get('search', '').strip()
        
        # Base query for public users who are not banned
        query = User.query.filter_by(is_public=True, is_banned=False)
        
        # Filter by skill if provided
        if skill:
            # This is a simplified search - in a real app you might want full-text search
            query = query.filter(
                or_(
                    User._skills_offered.contains(f'"{skill}"'),
                    User._skills_wanted.contains(f'"{skill}"')
                )
            )
        
        # Search by name if provided
        if search:
            query = query.filter(User.name.ilike(f'%{search}%'))
        
        users = query.all()
        
        return jsonify({
            'success': True,
            'data': [user.to_dict() for user in users]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get users: {str(e)}'
        }), 500

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """Get user by ID (public profiles only)"""
    try:
        user = User.query.filter_by(id=user_id, is_public=True, is_banned=False).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found or profile is private'
            }), 404
        
        return jsonify({
            'success': True,
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get user: {str(e)}'
        }), 500

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_my_profile():
    """Get current user's profile"""
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
            'data': user.to_dict(include_email=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get profile: {str(e)}'
        }), 500

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user's profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data and data['name'].strip():
            user.name = sanitize_string(data['name'], 100)
        
        if 'email' in data:
            email = data['email'].strip().lower()
            if email != user.email:
                if not validate_email(email):
                    return jsonify({
                        'success': False,
                        'message': 'Please enter a valid email address'
                    }), 400
                
                # Check if email is already taken
                existing_user = User.query.filter_by(email=email).first()
                if existing_user and existing_user.id != user.id:
                    return jsonify({
                        'success': False,
                        'message': 'Email is already taken'
                    }), 400
                
                user.email = email
        
        if 'location' in data:
            user.location = sanitize_string(data['location'], 100)
        
        if 'availability' in data:
            user.availability = sanitize_string(data['availability'], 50)
        
        if 'skillsOffered' in data:
            user.skills_offered = data['skillsOffered']
        
        if 'skillsWanted' in data:
            user.skills_wanted = data['skillsWanted']
        
        if 'isPublic' in data:
            user.is_public = bool(data['isPublic'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'data': user.to_dict(include_email=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to update profile: {str(e)}'
        }), 500

@user_bp.route('/skills', methods=['GET'])
def get_all_skills():
    """Get all unique skills from all users"""
    try:
        users = User.query.filter_by(is_public=True, is_banned=False).all()
        
        skills_set = set()
        for user in users:
            skills_set.update(user.skills_offered)
            skills_set.update(user.skills_wanted)
        
        skills_list = sorted(list(skills_set))
        
        return jsonify({
            'success': True,
            'data': skills_list
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get skills: {str(e)}'
        }), 500

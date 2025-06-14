from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.simple_app import db, Skill, User
from app.utils.validators import sanitize_string

skill_bp = Blueprint('skills', __name__)

@skill_bp.route('', methods=['GET'])
def get_skills():
    """Get all approved skills"""
    try:
        category = request.args.get('category')
        search = request.args.get('search', '').strip()
        
        query = Skill.query.filter_by(status='approved')
        
        if category:
            query = query.filter_by(category=category)
        
        if search:
            query = query.filter(Skill.name.ilike(f'%{search}%'))
        
        skills = query.order_by(Skill.name).all()
        
        return jsonify({
            'success': True,
            'data': [skill.to_dict() for skill in skills]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get skills: {str(e)}'
        }), 500

@skill_bp.route('', methods=['POST'])
@jwt_required()
def create_skill():
    """Create a new skill"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', '').strip()
        
        if not name:
            return jsonify({
                'success': False,
                'message': 'Skill name is required'
            }), 400
        
        # Check if skill already exists
        existing_skill = Skill.query.filter_by(name=name).first()
        if existing_skill:
            return jsonify({
                'success': False,
                'message': 'Skill already exists'
            }), 400
        
        skill = Skill(
            name=sanitize_string(name, 100),
            description=sanitize_string(description, 500),
            category=sanitize_string(category, 50),
            created_by=user_id,
            status='pending'  # New skills need approval
        )
        
        db.session.add(skill)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Skill created successfully and is pending approval',
            'data': skill.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to create skill: {str(e)}'
        }), 500

@skill_bp.route('/<int:skill_id>', methods=['GET'])
def get_skill_by_id(skill_id):
    """Get skill by ID"""
    try:
        skill = Skill.query.filter_by(id=skill_id, status='approved').first()
        
        if not skill:
            return jsonify({
                'success': False,
                'message': 'Skill not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': skill.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get skill: {str(e)}'
        }), 500

@skill_bp.route('/<int:skill_id>', methods=['PUT'])
@jwt_required()
def update_skill(skill_id):
    """Update skill (only by creator or admin)"""
    try:
        user_id = get_jwt_identity()
        skill = Skill.query.get(skill_id)
        
        if not skill:
            return jsonify({
                'success': False,
                'message': 'Skill not found'
            }), 404
        
        # Check if user is the creator (admin check would go here too)
        if skill.created_by != user_id:
            return jsonify({
                'success': False,
                'message': 'You can only update skills you created'
            }), 403
        
        data = request.get_json()
        
        if 'name' in data and data['name'].strip():
            skill.name = sanitize_string(data['name'], 100)
        
        if 'description' in data:
            skill.description = sanitize_string(data['description'], 500)
        
        if 'category' in data:
            skill.category = sanitize_string(data['category'], 50)
        
        # Reset status to pending when updated
        skill.status = 'pending'
        skill.rejection_reason = None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Skill updated successfully and is pending approval',
            'data': skill.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to update skill: {str(e)}'
        }), 500

@skill_bp.route('/<int:skill_id>', methods=['DELETE'])
@jwt_required()
def delete_skill(skill_id):
    """Delete skill (only by creator or admin)"""
    try:
        user_id = get_jwt_identity()
        skill = Skill.query.get(skill_id)
        
        if not skill:
            return jsonify({
                'success': False,
                'message': 'Skill not found'
            }), 404
        
        # Check if user is the creator (admin check would go here too)
        if skill.created_by != user_id:
            return jsonify({
                'success': False,
                'message': 'You can only delete skills you created'
            }), 403
        
        db.session.delete(skill)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Skill deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete skill: {str(e)}'
        }), 500

@skill_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all skill categories"""
    try:
        categories = db.session.query(Skill.category).filter(
            Skill.status == 'approved',
            Skill.category.isnot(None),
            Skill.category != ''
        ).distinct().all()
        
        category_list = sorted([cat[0] for cat in categories if cat[0]])
        
        return jsonify({
            'success': True,
            'data': category_list
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get categories: {str(e)}'
        }), 500

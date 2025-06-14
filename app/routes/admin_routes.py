from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.simple_app import db, User, Skill, SwapRequest
from app.utils.validators import sanitize_string
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

# Note: In a real application, you would have proper admin role checking
# For this demo, we'll implement basic admin functionality

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_platform_stats():
    """Get platform statistics"""
    try:
        # In a real app, you'd check if user is admin
        
        # Get user statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_banned=False).count()
        banned_users = User.query.filter_by(is_banned=True).count()
        
        # Get skill statistics
        total_skills = Skill.query.count()
        approved_skills = Skill.query.filter_by(status='approved').count()
        pending_skills = Skill.query.filter_by(status='pending').count()
        rejected_skills = Skill.query.filter_by(status='rejected').count()
        
        # Get swap request statistics
        total_requests = SwapRequest.query.count()
        pending_requests = SwapRequest.query.filter_by(status='pending').count()
        accepted_requests = SwapRequest.query.filter_by(status='accepted').count()
        rejected_requests = SwapRequest.query.filter_by(status='rejected').count()
        cancelled_requests = SwapRequest.query.filter_by(status='cancelled').count()
        
        return jsonify({
            'success': True,
            'data': {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'banned': banned_users
                },
                'skills': {
                    'total': total_skills,
                    'approved': approved_skills,
                    'pending': pending_skills,
                    'rejected': rejected_skills
                },
                'swap_requests': {
                    'total': total_requests,
                    'pending': pending_requests,
                    'accepted': accepted_requests,
                    'rejected': rejected_requests,
                    'cancelled': cancelled_requests
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get stats: {str(e)}'
        }), 500

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """Get all users (admin only)"""
    try:
        # In a real app, you'd check if user is admin
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        
        query = User.query
        
        if search:
            query = query.filter(
                User.name.ilike(f'%{search}%') | 
                User.email.ilike(f'%{search}%')
            )
        
        paginated_users = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'users': [user.to_dict(include_email=True) for user in paginated_users.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': paginated_users.total,
                    'pages': paginated_users.pages
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get users: {str(e)}'
        }), 500

@admin_bp.route('/users/<int:user_id>/ban', methods=['POST'])
@jwt_required()
def ban_user(user_id):
    """Ban a user"""
    try:
        # In a real app, you'd check if user is admin
        
        data = request.get_json()
        reason = data.get('reason', '').strip()
        
        if not reason:
            return jsonify({
                'success': False,
                'message': 'Ban reason is required'
            }), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        user.is_banned = True
        user.ban_reason = sanitize_string(reason, 500)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User banned successfully',
            'data': user.to_dict(include_email=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to ban user: {str(e)}'
        }), 500

@admin_bp.route('/users/<int:user_id>/unban', methods=['POST'])
@jwt_required()
def unban_user(user_id):
    """Unban a user"""
    try:
        # In a real app, you'd check if user is admin
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        user.is_banned = False
        user.ban_reason = None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User unbanned successfully',
            'data': user.to_dict(include_email=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to unban user: {str(e)}'
        }), 500

@admin_bp.route('/skills/pending', methods=['GET'])
@jwt_required()
def get_pending_skills():
    """Get all pending skills for approval"""
    try:
        # In a real app, you'd check if user is admin
        
        skills = Skill.query.filter_by(status='pending').order_by(Skill.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [skill.to_dict() for skill in skills]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get pending skills: {str(e)}'
        }), 500

@admin_bp.route('/skills/<int:skill_id>/approve', methods=['POST'])
@jwt_required()
def approve_skill(skill_id):
    """Approve a skill"""
    try:
        # In a real app, you'd check if user is admin
        
        skill = Skill.query.get(skill_id)
        if not skill:
            return jsonify({
                'success': False,
                'message': 'Skill not found'
            }), 404
        
        skill.status = 'approved'
        skill.rejection_reason = None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Skill approved successfully',
            'data': skill.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to approve skill: {str(e)}'
        }), 500

@admin_bp.route('/skills/<int:skill_id>/reject', methods=['POST'])
@jwt_required()
def reject_skill(skill_id):
    """Reject a skill"""
    try:
        # In a real app, you'd check if user is admin
        
        data = request.get_json()
        reason = data.get('reason', '').strip()
        
        if not reason:
            return jsonify({
                'success': False,
                'message': 'Rejection reason is required'
            }), 400
        
        skill = Skill.query.get(skill_id)
        if not skill:
            return jsonify({
                'success': False,
                'message': 'Skill not found'
            }), 404
        
        skill.status = 'rejected'
        skill.rejection_reason = sanitize_string(reason, 500)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Skill rejected successfully',
            'data': skill.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to reject skill: {str(e)}'
        }), 500

@admin_bp.route('/requests', methods=['GET'])
@jwt_required()
def get_all_requests():
    """Get all swap requests (admin only)"""
    try:
        # In a real app, you'd check if user is admin
        
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = SwapRequest.query
        
        if status:
            query = query.filter_by(status=status)
        
        paginated_requests = query.order_by(SwapRequest.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'requests': [req.to_dict() for req in paginated_requests.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': paginated_requests.total,
                    'pages': paginated_requests.pages
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get requests: {str(e)}'
        }), 500

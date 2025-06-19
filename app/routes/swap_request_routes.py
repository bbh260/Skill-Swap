from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.simple_app import db, SwapRequest, User
from app.utils.validators import sanitize_string

swap_request_bp = Blueprint('swap_requests', __name__)

@swap_request_bp.route('', methods=['POST'])
@jwt_required()
def create_swap_request():
    """Create a new swap request"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        receiver_id = data.get('receiverId')
        skill_offered = data.get('skillOffered', '').strip()
        skill_wanted = data.get('skillWanted', '').strip()
        message = data.get('message', '').strip()
        
        # Validate required fields
        if not receiver_id:
            return jsonify({
                'success': False,
                'message': 'Receiver ID is required'
            }), 400
        
        if not skill_offered or not skill_wanted:
            return jsonify({
                'success': False,
                'message': 'Both offered and wanted skills are required'
            }), 400
        
        # Check if receiver exists and is not banned
        receiver = User.query.filter_by(id=receiver_id, is_banned=False).first()
        if not receiver:
            return jsonify({
                'success': False,
                'message': 'Receiver not found or unavailable'
            }), 404
        
        # Prevent sending request to yourself
        if user_id == receiver_id:
            return jsonify({
                'success': False,
                'message': 'You cannot send a swap request to yourself'
            }), 400
        
        # Check if there's already a pending request between these users for the same skills
        existing_request = SwapRequest.query.filter_by(
            requester_id=user_id,
            receiver_id=receiver_id,
            skill_offered=skill_offered,
            skill_wanted=skill_wanted,
            status='pending'
        ).first()
        
        if existing_request:
            return jsonify({
                'success': False,
                'message': 'You already have a pending request for these skills with this user'
            }), 400
        
        swap_request = SwapRequest(
            requester_id=user_id,
            receiver_id=receiver_id,
            skill_offered=sanitize_string(skill_offered, 100),
            skill_wanted=sanitize_string(skill_wanted, 100),
            message=sanitize_string(message, 500),
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

@swap_request_bp.route('/my-requests', methods=['GET'])
@jwt_required()
def get_my_requests():
    """Get all requests sent by current user"""
    try:
        user_id = int(get_jwt_identity())
        status = request.args.get('status')
        
        query = SwapRequest.query.filter_by(requester_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        requests = query.order_by(SwapRequest.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [req.to_dict() for req in requests]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get requests: {str(e)}'
        }), 500

@swap_request_bp.route('/received', methods=['GET'])
@jwt_required()
def get_received_requests():
    """Get all requests received by current user"""
    try:
        user_id = int(get_jwt_identity())
        status = request.args.get('status')
        
        query = SwapRequest.query.filter_by(receiver_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        requests = query.order_by(SwapRequest.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [req.to_dict() for req in requests]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get received requests: {str(e)}'
        }), 500

@swap_request_bp.route('/<int:request_id>', methods=['GET'])
@jwt_required()
def get_swap_request(request_id):
    """Get specific swap request"""
    try:
        user_id = int(get_jwt_identity())
        swap_request = SwapRequest.query.get(request_id)
        
        if not swap_request:
            return jsonify({
                'success': False,
                'message': 'Swap request not found'
            }), 404
        
        # Check if user is involved in this request
        if user_id not in [swap_request.requester_id, swap_request.receiver_id]:
            return jsonify({
                'success': False,
                'message': 'You are not authorized to view this request'
            }), 403
        
        return jsonify({
            'success': True,
            'data': swap_request.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get swap request: {str(e)}'
        }), 500

@swap_request_bp.route('/<int:request_id>', methods=['PUT'])
@jwt_required()
def update_swap_request(request_id):
    """Update swap request status"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        swap_request = SwapRequest.query.get(request_id)
        
        if not swap_request:
            return jsonify({
                'success': False,
                'message': 'Swap request not found'
            }), 404
        
        # Check if user can update this request
        if not swap_request.can_be_updated_by(user_id):
            return jsonify({
                'success': False,
                'message': 'You are not authorized to update this request'
            }), 403
        
        new_status = data.get('status')
        acceptance_message = data.get('acceptanceMessage', '').strip()
        valid_statuses = ['accepted', 'rejected', 'cancelled']
        
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        # Only the receiver can accept/reject, only the requester can cancel
        if new_status in ['accepted', 'rejected'] and user_id != swap_request.receiver_id:
            return jsonify({
                'success': False,
                'message': 'Only the receiver can accept or reject requests'
            }), 403
        
        if new_status == 'cancelled' and user_id != swap_request.requester_id:
            return jsonify({
                'success': False,
                'message': 'Only the requester can cancel requests'
            }), 403
        
        # Check if request is still pending
        if swap_request.status != 'pending':
            return jsonify({
                'success': False,
                'message': f'Cannot update request with status: {swap_request.status}'
            }), 400
        
        swap_request.status = new_status
        
        # Add acceptance message if provided and action is accept/reject
        if new_status in ['accepted', 'rejected'] and acceptance_message:
            from app.utils.validators import sanitize_string
            swap_request.acceptance_message = sanitize_string(acceptance_message, 500)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Request {new_status} successfully',
            'data': swap_request.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to update swap request: {str(e)}'
        }), 500

@swap_request_bp.route('/<int:request_id>', methods=['DELETE'])
@jwt_required()
def delete_swap_request(request_id):
    """Delete swap request (only by requester)"""
    try:
        user_id = int(get_jwt_identity())
        swap_request = SwapRequest.query.get(request_id)
        
        if not swap_request:
            return jsonify({
                'success': False,
                'message': 'Swap request not found'
            }), 404
        
        # Only the requester can delete the request
        if user_id != swap_request.requester_id:
            return jsonify({
                'success': False,
                'message': 'Only the requester can delete the request'
            }), 403
        
        db.session.delete(swap_request)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Swap request deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete swap request: {str(e)}'
        }), 500

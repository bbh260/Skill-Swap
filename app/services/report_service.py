from app.models.user import User
from app.models.swap_request import SwapRequest
from app import db
from sqlalchemy import func

class ReportService:
    """Service for generating reports and analytics"""
    
    @staticmethod
    def get_user_activity_report():
        """Generate user activity report"""
        try:
            # Get user statistics
            total_users = User.query.count()
            active_users = User.query.filter_by(is_banned=False).count()
            banned_users = User.query.filter_by(is_banned=True).count()
            
            # Get users with most skills offered
            top_skill_providers = db.session.query(
                User.name,
                func.json_array_length(User._skills_offered).label('skills_count')
            ).filter(
                User.is_banned == False,
                User.is_public == True
            ).order_by(
                func.json_array_length(User._skills_offered).desc()
            ).limit(10).all()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'banned_users': banned_users,
                'top_skill_providers': [
                    {'name': user.name, 'skills_count': user.skills_count}
                    for user in top_skill_providers
                ]
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_swap_requests_report():
        """Generate swap requests report"""
        try:
            # Get request statistics by status
            request_stats = db.session.query(
                SwapRequest.status,
                func.count(SwapRequest.id).label('count')
            ).group_by(SwapRequest.status).all()
            
            # Get most popular skills
            offered_skills = db.session.query(
                SwapRequest.skill_offered,
                func.count(SwapRequest.id).label('count')
            ).group_by(SwapRequest.skill_offered).order_by(
                func.count(SwapRequest.id).desc()
            ).limit(10).all()
            
            wanted_skills = db.session.query(
                SwapRequest.skill_wanted,
                func.count(SwapRequest.id).label('count')
            ).group_by(SwapRequest.skill_wanted).order_by(
                func.count(SwapRequest.id).desc()
            ).limit(10).all()
            
            return {
                'request_stats': {
                    status.status: status.count for status in request_stats
                },
                'most_offered_skills': [
                    {'skill': skill.skill_offered, 'count': skill.count}
                    for skill in offered_skills
                ],
                'most_wanted_skills': [
                    {'skill': skill.skill_wanted, 'count': skill.count}
                    for skill in wanted_skills
                ]
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_platform_health_report():
        """Generate platform health report"""
        try:
            # Get recent activity (last 30 days would require date filtering)
            recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
            recent_requests = SwapRequest.query.order_by(SwapRequest.created_at.desc()).limit(10).all()
            
            # Calculate success rate (accepted / total non-pending requests)
            total_processed = SwapRequest.query.filter(
                SwapRequest.status.in_(['accepted', 'rejected', 'cancelled'])
            ).count()
            
            accepted_requests = SwapRequest.query.filter_by(status='accepted').count()
            success_rate = (accepted_requests / total_processed * 100) if total_processed > 0 else 0
            
            return {
                'recent_users_count': len(recent_users),
                'recent_requests_count': len(recent_requests),
                'success_rate': round(success_rate, 2),
                'total_processed_requests': total_processed,
                'accepted_requests': accepted_requests
            }
        except Exception as e:
            return {'error': str(e)}

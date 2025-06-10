from app import db
from datetime import datetime

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

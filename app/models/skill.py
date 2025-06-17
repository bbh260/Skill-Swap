from datetime import datetime

# This will be set by the app factory
db = None

class Skill:
    """Skill model for storing skill information"""
    pass

def init_skill_model(database):
    """Initialize the Skill model with the database instance"""
    global db
    db = database
    
    class SkillModel(db.Model):
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
    
    # Replace the Skill class with the actual model
    globals()['Skill'] = SkillModel
    return SkillModel

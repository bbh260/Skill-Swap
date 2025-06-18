from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///skillswap.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # For development, set to expire in production
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, origins=[os.getenv('FRONTEND_URL', 'http://localhost:3000')])
    
    # Import and create models
    from app.models.base import create_models
    User, Skill, SwapRequest = create_models(db)
    
    # Make models available globally
    globals()['User'] = User
    globals()['Skill'] = Skill
    globals()['SwapRequest'] = SwapRequest
    
    # Import and register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.user_routes import user_bp
    from app.routes.skill_routes import skill_bp
    from app.routes.swap_request_routes import swap_request_bp
    from app.routes.admin_routes import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(skill_bp, url_prefix='/api/skills')
    app.register_blueprint(swap_request_bp, url_prefix='/api/swap-requests')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Root route - serve HTML frontend
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # API info route
    @app.route('/api-info')
    def api_info():
        return {
            'message': 'Skill Swap Platform API',
            'status': 'running',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth/*',
                'users': '/api/users/*',
                'skills': '/api/skills/*',
                'swap_requests': '/api/swap-requests/*',
                'admin': '/api/admin/*'
            }
        }
    
    # API status endpoint
    @app.route('/api')
    def api_status():
        return {
            'message': 'Skill Swap Platform API is running',
            'version': '1.0.0',
            'database': 'connected' if db.engine else 'disconnected'
        }
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

# Import models
from src.models.user_enhanced import db, User, UserProfile, CVData, Internship, Application, ApplicationTracking, ChatSession, ChatMessage

# Import routes
from src.routes.auth_enhanced_github import auth_github_bp
from src.routes.ai_chatbot import ai_chatbot_bp
from src.routes.autofill import autofill_bp
from src.routes.job_search import job_search_bp
from src.routes.cv_parser import cv_parser_bp
from src.routes.i18n_routes import i18n_bp

# Import utilities
from src.utils.i18n import i18n

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///autointern_enhanced.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')
    
    # OAuth Configuration
    app.config['GITHUB_CLIENT_ID'] = os.environ.get('GITHUB_CLIENT_ID')
    app.config['GITHUB_CLIENT_SECRET'] = os.environ.get('GITHUB_CLIENT_SECRET')
    app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # OpenAI Configuration
    app.config['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY')
    
    # Enable CORS for all routes
    CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])
    
    # Initialize database
    db.init_app(app)
    
    # Initialize i18n
    i18n.init_app(app)
    
    # Create upload directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'cvs'), exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(auth_github_bp, url_prefix='/api/auth')
    app.register_blueprint(ai_chatbot_bp, url_prefix='/api/ai')
    app.register_blueprint(autofill_bp, url_prefix='/api/autofill')
    app.register_blueprint(job_search_bp, url_prefix='/api/jobs')
    app.register_blueprint(cv_parser_bp, url_prefix='/api/cv')
    app.register_blueprint(i18n_bp, url_prefix='/api/i18n')
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '2.0.0-enhanced',
            'features': [
                'github_oauth',
                'ai_chatbot',
                'autofill',
                'job_search',
                'application_tracker',
                'cv_parser',
                'multilingual_support'
            ]
        }), 200
    
    # API info endpoint
    @app.route('/api/info', methods=['GET'])
    def api_info():
        return jsonify({
            'name': 'Auto Intern Enhanced API',
            'version': '2.0.0',
            'description': 'Enhanced Auto Intern platform with AI, autofill, and multilingual support',
            'endpoints': {
                'authentication': '/api/auth',
                'ai_chatbot': '/api/ai',
                'autofill': '/api/autofill',
                'job_search': '/api/jobs',
                'cv_parser': '/api/cv',
                'internationalization': '/api/i18n'
            },
            'supported_languages': ['en', 'ar'],
            'features': {
                'github_oauth': 'GitHub OAuth authentication',
                'google_oauth': 'Google OAuth authentication',
                'ai_chatbot': 'AI-powered chatbot for job assistance',
                'autofill': 'Automatic form filling for job applications',
                'job_search': 'Intelligent job search and recommendations',
                'auto_apply': 'Automatic job application submission',
                'application_tracker': 'Track application status and progress',
                'cv_parser': 'CV parsing and analysis with AI',
                'cover_letter_ai': 'AI-generated cover letters',
                'multilingual': 'Arabic and English language support'
            }
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden'}), 403
    
    # Create database tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")
    
    return app

# Create the application
app = create_app()

if __name__ == '__main__':
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"Starting Auto Intern Enhanced API on port {port}")
    print(f"Debug mode: {debug}")
    print("Available endpoints:")
    print("  - /api/health - Health check")
    print("  - /api/info - API information")
    print("  - /api/auth/* - Authentication endpoints")
    print("  - /api/ai/* - AI chatbot endpoints")
    print("  - /api/autofill/* - Autofill endpoints")
    print("  - /api/jobs/* - Job search endpoints")
    print("  - /api/cv/* - CV parser endpoints")
    print("  - /api/i18n/* - Internationalization endpoints")
    
    app.run(host='0.0.0.0', port=port, debug=debug)


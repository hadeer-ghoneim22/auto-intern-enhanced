import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# DON\'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.internships import internships_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Load configuration from environment variables
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')
app.config['SUPABASE_URL'] = os.getenv('SUPABASE_URL')
app.config['SUPABASE_ANON_KEY'] = os.getenv('SUPABASE_ANON_KEY')
app.config['SUPABASE_SERVICE_ROLE_KEY'] = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')

# للحصول على عنوان URL للواجهة الأمامية من متغيرات البيئة
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://auto-intern-ai.vercel.app') # استخدم الرابط الجديد

# للسماح بالطلبات من الواجهة الأمامية قم بتكوين CORS
CORS(app, resources={
    r"/*": {
        "origins": ["https://auto-intern-ai-5poo.vercel.app/", "http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
} )


# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(internships_bp, url_prefix='/api')

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables and add sample data
with app.app_context():
    db.create_all()
    
    # Add sample internships if none exist
    from src.models.user import Internship
    if Internship.query.count() == 0:
        sample_internships = [
            Internship(
                title="Software Engineering Intern",
                company="Google",
                location="Mountain View, CA",
                description="Join our team to work on cutting-edge technology and build products used by billions of people worldwide.",
                url="https://careers.google.com/jobs/results/123456789/"
             ),
            Internship(
                title="Data Science Intern",
                company="Microsoft",
                location="Seattle, WA",
                description="Work with our data science team to analyze large datasets and build machine learning models.",
                url="https://careers.microsoft.com/us/en/job/123456"
             ),
            Internship(
                title="Product Management Intern",
                company="Apple",
                location="Cupertino, CA",
                description="Help shape the future of Apple products by working closely with engineering and design teams.",
                url="https://jobs.apple.com/en-us/details/123456789"
             ),
            Internship(
                title="Frontend Developer Intern",
                company="Meta",
                location="Menlo Park, CA",
                description="Build user interfaces for Facebook, Instagram, and other Meta products using React and modern web technologies.",
                url="https://www.metacareers.com/jobs/123456789/"
             ),
            Internship(
                title="Machine Learning Intern",
                company="OpenAI",
                location="San Francisco, CA",
                description="Research and develop advanced AI systems that benefit humanity.",
                url="https://openai.com/careers/123456"
             )
        ]
        
        for internship in sample_internships:
            db.session.add(internship)
        
        db.session.commit()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

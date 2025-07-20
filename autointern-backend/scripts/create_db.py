#!/usr/bin/env python3
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

from src.models.user import db, User, Internship, Application
from flask import Flask

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

with app.app_context():
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()
    
    # Add sample internships
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
    print("Database created successfully with sample data!")

#!/usr/bin/env python3
"""
Database setup and migration script for AutoIntern.AI
This script creates the database schema and populates it with sample data.
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def create_database_schema():
    """Create database tables and relationships"""
    
    # Database schema creation SQL
    schema_sql = """
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255),
        google_id VARCHAR(255),
        name VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Internships table
    CREATE TABLE IF NOT EXISTS internships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(255) NOT NULL,
        company VARCHAR(255) NOT NULL,
        location VARCHAR(255),
        description TEXT,
        url VARCHAR(500),
        requirements TEXT,
        salary_range VARCHAR(100),
        duration VARCHAR(100),
        application_deadline DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Applications table
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        internship_id INTEGER NOT NULL,
        status VARCHAR(50) DEFAULT 'submitted',
        applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cover_letter TEXT,
        resume_url VARCHAR(500),
        notes TEXT,
        interview_date TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (internship_id) REFERENCES internships (id) ON DELETE CASCADE
    );

    -- User profiles table
    CREATE TABLE IF NOT EXISTS user_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        phone VARCHAR(20),
        linkedin_url VARCHAR(500),
        github_url VARCHAR(500),
        portfolio_url VARCHAR(500),
        skills TEXT,
        education TEXT,
        experience TEXT,
        bio TEXT,
        avatar_url VARCHAR(500),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );

    -- Application tracking table
    CREATE TABLE IF NOT EXISTS application_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER NOT NULL,
        status VARCHAR(50) NOT NULL,
        notes TEXT,
        changed_by INTEGER,
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES applications (id) ON DELETE CASCADE,
        FOREIGN KEY (changed_by) REFERENCES users (id)
    );

    -- Indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
    CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
    CREATE INDEX IF NOT EXISTS idx_applications_internship_id ON applications(internship_id);
    CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
    CREATE INDEX IF NOT EXISTS idx_internships_company ON internships(company);
    CREATE INDEX IF NOT EXISTS idx_internships_location ON internships(location);
    """
    
    return schema_sql

def insert_sample_data():
    """Insert sample internships and test data"""
    
    sample_data_sql = """
    -- Insert sample internships
    INSERT OR IGNORE INTO internships (title, company, location, description, url, requirements, salary_range, duration, application_deadline) VALUES
    ('Software Engineering Intern', 'Google', 'Mountain View, CA', 
     'Join our team to work on cutting-edge technology and build products used by billions of people worldwide. You will collaborate with experienced engineers on real-world projects.',
     'https://careers.google.com/jobs/results/123456789/',
     'Computer Science or related field, Programming experience in Python/Java/C++, Strong problem-solving skills',
     '$8,000 - $10,000/month', '12 weeks', '2024-03-15'),
    
    ('Data Science Intern', 'Microsoft', 'Seattle, WA',
     'Work with our data science team to analyze large datasets and build machine learning models that power Microsoft products.',
     'https://careers.microsoft.com/us/en/job/123456',
     'Statistics or Data Science background, Python/R programming, Machine Learning knowledge',
     '$7,500 - $9,500/month', '10-12 weeks', '2024-03-20'),
    
    ('Product Management Intern', 'Apple', 'Cupertino, CA',
     'Help shape the future of Apple products by working closely with engineering and design teams to deliver exceptional user experiences.',
     'https://jobs.apple.com/en-us/details/123456789',
     'Business or Engineering background, Strong analytical skills, User experience focus',
     '$8,500 - $11,000/month', '12 weeks', '2024-03-10'),
    
    ('Frontend Developer Intern', 'Meta', 'Menlo Park, CA',
     'Build user interfaces for Facebook, Instagram, and other Meta products using React and modern web technologies.',
     'https://www.metacareers.com/jobs/123456789/',
     'Web development experience, React/JavaScript proficiency, UI/UX design understanding',
     '$8,000 - $10,500/month', '12-16 weeks', '2024-03-25'),
    
    ('Machine Learning Intern', 'OpenAI', 'San Francisco, CA',
     'Research and develop advanced AI systems that benefit humanity. Work on cutting-edge projects in natural language processing and computer vision.',
     'https://openai.com/careers/123456',
     'Machine Learning background, Python/PyTorch experience, Research experience preferred',
     '$9,000 - $12,000/month', '12 weeks', '2024-04-01'),
    
    ('UX Design Intern', 'Airbnb', 'San Francisco, CA',
     'Design intuitive and delightful user experiences for millions of travelers worldwide. Collaborate with product and engineering teams.',
     'https://careers.airbnb.com/positions/123456',
     'Design portfolio, Figma/Sketch proficiency, User research experience',
     '$7,000 - $9,000/month', '12 weeks', '2024-03-30'),
    
    ('DevOps Intern', 'Netflix', 'Los Gatos, CA',
     'Help build and maintain the infrastructure that delivers entertainment to millions of users globally.',
     'https://jobs.netflix.com/jobs/123456',
     'Cloud platforms experience, Docker/Kubernetes knowledge, Scripting skills',
     '$8,500 - $10,000/month', '12 weeks', '2024-04-05'),
    
    ('Cybersecurity Intern', 'Palantir', 'Palo Alto, CA',
     'Work on security solutions that protect critical infrastructure and help solve important problems.',
     'https://www.palantir.com/careers/123456',
     'Cybersecurity knowledge, Network security understanding, Programming skills',
     '$9,500 - $11,500/month', '10-12 weeks', '2024-03-18');
    """
    
    return sample_data_sql

def main():
    """Main function to set up the database"""
    
    print("🚀 Setting up AutoIntern.AI Database...")
    print("=" * 50)
    
    # Create database directory if it doesn't exist
    db_dir = os.path.join(project_root, 'src', 'database')
    os.makedirs(db_dir, exist_ok=True)
    
    # Database file path
    db_path = os.path.join(db_dir, 'app.db')
    
    try:
        import sqlite3
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📊 Creating database schema...")
        
        # Execute schema creation
        schema_sql = create_database_schema()
        cursor.executescript(schema_sql)
        
        print("✅ Database schema created successfully!")
        
        print("📝 Inserting sample data...")
        
        # Insert sample data
        sample_data_sql = insert_sample_data()
        cursor.executescript(sample_data_sql)
        
        print("✅ Sample data inserted successfully!")
        
        # Commit changes
        conn.commit()
        
        # Verify data
        cursor.execute("SELECT COUNT(*) FROM internships")
        internship_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        print(f"📈 Database Statistics:")
        print(f"   • Internships: {internship_count}")
        print(f"   • Users: {user_count}")
        print(f"   • Database location: {db_path}")
        
        conn.close()
        
        print("\n🎉 Database setup completed successfully!")
        print("You can now run your Flask application.")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
